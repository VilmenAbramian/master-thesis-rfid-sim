import numpy as np

from pysim.objects import Transaction, Model, Tag
import pysim.epcstd as std


def start_simulation(kernel):
    assert isinstance(kernel.context, Model)
    ctx = kernel.context
    ctx.reader.kernel = kernel
    for generator in ctx.generators:
        kernel.schedule(generator.interval, generate_tag, generator)   # FIXME: uncomment!
        # kernel.schedule(0.001, generate_tag, generator)
    kernel.schedule(ctx.update_interval, update_positions)
    kernel.call(turn_reader_on, ctx.reader)


def _update_power(time, reader, tags, transaction, medium, statistics):
    for tag in tags:
        power = medium.estimate_tag_rx_power(reader, tag, time)
        tag.set_power(time, power)
        tag.pos += tag.velocity * tag.normalized_direction * (
            time - tag.last_pos_update)
        tag.last_pos_update = time
        # TODO: uncomment lines below for PL debug
        # print(f"Estimated tag RX power: {power}")
        # print(f"- tag:    pos={tag.antenna.pos}, direction={tag.antenna.direction_theta}")
        # print(f"- reader: pos={reader.antenna.pos}, direction={reader.antenna.direction_theta}")

    if transaction is not None:
        for tag in transaction.tags:
            power = medium.estimate_reader_rx_power(reader, tag, time)
            transaction.reader_rx_power_map.update(tag, power)

    # Writing statistics
    if statistics is not None and statistics.use_power_statistics:
        for tag in tags:
            statistics.get_tag_record(tag).write_power_record(
                time, reader, medium)


def _build_transaction(kernel, reader, reader_frame):
    ctx = kernel.context
    all_responses = ((tag, tag.receive(reader_frame)) for tag in ctx.tags)
    tag_frames = [(tag, frame) for (tag, frame) in all_responses
                  if frame is not None]

    if ctx.tags:
        if isinstance(reader_frame.command, std.Query):
            stat = kernel.context.statistics
            participating_tags = [tag for tag in ctx.tags if tag.state in
                                  {Tag.State.ARBITRATE, Tag.State.REPLY}]
            for tag in participating_tags:
                stat.get_tag_record(tag).num_rounds_attained += 1
                # print("incrementing num_rounds for tag = {}".format(tag.tag_id))

    now = kernel.time
    return Transaction(ctx.medium, reader, reader_frame, tag_frames, now)


def turn_reader_on(kernel, reader):
    ctx = kernel.context

    # Turning ON and getting the first command
    cmd_frame = reader.turn_on()

    # Managing antennas
    if reader.num_antennas > 1:
        reader.antenna_switch_event_id = kernel.schedule(
            reader.antenna_switch_interval, switch_reader_antenna, reader)
    kernel.logger.debug("switched antenna #{}".format(reader.antenna_index))

    # Updating tags and transaction power
    assert ctx.transaction is None
    _update_power(kernel.time, reader, ctx.tags, None, ctx.medium,
                  ctx.statistics)

    # Processing new command (reader frame)
    transaction = _build_transaction(kernel, reader, cmd_frame)
    ctx.transaction = transaction
    ctx.transaction.timeout_event_id = kernel.schedule(
        transaction.duration, finish_transaction, transaction)
    if transaction.reply_start_time is not None:
        dt = transaction.reply_start_time - kernel.time
        kernel.schedule(dt, update_power_at_response_start, transaction)

    # Scheduling turning off
    power_mode = reader.power_control_mode
    turned_on_duration = power_mode.min_powered_on_interval(reader)
    kernel.schedule(turned_on_duration, turn_reader_off, reader)


def turn_reader_off(kernel, reader):
    ctx = kernel.context
    reader.turn_off()
    _update_power(kernel.time, reader, ctx.tags, None, ctx.medium,
                  ctx.statistics)

    # Clearing current transaction
    if ctx.transaction is not None:
        kernel.cancel(ctx.transaction.response_start_event_id)
        kernel.cancel(ctx.transaction.timeout_event_id)
        ctx.transaction = None

    # Clearing antenna switch event
    kernel.cancel(reader.antenna_switch_event_id)

    # Scheduling turning ON
    power_mode = reader.power_control_mode
    turned_off_duration = power_mode.powered_off_interval(reader)
    kernel.schedule(turned_off_duration, turn_reader_on, reader)


def generate_tag(kernel, generator):
    assert isinstance(kernel.context, Model)

    if 0 <= generator.max_tags_generated <= generator.num_tags_generated:
        return

    # Creating a tag and adding it to the model
    ctx = kernel.context
    tag = generator.create_tag(kernel.context)
    tag.kernel = kernel
    tag.last_pos_update = kernel.time
    ctx.tags.append(tag)

    # Adding statistics record
    ctx.statistics.num_tags_created += 1
    generator.num_tags_generated += 1
    ctx.statistics.create_tag_record(tag)

    # Scheduling tag death (remove_tag) and next tag generation (this function)
    kernel.schedule(generator.lifetime, remove_tag, tag)
    kernel.schedule(generator.interval, generate_tag, generator)

    _update_power(kernel.time, ctx.reader, [tag], None, ctx.medium,
                  ctx.statistics)
    kernel.logger.info("(+) tag {} created for {}s: {}".format(
        tag.tag_id, generator.lifetime, str(tag)))


def remove_tag(kernel, tag):
    ctx = kernel.context
    ctx.tags.remove(tag)
    kernel.logger.info("(x) tag {} died".format(tag.tag_id))
    ctx.num_tags_simulated += 1
    if (ctx.max_tags_num is not None and
            ctx.num_tags_simulated >= ctx.max_tags_num):
        kernel.stop()
    # Closing statistics record
    ctx.statistics.close_tag_record(tag)


def update_positions(kernel):
    ctx = kernel.context

    kernel.schedule(kernel.context.update_interval, update_positions)
    _update_power(kernel.time, ctx.reader, ctx.tags, ctx.transaction,
                  ctx.medium, ctx.statistics)


def finish_transaction(kernel, transaction):
    kernel.logger.trace("finished transaction: {}".format(str(transaction)))
    ctx = kernel.context
    reader = ctx.reader
    assert transaction is ctx.transaction

    tag, frame, snr, ber = transaction.received_tag_frame(
        ctx.medium, kernel.time)
    if frame is not None:
        if isinstance(frame.reply, std.AckReply):
            tag_read_record = (
                ctx.statistics.get_tag_record(tag)
                .new_tag_read_record(reader, reader.inventory_round.index))
            tag_read_record.tag_pos = np.array(tag.pos, copy=True)
            tag_read_record.reader_antenna_pos = np.array(
                reader.antenna.pos, copy=True)
            tag_read_record.ber = ber
            tag_read_record.snr = snr

            # noinspection PyShadowingNames
            def on_slot_end(round_index, slot_index, reader, tag, statistics):
                statistics.get_tag_record(tag).close_tag_read_record()
                reader.slot_finish_listeners.remove(
                    statistics.slot_end_listener_id)

            ctx.statistics.slot_end_listener_id = \
                ctx.reader.slot_finish_listeners.add(
                    on_slot_end, reader=reader, tag=tag,
                    statistics=ctx.statistics)

            kernel.logger.info(
                "---> Received tag data: EPC={}, received power={} from tag {}"
                "".format(
                    "".join("{:02X}".format(b) for b in frame.reply.epc),
                    transaction.reader_rx_power_map.get(tag), tag.tag_id))

        if isinstance(frame.reply, std.ReadReply):
            tag_read_record = ctx.statistics.get_tag_record(tag).tag_read_record
            tag_read_record.read_tid = True

            kernel.logger.info(
                "---> Received TID: memory={}, received power={} from tag {}"
                "".format(
                    "".join("{:02X}".format(b) for b in frame.reply.memory),
                    transaction.reader_rx_power_map.get(tag), tag.tag_id))

        cmd_frame = ctx.reader.receive(frame)
    else:
        cmd_frame = ctx.reader.timeout()

    # Processing new command (reader frame)
    ctx.transaction = _build_transaction(kernel, ctx.reader, cmd_frame)
    ctx.transaction.timeout_event_id = kernel.schedule(
        transaction.duration, finish_transaction, ctx.transaction)
    if transaction.reply_start_time is not None:
        dt = transaction.reply_start_time - kernel.time
        kernel.schedule(dt, update_power_at_response_start, transaction)


def switch_reader_antenna(kernel, reader):
    antenna = reader.select_next_antenna()
    kernel.logger.debug("switched antenna #{}".format(antenna.index))
    reader.antenna_switch_event_id = kernel.schedule(
        reader.antenna_switch_interval, switch_reader_antenna, reader)


def update_power_at_response_start(kernel, transaction):
    ctx = kernel.context
    _update_power(kernel.time, ctx.reader, ctx.tags, transaction, ctx.medium,
                  ctx.statistics)
    transaction.response_start_event_id = None
