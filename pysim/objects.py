import functools
import numpy as np
import enum
import itertools

import pysim.epcstd as std
import pysim.channel as chan


#############################################################################
# HELPERS
#############################################################################
class Listeners:
    def __init__(self):
        self._items = []
        self._id = itertools.count()

    def add(self, fn, **kwargs):
        index = next(self._id)
        self._items.append((index, fn, kwargs))
        return index

    def remove(self, index):
        new_items = [item for item in self._items if item[0] != index]
        self._items = new_items

    def clear(self):
        self._items = []

    def call(self, *args, **kwargs):
        for item in self._items:
            fn = item[1]
            _kwargs = dict(kwargs)
            _kwargs.update(item[2])
            fn(*args, **_kwargs)


def cached_method(key, cache_attr_name='__cache__'):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            cache = getattr(self, cache_attr_name)
            if key not in cache:
                cache[key] = fn(self, *args, **kwargs)
            return cache[key]
        return wrapper
    return decorator


def inc_hex_string(s):
    pos = len(s) - 1
    while pos >= 0:
        x = int(s[pos], 16)
        if x < 15:
            return s[:pos] + "{:1X}".format(x + 1) + ("0" * (len(s) - 1 - pos))
        else:
            pos -= 1
    return "0" * len(s)


#############################################################################
# Model
#############################################################################
class Model:
    reader = None
    tags = None
    generators = None
    medium = None
    statistics = None
    update_interval = 0.001
    next_tag_id = itertools.count()
    max_tags_num = None

    def __init__(self):
        self.reader = Reader()
        self.tags = []
        self.statistics = Statistics()
        self.generators = []
        self.medium = Medium()
        self.transaction = None
        self.num_tags_simulated = 0



#############################################################################
# ANTENNAS
#############################################################################
class Antenna:
    index = None
    pos = None          # 3D np.ndarray
    direction_theta = None    # 3D np.ndarray
    direction_phi = np.array([1, 0, 0])
    rp_type = 'dipole'
    cable_loss = -1.0  # dB
    gain = 8.0  # dB

    @property
    def radiation_pattern(self):
        if self.rp_type == 'dipole':
            return chan.rp_dipole
        else:
            raise ValueError("unsupported rp_type='{}'".format(self.rp_type))

    @property
    def normalized_direction_theta(self):
        return self.direction_theta / np.linalg.norm(self.direction_theta)


#############################################################################
# READER
#############################################################################
# ===========================================================================
# Reader states
# ===========================================================================
class _ReaderState:
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._name

    def get_timeout(self, reader):
        raise NotImplementedError

    def enter(self, reader):
        raise NotImplementedError

    def handle_turn_on(self, reader):
        raise NotImplementedError

    def handle_turn_off(self, reader):
        raise NotImplementedError

    def handle_timeout(self, reader):
        raise NotImplementedError

    def handle_query_reply(self, reader, frame):
        raise NotImplementedError

    def handle_ack_reply(self, reader, frame):
        raise NotImplementedError

    def handle_reqrn_reply(self, reader, frame):
        raise NotImplementedError

    def handle_read_reply(self, reader, frame):
        raise NotImplementedError


# ----------------------------------------------------------------------------
# Reader state: OFF
# ----------------------------------------------------------------------------
class _ReaderOFF(_ReaderState):
    def __init__(self):
        super().__init__('OFF')

    def get_timeout(self, reader):
        return reader.power_control_mode.power_off_interval(reader)

    def enter(self, reader):
        # On turning off the reader must finish current round and power down.
        reader.last_rn = None
        reader.stop_round()
        reader.set_power(None)
        return None

    def handle_turn_on(self, reader):
        # On turning on a new round is started, reader is powered up and
        # the FSM moves to the first state as defined by the first slot
        reader.set_power(reader.max_power)
        slot = reader.next_slot()
        if reader.target_strategy == "switch":
            reader.target = std.InventoryFlag.A
            reader.num_rounds_before_target_switch = reader.rounds_per_target

        return reader.set_state(slot.first_state)

    def handle_turn_off(self, reader):
        return None  # Already off

    def handle_timeout(self, reader):
        return reader.turn_on()  # The default action on timeout is turn on

    def handle_query_reply(self, reader, frame):
        return None  # Any reply ignored

    def handle_ack_reply(self, reader, frame):
        return None  # Any reply ignored

    def handle_reqrn_reply(self, reader, frame):
        return None  # Any reply ignored

    def handle_read_reply(self, reader, frame):
        return None  # Any reply ignored


# ----------------------------------------------------------------------------
# Reader state: QUERY
# ----------------------------------------------------------------------------
class _ReaderQUERY(_ReaderState):
    def __init__(self):
        super().__init__('QUERY')

    def get_timeout(self, reader):
        t_cmd = std.query_duration(reader.tari, reader.rtcal, reader.trcal,
                                   reader.delim, reader.dr, reader.tag_encoding,
                                   reader.trext, reader.sel, reader.session,
                                   reader.target, reader.q)
        t1 = std.link_t1_max(reader.rtcal, reader.trcal, reader.dr, reader.temp)
        t3 = std.link_t3()
        return t_cmd + t1 + t3

    def enter(self, reader):
        if reader.target_strategy == "switch":
            if reader.num_rounds_before_target_switch <= 0:
                reader.target = reader.target.invert()
                reader.num_rounds_before_target_switch = \
                    reader.rounds_per_target
            else:
                reader.num_rounds_before_target_switch -= 1

        reader.last_rn = None
        cmd = std.Query(reader.dr, reader.tag_encoding, reader.trext,
                        reader.sel, reader.session, reader.target, reader.q)
        return std.ReaderFrame(reader.preamble, cmd)

    def handle_turn_on(self, reader):
        return None  # Reader is already ON

    def handle_turn_off(self, reader):
        # All actions are performed in OFF.enter(), just move there
        return reader.set_state(Reader.State.OFF)

    def handle_timeout(self, reader):
        slot = reader.next_slot()
        return reader.set_state(slot.first_state)

    def handle_query_reply(self, reader, frame):
        reader.last_rn = frame.reply.rn
        return reader.set_state(Reader.State.ACK)

    def handle_ack_reply(self, reader, frame):
        raise RuntimeError("unexpected AckReply in QUERY state")

    def handle_reqrn_reply(self, reader, frame):
        raise RuntimeError("unexpected ReqRNReply in QUERY state")

    def handle_read_reply(self, reader, frame):
        raise RuntimeError("unexpected ReadReply in QUERY state")


# ----------------------------------------------------------------------------
# Reader state: QREP
# ----------------------------------------------------------------------------
class _ReaderQREP(_ReaderState):
    def __init__(self): super().__init__('QREP')

    def get_timeout(self, reader):
        t_cmd = std.query_rep_duration(reader.tari, reader.rtcal, reader.trcal,
                                       reader.delim, reader.session)
        t1 = std.link_t1_max(reader.rtcal, reader.trcal, reader.dr,
                             reader.temp)
        t3 = std.link_t3()
        return t_cmd + t1 + t3

    def enter(self, reader):
        reader.last_rn = None
        cmd = std.QueryRep(reader.session)
        return std.ReaderFrame(reader.preamble, cmd)

    def handle_turn_on(self, reader): return None

    def handle_turn_off(self, reader):
        return reader.set_state(Reader.State.OFF)

    def handle_timeout(self, reader):
        slot = reader.next_slot()
        return reader.set_state(slot.first_state)

    def handle_query_reply(self, reader, frame):
        reader.last_rn = frame.reply.rn
        return reader.set_state(Reader.State.ACK)

    def handle_ack_reply(self, reader, frame):
        raise RuntimeError("unexpected AckReply in QREP state")

    def handle_reqrn_reply(self, reader, frame):
        raise RuntimeError("unexpected ReqRNReply in QUERY state")

    def handle_read_reply(self, reader, frame):
        raise RuntimeError("unexpected ReadReply in QUERY state")


# ----------------------------------------------------------------------------
# Reader state: ACK
# ----------------------------------------------------------------------------
class _ReaderACK(_ReaderState):
    def __init__(self): super().__init__('ACK')

    def get_timeout(self, reader):
        t_cmd = std.ack_duration(reader.tari, reader.rtcal, reader.trcal,
                                 reader.delim, reader.last_rn)
        t1 = std.link_t1_max(reader.rtcal, reader.trcal, reader.dr,
                             reader.temp)
        t3 = std.link_t3()
        return t_cmd + t1 + t3

    def enter(self, reader):
        cmd = std.Ack(reader.last_rn)
        return std.ReaderFrame(reader.preamble, cmd)

    def handle_turn_on(self, reader): return None

    def handle_turn_off(self, reader):
        return reader.set_state(Reader.State.OFF)

    def handle_timeout(self, reader):
        slot = reader.next_slot()
        return reader.set_state(slot.first_state)

    def handle_query_reply(self, reader, frame):
        raise RuntimeError("unexpected RN16 in ACK state")

    def handle_ack_reply(self, reader, frame):
        if reader.read_tid_bank:
            return reader.set_state(Reader.State.REQRN)
        else:
            slot = reader.next_slot()
            return reader.set_state(slot.first_state)

    def handle_reqrn_reply(self, reader, frame):
        raise RuntimeError("unexpected ReqRNReply in ACK state")

    def handle_read_reply(self, reader, frame):
        raise RuntimeError("unexpected ReadReply in ACK state")


# ----------------------------------------------------------------------------
# Reader state: ReqRN
# ----------------------------------------------------------------------------
class _ReaderREQRN(_ReaderState):
    def __init__(self):
        super().__init__('REQRN')

    def get_timeout(self, reader):
        t_cmd = std.reqrn_duration(reader.tari, reader.rtcal, reader.trcal,
                                   reader.delim, reader.last_rn)
        t1 = std.link_t1_max(reader.rtcal, reader.trcal, reader.dr,
                             reader.temp)
        t3 = std.link_t3()
        return t_cmd + t1 + t3

    def enter(self, reader):
        cmd = std.ReqRN(reader.last_rn)
        return std.ReaderFrame(reader.preamble, cmd)

    def handle_turn_on(self, reader): return None

    def handle_turn_off(self, reader):
        return reader.set_state(Reader.State.OFF)

    def handle_timeout(self, reader):
        slot = reader.next_slot()
        return reader.set_state(slot.first_state)

    def handle_query_reply(self, reader, frame):
        raise RuntimeError("unexpected RN16 in REQRN state")

    def handle_ack_reply(self, reader, frame):
        raise RuntimeError("unexpected AckReply in REQRN state")

    def handle_reqrn_reply(self, reader, frame):
        reader.last_rn = frame.reply.rn
        return reader.set_state(Reader.State.READ)

    def handle_read_reply(self, reader, frame):
        raise RuntimeError("unexpected ReadReply in REQRN state")


# ----------------------------------------------------------------------------
# Reader state: ReqRN
# ----------------------------------------------------------------------------
class _ReaderREAD(_ReaderState):
    def __init__(self):
        super().__init__('READ')

    def get_timeout(self, reader):
        t_cmd = std.read_duration(reader.tari, reader.rtcal, reader.trcal,
                                  reader.delim, std.MemoryBank.TID, 0x00,
                                  reader.read_tid_words_num, reader.last_rn)
        t1 = std.link_t1_max(reader.rtcal, reader.trcal, reader.dr,
                             reader.temp)
        t3 = std.link_t3()
        return t_cmd + t1 + t3

    def enter(self, reader):
        cmd = std.Read(std.MemoryBank.TID, 0x00, reader.read_tid_words_num,
                       reader.last_rn)
        return std.ReaderFrame(reader.preamble, cmd)

    def handle_turn_on(self, reader): return None

    def handle_turn_off(self, reader):
        return reader.set_state(Reader.State.OFF)

    def handle_timeout(self, reader):
        slot = reader.next_slot()
        return reader.set_state(slot.first_state)

    def handle_query_reply(self, reader, frame):
        raise RuntimeError("unexpected RN16 in READ state")

    def handle_ack_reply(self, reader, frame):
        raise RuntimeError("unexpected AckReply in READ state")

    def handle_reqrn_reply(self, reader, frame):
        raise RuntimeError("unexpected ReqRNReply in READ state")

    def handle_read_reply(self, reader, frame):
        assert isinstance(frame.reply, std.ReadReply)
        reader.kernel.logger.info("received TID={}".format(
            "".join("{:02X}".format(b) for b in frame.reply.memory)))
        slot = reader.next_slot()
        return reader.set_state(slot.first_state)


# ===========================================================================
# Reader power control modes
# ===========================================================================
class _PowerControlMode:
    def __init__(self, name):
        self._name = name

    def __str__(self):
        return self._name

    def min_powered_on_interval(self, reader):
        raise NotImplementedError

    def powered_off_interval(self, reader):
        raise NotImplementedError


class _AlwaysPoweredOn(_PowerControlMode):
    def __init__(self):
        super().__init__('ALWAYS_ON')

    def min_powered_on_interval(self, reader):
        return None

    def powered_off_interval(self, reader):
        return None


class _PeriodicPowerOn(_PowerControlMode):
    def __init__(self):
        super().__init__('PERIODIC')

    def min_powered_on_interval(self, reader):
        return reader.power_on_duration

    def powered_off_interval(self, reader):
        return reader.power_off_duration


# ===========================================================================
# Rounds and slots
# ===========================================================================
class _ReaderSlot:
    def __init__(self, owner, index, first_state):
        self._owner, self._index, self._first_state = owner, index, first_state

    @property
    def first_state(self):
        return self._first_state

    @property
    def index(self):
        return self._index

    @property
    def owner(self):
        return self._owner

    def on_start(self, reader):
        reader.kernel.logger.debug(".. SLOT #{} STARTED".format(self.index))
        reader.slot_start_listeners.call(self.owner.index, self.index)

    def on_finish(self, reader):
        reader.slot_finish_listeners.call(self.owner.index, self.index)


class _ReaderRound:
    def __init__(self, reader, index):
        self._index = index

        def slots_gen():
            yield _ReaderSlot(self, 0, Reader.State.QUERY)
            for i in range(1, round(pow(2, reader.q))):
                yield _ReaderSlot(self, i, Reader.State.QREP)

        self._reader = reader
        self._slots = slots_gen()
        self._slot = None

    @property
    def index(self):
        return self._index

    @property
    def slot(self):
        return self._slot

    def next_slot(self):
        if self._slot is not None:
            self._slot.on_finish(self._reader)
        self._slot = next(self._slots)
        self._slot.on_start(self._reader)
        return self._slot

    def on_start(self, reader):
        reader.kernel.logger.debug("ROUND #{} STARTED".format(self.index))
        reader.round_start_listeners.call(self.index)

    def on_finish(self, reader):
        reader.round_finish_listeners.call(self.index)


# ===========================================================================
# Reader class
# ===========================================================================
class Reader:

    class State(enum.Enum):
        OFF = _ReaderOFF()
        QUERY = _ReaderQUERY()
        QREP = _ReaderQREP()
        ACK = _ReaderACK()
        REQRN = _ReaderREQRN()
        READ = _ReaderREAD()

        def __init__(self, obj):
            self.__obj__ = obj

        def __str__(self):
            return self.__obj__.__str__()

        def __getattr__(self, item):
            children = {'enter', 'handle_turn_on', 'handle_turn_off',
                        'handle_query_reply', 'handle_ack_reply',
                        'handle_timeout', 'handle_reqrn_reply',
                        'handle_read_reply', 'get_timeout'}
            if item in children:
                return getattr(self.__obj__, item)
            else:
                raise AttributeError

    class PowerControlMode(enum.Enum):
        ALWAYS_ON = _AlwaysPoweredOn()
        PERIODIC = _PeriodicPowerOn()

        def __init__(self, obj):
            self.__obj__ = obj

        def __str__(self):
            return self.__obj__.__str__()

        def __getattr__(self, item):
            children = {'min_powered_on_interval', 'powered_off_interval'}
            if item in children:
                return getattr(self.__obj__, item)
            else:
                raise AttributeError

    # PIE time settings
    tari = 6.25e-6
    rtcal = 6.25e-6 * 3
    trcal = 6.25e-6 * 5
    delim = 12.5e-6

    # Temperature range
    temp = std.TempRange.NOMINAL

    # Round settings
    q = 2
    tag_encoding = None
    trext = False
    dr = std.DivideRatio.DR_8
    sel = std.SelFlag.ALL
    session = std.Session.S0
    target = std.InventoryFlag.A
    target_strategy = "const"  # or "const" or "switch"
    rounds_per_target = 1

    # Power settings
    max_power = 31.5    # dBm
    power_control_mode = PowerControlMode.PERIODIC
    power_on_duration = 2.0     # sec.
    power_off_duration = 0.5    # sec.
    noise = -80.0       # dBm

    # Operation modes
    read_tid_bank = False
    read_tid_words_num = None

    # Antenna settings (more precisely they must be set up individually)
    always_start_with_first_antenna = True
    antenna_switch_event_id = None
    antenna_switch_interval = None

    def __init__(self, kernel=None):
        self.kernel = kernel
        self._state = Reader.State.OFF
        self._slot_index = 0

        # Antennas
        self._antennas = []
        self._antenna_index = 0

        # Temporary data, e.g. received from the tag
        self.last_rn = None

        # Rounds managers
        self._round = None
        self._round_index = itertools.count()

        # Power-related fields
        self._power = None
        self._time_last_turned_on = None

        # Listeners
        self._state_change_listeners = Listeners()
        self._round_start_listeners = Listeners()   # (round_index,)
        self._round_finish_listeners = Listeners()  # (round_finish,)
        self._power_on_listeners = Listeners()
        self._power_off_listeners = Listeners()
        self._slot_start_listeners = Listeners()  # (round_index, slot_index)
        self._slot_finish_listeners = Listeners()  # (round_index, slot_index)

        # This field is used when target_strategy is "switch"
        self.num_rounds_before_target_switch = None

    @property
    def state(self):
        return self._state

    def set_state(self, new_state):
        self.kernel.logger.debug("reader state changed: {} --> {}".format(
            self.state, new_state))
        self._state_change_listeners.call(self.state, new_state)
        self._state = new_state
        return new_state.enter(self)

    @property
    def state_change_listeners(self):
        return self._state_change_listeners

    @property
    def power_on_listeners(self):
        return self._power_on_listeners

    @property
    def power_off_listeners(self):
        return self._power_off_listeners

    @property
    def power(self):
        return self._power

    @property
    def tx_power(self):
        return self.power

    def set_power(self, power):
        self._power = power

    @property
    def preamble(self):
        return std.ReaderPreamble(self.tari, self.rtcal, self.trcal, self.delim)

    @property
    def sync(self):
        return std.ReaderSync(self.tari, self.rtcal, self.delim)

    def receive(self, tag_frame):
        assert isinstance(tag_frame, std.TagFrame)
        reply = tag_frame.reply
        if isinstance(reply, std.QueryReply):
            return self._state.handle_query_reply(self, tag_frame)
        elif isinstance(reply, std.AckReply):
            return self._state.handle_ack_reply(self, tag_frame)
        elif isinstance(reply, std.ReqRnReply):
            return self._state.handle_reqrn_reply(self, tag_frame)
        elif isinstance(reply, std.ReadReply):
            return self._state.handle_read_reply(self, tag_frame)
        else:
            raise ValueError('unexpected tag reply {}'.format(str(reply)))

    def timeout(self):
        return self._state.handle_timeout(self)

    def turn_on(self):
        self.kernel.logger.debug("reader turned ON")
        self._power_on_listeners.call()
        if self.always_start_with_first_antenna:
            self._antenna_index = 0
        self._time_last_turned_on = self.kernel.time
        return self._state.handle_turn_on(self)

    def turn_off(self):
        self.kernel.logger.debug("reader turned OFF")
        self._power_off_listeners.call()
        self._time_last_turned_on = None
        return self._state.handle_turn_off(self)

    @property
    def time_last_turned_on(self):
        return self._time_last_turned_on

    # Antenna management
    @property
    def antenna_index(self):
        return self._antenna_index

    def attach_antenna(self, antenna):
        antenna.index = len(self._antennas)
        self._antennas.append(antenna)
        return antenna.index

    def get_antenna(self, index):
        return self._antennas[index]

    @property
    def antenna(self):
        return self._antennas[self._antenna_index]

    @property
    def num_antennas(self): return len(self._antennas)

    def select_next_antenna(self):
        if self.num_antennas > 0:
            self._antenna_index = (self._antenna_index + 1) % self.num_antennas
            return self._antennas[self._antenna_index]
        else:
            return None

    # Round management

    @property
    def inventory_round(self):
        return self._round

    def stop_round(self):
        if self._round:
            self._round.slot.on_finish(self)
            self._round.on_finish(self)
        self._round = None

    def next_slot(self):
        if self._round is None:
            self._round = _ReaderRound(self, next(self._round_index))
            self._round.on_start(self)
            slot = self._round.next_slot()
        else:
            try:
                slot = self._round.next_slot()
            except StopIteration:
                self._round.on_finish(self)
                self._round = _ReaderRound(self, next(self._round_index))
                self._round.on_start(self)
                slot = self._round.next_slot()
        return slot

    @property
    def round_start_listeners(self):
        return self._round_start_listeners

    @property
    def round_finish_listeners(self):
        return self._round_finish_listeners

    @property
    def slot_start_listeners(self):
        return self._slot_start_listeners

    @property
    def slot_finish_listeners(self):
        return self._slot_finish_listeners


#############################################################################
# TAG
#############################################################################
class Tag:
    class State(enum.Enum):
        OFF = 0
        READY = 1
        ARBITRATE = 2
        REPLY = 3
        ACKNOWLEDGED = 4
        SECURED = 5

    # Geometric settings
    velocity = None     # set by the generator
    direction = None    # should be a 3-dim np.ndarray
    last_pos_update = None  # sec.

    # EPC Std. settings
    epc = ""            # should be a hex-string
    tid = None          # should be either None or hex-string
    user_mem = None     # should be either None or hex-string
    s1_persistence = 2.0    # sec.
    s2_persistence = 2.0    # sec.
    s3_persistence = 2.0    # sec.

    # Power and antenna settings
    modulation_loss = -18.0     # dB

    def __init__(self, tag_id, kernel=None):
        self.kernel = kernel
        self._tag_id = tag_id

        # Antennas and geometry
        self.antenna = Antenna()
        self.antenna.index = 0
        self.sensitivity = -18.0

        # Internal registers and flags
        self._state = Tag.State.OFF
        self._slot_counter = 0
        self._rn = 0
        self._powered_on_time = None
        self._powered_off_time = 0.0
        self._power_update_time = None
        self._power = None
        self._sl = False
        self._active_session = None
        self._preamble = None
        self.sessions = {}
        for session in {std.Session.S0, std.Session.S1, std.Session.S2,
                        std.Session.S3}:
            self.sessions[session] = None

        # Persistence dictionary is used to access sX_persistence via
        # method persistence(session)
        self._persistence = {std.Session.S0: lambda tag: None,
                             std.Session.S1: lambda tag: tag.s1_persistence,
                             std.Session.S2: lambda tag: tag.s2_persistence,
                             std.Session.S3: lambda tag: tag.s3_persistence}

        self._banks = {std.MemoryBank.EPC: lambda tag: tag.epc,
                       std.MemoryBank.TID: lambda tag: tag.tid,
                       std.MemoryBank.USER: lambda tag: tag.user_mem,
                       std.MemoryBank.RESERVED: lambda tag: None}

        # Parameters received from the reader
        self._encoding = std.TagEncoding.FM0
        self._blf = std.get_blf(std.DivideRatio.DR_8, 12.5e-6*6)
        self._trext = False

    def persistence(self, session):
        fn = self._persistence[session]
        assert callable(fn)
        return fn(self)

    def bank_data(self, bank):
        fn = self._banks[bank]
        assert callable(fn)
        return fn(self)

    @property
    def pos(self):
        return self.antenna.pos

    @pos.setter
    def pos(self, value):
        self.antenna.pos = np.asarray(value)

    @property
    def encoding(self):
        return self._encoding

    @property
    def logger(self):
        return self.kernel.logger

    @property
    def blf(self):
        return self._blf

    @property
    def trext(self):
        return self._trext

    @property
    def tag_id(self):
        return self._tag_id

    @property
    def normalized_direction(self):
        return self.direction / np.linalg.norm(self.direction)

    @property
    def state(self):
        return self._state

    @property
    def power(self):
        return self._power

    @property
    def tx_power(self):
        return (self._power + self.modulation_loss if self._power is not None
                else None)

    @property
    def slot_counter(self):
        return self._slot_counter

    @property
    def rn(self):
        return self._rn

    @property
    def sl(self):
        return self._sl

    @property
    def s0(self):
        return self.sessions[std.Session.S0]

    @property
    def s1(self):
        return self.sessions[std.Session.S1]

    @property
    def s2(self):
        return self.sessions[std.Session.S2]

    @property
    def s3(self):
        return self.sessions[std.Session.S3]

    def setup(self, time, powered_on=False):
        for session in {std.Session.S0, std.Session.S1, std.Session.S2,
                        std.Session.S3}:
            self.sessions[session] = std.InventoryFlag.A
        self._sl = False
        self._rn = 0x0000
        self._slot_counter = 0
        self._active_session = None
        self._preamble = None
        if powered_on:
            self._powered_off_time = None
            self._powered_on_time = time
            self._set_state(Tag.State.READY)
        else:
            self._powered_off_time = time
            self._powered_on_time = None
            self._set_state(Tag.State.OFF)

    def _power_on(self, time, power):
        if self.state is Tag.State.OFF:
            # Updating sessions
            interval = time - self._powered_off_time
            for session in self.sessions.keys():
                stored_value = self.sessions[session]
                persistence = self.persistence(session)
                self.sessions[session] = session.power_on_value(
                    interval, persistence, stored_value)
            # Updating timestamps and power
            self._powered_on_time = time
            self._powered_off_time = None
            self._power_update_time = time
            self._power = power
            self.logger.debug("tag {} powered on: {}".format(
                self._tag_id, self.describe()))
            self._set_state(Tag.State.READY)

    def _power_off(self, time):
        if self.state is not Tag.State.OFF:
            self._powered_on_time = None
            self._powered_off_time = time
            self._power_update_time = time
            self._power = None
            self._active_session = None
            self._preamble = None
            self.logger.debug("tag {} powered off: {}".format(
                self._tag_id, self.describe()))
            self._set_state(Tag.State.OFF)

    def set_power(self, time, power):
        if self.state is Tag.State.OFF:
            if power is not None and power > self.sensitivity:
                self._power_on(time, power)
                self._power_update_time = time
        else:
            if power is None or power < self.sensitivity:
                self._power_off(time)
            else:
                self._power = power
                self._power_update_time = time

    def _set_state(self, new_state):
        if self._state != new_state:
            self.kernel.logger.trace(
                "tag {} state changed: {} --> {}, {}".format(
                    self.tag_id, self.state.name, new_state.name,
                    self.describe()))
        self._state = new_state

    def process_query(self, query):
        assert isinstance(query, std.ReaderFrame)
        assert isinstance(query.command, std.Query)
        assert isinstance(query.preamble, std.ReaderPreamble)
        command, preamble = query.command, query.preamble
        if self.state is Tag.State.OFF:
            return None

        if self.state not in {Tag.State.READY, Tag.State.ARBITRATE,
                              Tag.State.REPLY}:
            flag = self.sessions[self._active_session]
            self.sessions[self._active_session] = flag.invert()

        # Checking flags
        if not (self.sessions[command.session] == command.target and
                command.sel.match(self.sl)):
            self._set_state(Tag.State.READY)
            return None

        # Processing QUERY: select random slot, move to REPLY or ARBITRATE,
        # set current session, extract TRext and compute BLF
        self._active_session = command.session
        self._trext = command.trext
        self._encoding = command.m
        self._blf = std.get_blf(command.dr, preamble.trcal)
        self._slot_counter = np.random.randint(0, pow(2, command.q))
        self._preamble = std.create_tag_preamble(self.encoding, self.trext)
        if self._slot_counter == 0:
            self._set_state(Tag.State.REPLY)
            self._rn = np.random.randint(0, 0x10000)
            return std.TagFrame(self._preamble, std.QueryReply(self._rn))
        else:
            self._set_state(Tag.State.ARBITRATE)
            return None

    def process_query_rep(self, frame):
        assert isinstance(frame, std.ReaderFrame)
        assert isinstance(frame.command, std.QueryRep)
        qrep = frame.command
        if self.state is Tag.State.OFF:
            return None

        if qrep.session is not self._active_session:
            return None

        self._slot_counter -= 1
        if self._slot_counter == 0 and self.state is Tag.State.ARBITRATE:
            self._set_state(Tag.State.REPLY)
            self._rn = np.random.randint(0, 0x10000)
            return std.TagFrame(self._preamble, std.QueryReply(self._rn))
        else:
            if self.state in {Tag.State.ARBITRATE, Tag.State.REPLY}:
                self._set_state(Tag.State.ARBITRATE)
            elif self.state is not Tag.State.READY:
                flag = self.sessions[self._active_session]
                self.sessions[self._active_session] = flag.invert()
                self._set_state(Tag.State.READY)

            return None

    def process_ack(self, frame):
        assert isinstance(frame, std.ReaderFrame)
        assert isinstance(frame.command, std.Ack)
        ack = frame.command
        if self.state is not Tag.State.REPLY:
            return None
        if ack.rn == self.rn:
            self._set_state(Tag.State.ACKNOWLEDGED)
            return std.TagFrame(self._preamble, std.AckReply(self.epc))
        else:
            self._set_state(Tag.State.ARBITRATE)
            return None

    def process_reqrn(self, frame):
        assert isinstance(frame, std.ReaderFrame)
        assert isinstance(frame.command, std.ReqRN)
        reqrn = frame.command
        if self.state not in {Tag.State.ACKNOWLEDGED, Tag.State.SECURED}:
            return None
        if reqrn.rn == self.rn:
            self._set_state(Tag.State.SECURED)
            self._rn = np.random.randint(0, 0x10000)
            return std.TagFrame(self._preamble, std.ReqRnReply(self._rn))
        else:
            return None

    def process_read(self, frame):
        assert isinstance(frame, std.ReaderFrame)
        assert isinstance(frame.command, std.Read)
        read = frame.command
        if self.state is not Tag.State.SECURED:
            return None
        if read.rn == self.rn:
            content = self.bank_data(read.bank)
            # Извлекаем из банка ровно столько данных, сколько запрошено.
            # В команде указывается число слов (по два байта), а в content
            # лежит hex-строка, в которой каждый байт кодируется двумя
            # символами. Поэтому надо извлечь (word_count * 4) 16-ричных
            # цифр из строки content.
            if (frame.command.word_count * 4) < len(content):
                content = content[:frame.command.word_count * 4]
            # print(f"Content ({len(content) // 4} words): {content}")
            return std.TagFrame(
                self._preamble, std.ReadReply(content, rn=self.rn))

    def receive(self, frame):
        assert isinstance(frame, std.ReaderFrame)
        cmd = frame.command
        if isinstance(cmd, std.Query):
            return self.process_query(frame)
        elif isinstance(cmd, std.QueryRep):
            return self.process_query_rep(frame)
        elif isinstance(cmd, std.Ack):
            return self.process_ack(frame)
        elif isinstance(cmd, std.ReqRN):
            return self.process_reqrn(frame)
        elif isinstance(cmd, std.Read):
            return self.process_read(frame)
        else:
            raise TypeError("unexpected command '{}'".format(frame))

    def describe(self):
        return ("tag {{ id={}, state={}, pos={}, power={}, "
                "S0={}, S1={}, S2={}, S3={}, SL={}, M={}, CNT={}, RN={}".format(
                    self.tag_id, self.state.name, self.pos, self.power, self.s0,
                    self.s1, self.s2, self.s3, self.sl, self.encoding,
                    self._slot_counter, self.rn))

    def __str__(self):
        return ("Tag {{ id={self.tag_id}, pos={self.pos}, "
                "velocity={self.velocity:.3f}, direction={self.direction}, "
                "state={self.state.name}, power={self.power}, "
                "S0={s0}, S1={s1}, "
                "S2={s2}, S3={s3}, SL={self.sl}, M={self.encoding}, "
                "TRext={self.trext}, EPC={self.epc}, TID={self.tid} }}".format(
                    self=self, s0=self.sessions[std.Session.S0],
                    s1=self.sessions[std.Session.S1],
                    s2=self.sessions[std.Session.S2],
                    s3=self.sessions[std.Session.S3]))

    @staticmethod
    def get_new_slot_state(new_slot_counter, curr_state, match_flags=True):
        if curr_state is Tag.State.OFF:
            return Tag.State.OFF
        else:
            if not match_flags:
                return Tag.State.READY
            else:
                if new_slot_counter == 0:
                    return Tag.State.REPLY
                else:
                    return Tag.State.ARBITRATE


#############################################################################
# Generators
#############################################################################
class Generator:
    pos0 = None  # should be a 3-dim np.ndarray
    velocity = 10.0 / 3.6  # meters per second
    direction = np.asarray([0, 1, 0])  # should be a 3-dim np.array
    tag_antenna_direction = None
    travel_distance = 20.0  # meters
    epc_bitlen = 96
    tid_bitlen = 64
    epc_prefix = 'AAAA'
    tid_prefix = 'AAAA'
    max_tags_generated = -1
    num_tags_generated = 0

    # Antenna and power parameters
    antenna_gain = 2.0          # dBm
    cable_loss = 0.0            # dBm
    modulation_loss = -12.0     # dBm
    sensitivity = -18.0         # dBm

    def __init__(self):
        self._next_interval = (lambda: 1.0, )

    def set_interval(self, fn, *args):
        self._next_interval = (fn, ) + args

    @property
    def interval(self):
        fn = self._next_interval[0]
        args = self._next_interval[1:]
        return fn(*args)

    @property
    def lifetime(self):
        return self.travel_distance / self.velocity

    def create_tag(self, model):
        # print("GENERATOR: create new tag")
        def hex_string_bitlen(s):
            return len(s.strip()) * 4

        epc_suffix_bitlen = self.epc_bitlen - hex_string_bitlen(self.epc_prefix)
        tid_suffix_bitlen = self.tid_bitlen - hex_string_bitlen(self.tid_prefix)
        self._epc_suffix = '0' * int(np.ceil(epc_suffix_bitlen / 4))
        self._tid_suffix = '0' * int(np.ceil(tid_suffix_bitlen / 4))

        tag_id = next(model.next_tag_id)
        tag = Tag(tag_id)
        tag.epc = self.epc_prefix + self._epc_suffix
        tag.tid = self.tid_prefix + self._tid_suffix
        self._epc_suffix = inc_hex_string(self._epc_suffix)
        self._tid_suffix = inc_hex_string(self._tid_suffix)
        tag.pos = np.array(self.pos0, copy=True)
        tag.velocity = self.velocity
        tag.direction = np.array(self.direction, copy=True)
        tag.antenna.gain = self.antenna_gain
        tag.antenna.direction_theta = np.array(self.tag_antenna_direction, copy=True)
        tag.antenna.cable_loss = self.cable_loss
        tag.sensitivity = self.sensitivity
        tag.modulation_loss = self.modulation_loss
        return tag


#############################################################################
# Medium
#############################################################################
class Medium:
    SPEED_OF_LIGHT = 2.99792458 * 1e8

    bandwidth = 1.2e6     # or 0.6, MHz
    ber_distribution = 'rayleigh'
    ground_reflection_type = 'reflection'  # or 'const'
    frequency = 860 * 1e6
    permittivity = 15.0
    conductivity = 0.03
    polarization_loss = -3.0
    use_doppler = True

    def __init__(self):
        pass

    @property
    def ground_reflection(self):
        if self.ground_reflection_type == 'reflection':
            return chan.reflection
        elif self.ground_reflection_type == 'const':
            return chan.reflection_constant
        else:
            raise ValueError("unsupported reflection type = '{}'".format(
                self.ground_reflection_type))

    @property
    def wavelen(self):
        return self.SPEED_OF_LIGHT / self.frequency

    def _get_path_loss(self, on_interval, tx_ant, rx_ant, tx_vel, rx_vel,
                       polarization):
        assert isinstance(tx_ant, Antenna)
        assert isinstance(rx_ant, Antenna)

        if not self.use_doppler:
            on_interval = 0.0

        pl = chan.two_ray_pathloss(
            time=on_interval, ground_reflection=self.ground_reflection,
            wavelen=self.wavelen, tx_pos=tx_ant.pos,
            tx_dir_theta=tx_ant.normalized_direction_theta,
            tx_dir_phi=tx_ant.direction_phi,
            tx_velocity=tx_vel, tx_rp=tx_ant.radiation_pattern,
            rx_pos=rx_ant.pos, rx_dir_theta=rx_ant.normalized_direction_theta,
            rx_dir_phi=rx_ant.direction_phi, rx_velocity=rx_vel,
            rx_rp=rx_ant.radiation_pattern, log=True,
            polarization=polarization, conductivity=self.conductivity,
            permittivity=self.permittivity) + self.polarization_loss

        # TODO: uncomment three lines blow for PL debug:
        # print(f"PL = {pl}")
        # print(f"- tx_ant: pos={tx_ant.pos}, theta={tx_ant.direction_theta}, phi={tx_ant.direction_phi}, vel={tx_vel}")
        # print(f"- rx_ant: pos={rx_ant.pos}, theta={rx_ant.direction_theta}, phi={rx_ant.direction_phi}, vel={rx_vel}")

        return pl

    def get_forward_path_loss(self, reader, tag, time):
        if reader.power is None:
            return MIN_POWER_DBM
        on_interval = time - reader.time_last_turned_on
        tag_velocity = tag.velocity * tag.normalized_direction
        reader_velocity = np.asarray([0, 0, 0])
        pl = self._get_path_loss(on_interval, reader.antenna, tag.antenna,
                                 reader_velocity, tag_velocity, 0.5)
        return pl

    def get_backward_path_loss(self, reader, tag, time):
        if tag.power is None:
            return MIN_POWER_DBM
        on_interval = time - reader.time_last_turned_on
        tag_velocity = tag.velocity * tag.normalized_direction
        reader_velocity = np.asarray([0, 0, 0])
        pl = self._get_path_loss(on_interval, tag.antenna, reader.antenna,
                                 tag_velocity, reader_velocity, 1.0)
        return pl

    def estimate_tag_rx_power(self, reader, tag, time):
        if reader.power is None:
            return None
        pl = self.get_forward_path_loss(reader, tag, time)
        return (reader.tx_power + pl + reader.antenna.gain + tag.antenna.gain
                + reader.antenna.cable_loss + tag.antenna.cable_loss)

    def estimate_reader_rx_power(self, reader, tag, time):
        if tag.power is None:
            return None
        pl = self.get_backward_path_loss(reader, tag, time)
        return (tag.tx_power + pl + reader.antenna.gain + tag.antenna.gain
                + reader.antenna.cable_loss + tag.antenna.cable_loss)

    def estimate_reader_rx_snr(self, reader, tag, tags, time):
        power = self.estimate_reader_rx_power(reader, tag, time)
        if power is None:
            return 0.0
        # print('>>>>>>>>> power', power)
        raw_snr = chan.snr(power, reader.noise)
        # print('>>>>>>>>> snr', raw_snr)
        blf = tag.blf
        m = tag.encoding
        symbol = 1.0 / blf
        # print('>>>>>>>>> blf, m, symbol', blf, m, symbol)
        snr = chan.snr_full(
            snr=raw_snr, miller=m.symbols_per_bit, symbol=symbol,
            preamble=std.tag_preamble_duration(blf, m),
            bandwidth=self.bandwidth)
        # print('>>>>>>>>>> snr full', snr)
        return snr

    def estimate_reader_rx_ber(self, reader, tag, tags, snr):
        return chan.ber(snr)


#############################################################################
# Transactions
#############################################################################
class _TagPowerMinMap(object):
    def __init__(self, values):
        self._tag_power_map = {}
        for tag, power in values:
            self._tag_power_map[tag] = power

    def update(self, tag, power):
        if tag in self._tag_power_map:
            prev_power = self._tag_power_map[tag]
            if prev_power is not None:
                self._tag_power_map[tag] = power

    def get(self, tag):
        return self._tag_power_map.get(tag, None)


class Transaction(object):
    timeout_event_id = None
    response_start_event_id = None

    def __init__(self, medium, reader, command, replies, time):
        self._command = command
        self._reader = reader
        self._replies = tuple(replies)
        self._start_time = time

        self._command_duration = command.duration
        self._command_end_time = time + self._command_duration

        # Whether the transaction involves replies, its duration is measured
        # as maximum of (command + T4) and (command + T1 + reply + T3).
        # T4 is a minimum interval between successive commands.
        # Reply duration is taken as maximum reply duration among all replies.
        # If no replies exist, reader.state.get_timeout() is used.
        if replies:
            reply_durations = [f.get_duration(tag.blf) for tag, f in replies]
            self._reply_duration = np.max(reply_durations)
            t1 = std.link_t1_min(
                reader.rtcal, reader.trcal, reader.dr, reader.temp)
            t2 = std.link_t2_max(reader.trcal, reader.dr)   # NOTE: may be min?
            t4 = std.link_t4(reader.rtcal)
            exchange_duration = (self._command_duration + t1 +
                                 self._reply_duration + t2)
            self._reply_start_time = time + t1
            self._reply_end_time = self._reply_start_time + self._reply_duration
            self._duration = max(exchange_duration, self._command_duration + t4)
        else:
            self._reply_start_time = None
            self._reply_end_time = None
            self._reply_duration = None
            self._duration = reader.state.get_timeout(reader)

        self._finish_time = time + self._duration

        reader_rx_powers = \
            [(tag, medium.estimate_reader_rx_power(reader, tag, time))
             for (tag, f) in self.replies]
        self._reader_rx_powers = _TagPowerMinMap(reader_rx_powers)

    @property
    def command(self):
        return self._command

    @property
    def reader(self):
        return self._reader

    @property
    def replies(self):
        return self._replies

    @property
    def start_time(self):
        return self._start_time

    @property
    def command_end_time(self):
        return self._command_end_time

    @property
    def reply_start_time(self):
        return self._reply_start_time

    @property
    def reply_end_time(self):
        return self._reply_end_time

    @property
    def duration(self):
        return self._duration

    @property
    def finish_time(self):
        return self._finish_time

    @property
    def command_duration(self):
        return self._command_duration

    @property
    def reply_duration(self):
        return self._reply_duration

    @property
    def tags(self):
        return (tag for (tag, _) in self.replies)

    @property
    def reader_rx_power_map(self):
        return self._reader_rx_powers

    def received_tag_frame(self, medium, time):
        # NOTE: if two or more tags reply, their reply is treated as collision
        #       no matter of SNR. Try to implement this.
        if len(self.replies) != 1:
            return None, None, None, None
        tag, frame = self.replies[0]
        snr = medium.estimate_reader_rx_snr(self.reader, tag, self.tags, time)
        ber = medium.estimate_reader_rx_ber(self.reader, tag, self.tags, snr)
        receive_probability = pow(1.0 - ber, frame.reply.bitlen)
        p = np.random.uniform(0.0, 1.0)
        return (tag, frame, snr, ber) if p <= receive_probability else \
            (None, None, None, None)

    def __str__(self):
        replies = ", ".join("{} from {}".format(str(r.reply), t.tag_id)
                            for t, r in self.replies)
        return "Transaction {{ cmd={}, replies={}, duration={:.9f} }}".format(
            self.command.command, replies, self.duration)


#############################################################################
# Statistics
#############################################################################
MIN_POWER_DBM = -120  # dBm - use this value to replace None where needed


class _TagReadRecord:
    round_index = None
    antenna_index = None
    tag_pos = None
    reader_antenna_pos = None
    ber = None
    snr = None
    read_tid = False

    def __str__(self):
        return ("(round={}, ant={}, tag_pos={}, ant_pos={}, BER={}, SNR={},"
                "read_tid={})"
                "".format(self.round_index, self.antenna_index,
                          self.tag_pos, self.reader_antenna_pos,
                          self.ber, self.snr, self.read_tid))


class _TagPowerRecord:
    def __init__(self):
        self.time = None
        self.field_lifetime = None
        self.tag_pos = None
        self.reader_antenna_index = None
        self.reader_antenna_pos = None
        self._tag_rx_power = None
        self._tag_tx_power = None
        self._reader_rx_power = None
        self._reader_tx_power = None
        self.reader_tag_pl = None
        self.tag_reader_pl = None
        self.snr = None
        self.ber = None

    @property
    def tag_rx_power(self):
        if self._tag_rx_power is None:
            return MIN_POWER_DBM
        else:
            return self._tag_rx_power

    @tag_rx_power.setter
    def tag_rx_power(self, value): self._tag_rx_power = value

    @property
    def tag_tx_power(self):
        if self._tag_tx_power is None:
            return MIN_POWER_DBM
        else:
            return self._tag_tx_power

    @tag_tx_power.setter
    def tag_tx_power(self, value):
        self._tag_tx_power = value

    @property
    def reader_rx_power(self):
        if self._reader_rx_power is None:
            return MIN_POWER_DBM
        else:
            return self._reader_rx_power

    @reader_rx_power.setter
    def reader_rx_power(self, value):
        self._reader_rx_power = value

    @property
    def reader_tx_power(self):
        if self._reader_tx_power is None:
            return MIN_POWER_DBM
        else:
            return self._reader_tx_power

    @reader_tx_power.setter
    def reader_tx_power(self, value): self._reader_tx_power = value

    def __str__(self):
        return "time={:.9f}, t_on={:12.9f}, tag_pos={:14s}, " \
               "antenna_index={}, " \
               "antenna_pos={:8s}, tag_rx_power={:.2f}, " \
               "tag_tx_power={:.2f}, reader_rx_power={:.2f}, " \
               "reader_tx_power={:.2f}, SNR={:.4f}, BER={:.6f}, " \
               "PLrt={:.2f}, PLtr={:.2f}".format(
                self.time, self.field_lifetime, str(self.tag_pos),
                self.reader_antenna_index,
                str(self.reader_antenna_pos), self.tag_rx_power,
                self.tag_tx_power, self.reader_rx_power, self.reader_tx_power,
                self.snr, self.ber, self.reader_tag_pl, self.tag_reader_pl)


class _TagRecord:
    def __init__(self, tag):
        self._tag = tag
        # list of _TagReadRecord's
        self.inventory_history = []
        self.num_rounds_attained = 0
        # list of (pos, antenna, power@tag, power@reader, BER):
        self.power_mapping = []
        self._tag_read_record = None

    @property
    def tag(self):
        return self._tag

    def write_power_record(self, time, reader, medium):
        assert isinstance(medium, Medium)
        record = _TagPowerRecord()
        record.time = time
        if reader.time_last_turned_on is not None:
            record.field_lifetime = time - reader.time_last_turned_on
        else:
            record.field_lifetime = np.inf
        record.tag_pos = np.array(self.tag.pos, copy=True)
        record.reader_antenna_index = reader.antenna_index
        record.reader_antenna_pos = np.array(reader.antenna.pos, copy=True)
        record.tag_rx_power = self.tag.power
        record.tag_tx_power = self.tag.tx_power
        record.reader_rx_power = \
            medium.estimate_reader_rx_power(reader, self.tag, time)
        record.reader_tx_power = reader.power
        record.snr = medium.estimate_reader_rx_snr(
            reader, self.tag, [self._tag], time)
        record.ber = medium.estimate_reader_rx_ber(
            reader, self.tag, [self._tag], record.snr)
        record.reader_tag_pl = \
            medium.get_forward_path_loss(reader, self.tag, time)
        record.tag_reader_pl = \
            medium.get_backward_path_loss(reader, self.tag, time)
        self.power_mapping.append(record)

    def new_tag_read_record(self, reader, round_index):
        self._tag_read_record = _TagReadRecord()
        self._tag_read_record.round_index = round_index
        self._tag_read_record.antenna_index = reader.antenna_index
        return self._tag_read_record

    @property
    def tag_read_record(self): return self._tag_read_record

    def close_tag_read_record(self):
        if self._tag_read_record:
            self.inventory_history.append(self._tag_read_record)
            self._tag_read_record = None

    def to_long_string(self):
        return """TagRecord {{
        tag = {},
        num_rounds_attained = {},
        inventory_history = [{}],
        power_mapping = [{}],
    }}""".format(
            self._tag, self.num_rounds_attained,
            "\n\t\t\t".join(str(rec) for rec in self.inventory_history),
            "\n\t\t\t".join(str(rec) for rec in self.power_mapping))


class Statistics:
    num_tags_created = 0

    def __init__(self):
        self.tags_history = []
        self.use_power_statistics = True
        self._current_tag_records = {}

        self.slot_end_listener_id = None

    def create_tag_record(self, tag):
        record = _TagRecord(tag)
        self._current_tag_records[tag] = record
        return record

    def get_tag_record(self, tag):
        return self._current_tag_records.get(tag, None)

    def close_tag_record(self, tag):
        record = self._current_tag_records.pop(tag)
        self.tags_history.append(record)

    def average_rounds_per_tag(self):
        nums = [tr.num_rounds_attained for tr in self.tags_history]
        return np.average(nums)

    def inventory_probability(self):
        recs = [tr for tr in self.tags_history if tr.inventory_history]
        return len(recs) / len(self.tags_history)

    def read_tid_probability(self):
        recs = [tr for tr in self.tags_history if
                len([trd for trd in tr.inventory_history if trd.read_tid]) > 0]
        return len(recs) / len(self.tags_history)

    def to_long_string(self):
        return """Statistics {{
num_tags_created = {},
tags_history = {},
}}""".format(self.num_tags_created,
             "\n\t".join(rec.to_long_string() for rec in self.tags_history))
