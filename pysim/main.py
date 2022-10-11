from multiprocessing import Pool
import multiprocessing
import click
from time import time_ns
from tabulate import tabulate

from pysim import simulator as sim
from pysim import epcstd as std

import pysim.models as models
from pysim.models import KMPH_TO_MPS_MUL


DEFAULT_SPEED = 10             # kmph
DEFAULT_ENCODING = '2'        # FM0, M2, M4, M8
DEFAULT_TARI = "12.5"          # 6.25, 12.5, 18.75, 25
DEFAULT_USE_TREXT = False      # don't use extended preamble
DEFAULT_USE_DOPPLER = True     # simulate Doppler shift
DEFAULT_FREQUENCY = 860.0      # reader frequency in MHz
DEFAULT_Q = 2                  # Q parameter
DEFAULT_NUM_TAGS = 1_000       # number of tags to simulate
DEFAULT_TID_WORD_SIZE = 64     # number of words to read from TID (=1024 bits)
DEFAULT_READER_OFFSET = 5.0    # meters from the wall
DEFAULT_TAG_OFFSET = 5.0       # meters from the wall
DEFAULT_ALTITUDE = 5.0
DEFAULT_NUM_TAGS = 100
DEFAULT_POWER = 31.5


# ----------------------------------------------------------------------------
@click.group()
def cli():
    pass


@cli.command("start")
@click.option(
    "-s", "--speed", default=(DEFAULT_SPEED,), multiple=True,
    help="Vehicle speed, kmph. You can provide multiple values, e.g. "
         "`-s 10 -s 20 -s 80` for parallel computation.",
    show_default=True,)
@click.option(
    "-m", "--encoding", type=click.Choice(["1", "2", "4", "8"]),
    default=DEFAULT_ENCODING, help="Tag encoding", show_default=True)
@click.option(
    "-t", "--tari", default=DEFAULT_TARI, show_default=True,
    type=click.Choice(["6.25", "12.5", "18.75", "25"]), help="Tari value")
@click.option(
    "-ws", "--tid-word-size", default=(DEFAULT_TID_WORD_SIZE,), multiple=True,
    help="Size of TID bank in words (x16 bits). This is both TID bank "
         "size and the number of words the reader requests from the tag. "
         "You can provide multiple values for this parameter for parallel "
         "computation.",
    show_default=True,)
@click.option(
    "-a", "--altitude", multiple=True, default=(DEFAULT_ALTITUDE,),
    help="Drone with RFID-reader altitude. You can pass multiple values of "
         "this parameter for parallel computation.",
    show_default=True)
@click.option(
    "-ro", "--reader-offset", default=(DEFAULT_READER_OFFSET,), multiple=True,
    help="Reader offset from the wall. You can pass multiple values of this "
         "parameter for parallel computation.",
    show_default=True,)
@click.option(
    "-to", "--tag-offset", default=(DEFAULT_TAG_OFFSET,), multiple=True,
    help="Tag offset from the wall. You can pass multiple values of this "
         "parameter for parallel computation.",
    show_default=True)
@click.option(
    "-p", "--power", default=(DEFAULT_POWER,), multiple=True,
    help="Reader transmitter power. You can pass multiple values of this "
         "parameter for parallel computation",
    show_default=True)
@click.option(
    "-n", "--num-tags", default=DEFAULT_NUM_TAGS, show_default=True,
    help="Number of tags to simulate")
@click.option(
    "-j", "--jobs", default=multiprocessing.cpu_count(), show_default=True,
    help="Number of parallel jobs to run when multiple arguments are given.")
@click.option(
    "-v", "--verbose", is_flag=True, default=False, show_default=True,
    help="Print additional data, e.g. detailed model configuration")
def start_single(verbose: bool = False, **kwargs):
    # Сначала проверим, указан ли какой-то параметр несколько раз.
    # Если такой есть и он один, то выполним несколько симуляций параллельно.
    # Если все параметры даны в одном экземпляре, то выполним одну симуляцию.
    # Если несколько параметров заданы со множеством значений, это ошибка.
    var_arg_names = (
        'speed', 'tid_word_size', 'altitude', 'reader_offset',
        'tag_offset', 'power')
    variadic = None
    for arg_name in var_arg_names:
        if len(kwargs[arg_name]) > 1:
            if variadic is not None:
                print("Error: only one argument can have multiple values, "
                      f"not both \"{variadic}\" and \"{arg_name}\"")
                return -1
            variadic = arg_name
        else:
            kwargs[arg_name] = kwargs[arg_name][0]

    if variadic is None:
        t_start_ns = time_ns()
        ret = estimate_rates(
            speed=kwargs['speed'],
            tari=float(kwargs['tari']) * 1e-6,
            encoding=kwargs['encoding'],
            tid_word_size=kwargs['tid_word_size'],
            reader_offset=kwargs['reader_offset'],
            tag_offset=kwargs['tag_offset'],
            altitude=kwargs['altitude'],
            power=kwargs['power'],
            num_tags=kwargs['num_tags'],
            verbose=verbose,
        )
        t_end_ns = time_ns()
        print(tabulate([(key, value) for key, value in ret.items()],
                       tablefmt='pretty'))
        print(f"elapsed: {(t_end_ns - t_start_ns) / 1_000_000_000} sec.")

    else:
        # Какой-то параметр варьируется. Запускаем параллельно расчеты через
        # пул рабочих.

        # Убираем дубликаты и сортируем по возрастанию значения аргумента,
        # по которому варьируемся. Для того, чтобы убрать дубликаты,
        # строим множество из списка (в нем все значения будут уникальны),
        # затем строим сортированный список из множества.
        variadic_values = sorted(set(kwargs[variadic]))

        # Сначала построим массив из копий параметров. У каждого элемента
        # args список ключей в точности совпадает с тем, что мы передаем в
        # функцию estimate_rates (см. вызов выше).
        args_list = [{
            'speed': kwargs['speed'],
            'tari': float(kwargs['tari']) * 1e-6,
            'encoding': kwargs['encoding'],
            'tid_word_size': kwargs['tid_word_size'],
            'reader_offset': kwargs['reader_offset'],
            'tag_offset': kwargs['tag_offset'],
            'altitude': kwargs['altitude'],
            'power': kwargs['power'],
            'num_tags': kwargs['num_tags'],
            'verbose': False,
        } for _ in enumerate(variadic_values)]

        # Теперь заменим значения варьируемого аргумента, чтобы в каждом
        # элементе args хранилось только одно значение вместо всего набора.
        for i, value in enumerate(variadic_values):
            args_list[i][variadic] = value

        # Создаем пул рабочих (процессов), которые будут параллельно
        # выполняться.
        pool = Pool(kwargs.get('jobs', multiprocessing.cpu_count()))
        ret = pool.map(call_estimate_rates, args_list)

        # Результаты выводим в двух таблицах: таблице параметров и
        # таблице результатов. В последней - значение изменяющегося аргумента
        # и результаты, которые ему соответсвуют.
        params_names = list(var_arg_names) + ["encoding", "tari", "num_tags"]
        params_names.remove(variadic)

        print("\n# PARAMETERS:\n")
        print(tabulate([(name, kwargs[name]) for name in params_names],
                       tablefmt='pretty'))

        # Подготовим таблицу результатов.
        # Какие ключи нужны из словарей в списке ret (который вернул pool.map):
        ret_cols = (variadic, "read_tid_prob", "inventory_prob",
                    "rounds_per_tag")
        # Строки таблицы результатов:
        results_table = [[item[column] for column in ret_cols] for item in ret]
        print("\n# RESULTS:\n")
        print(tabulate(results_table, headers=ret_cols, tablefmt='pretty'))


# ----------------------------------------------------------------------------
def parse_tag_encoding(s):
    s = s.upper()
    if s in {'1', "FM0"}:
        return std.TagEncoding.FM0
    elif s in {'2', 'M2'}:
        return std.TagEncoding.M2
    elif s in {'4', 'M4'}:
        return std.TagEncoding.M4
    elif s in {'8', 'M8'}:
        return std.TagEncoding.M8
    else:
        raise ValueError('illegal encoding = {}'.format(s))


def estimate_rates(
        speed,
        tari,
        encoding,
        tid_word_size=None,
        reader_offset=None,
        tag_offset=None,
        altitude=None,
        power=None,
        num_tags=DEFAULT_NUM_TAGS,
        verbose=False,
):
    print(f"[+] Estimating speed = {speed} kmph, Tari = {tari*1e6:.2f} us, "
          f"M = {encoding}, tid_size = {tid_word_size} words, "
          f"reader_offset = {reader_offset} m, tag_offset = {tag_offset} m, "
          f"altitude = {altitude} m, power = {power} dBm, "
          f"num_tags = {num_tags}")

    try:
        encoding = parse_tag_encoding(encoding)
    except ValueError:
        pass
    result = models.simulate_tags(
        speed=(speed * KMPH_TO_MPS_MUL),
        encoding=encoding,
        tari=tari,
        log_level=sim.Logger.Level.WARNING,
        tid_word_size=tid_word_size,
        reader_offset=reader_offset,
        tag_offset=tag_offset,
        altitude=altitude,
        power=power,
        num_tags=num_tags,
        verbose=verbose,
    )
    result['encoding'] = encoding.name
    result['tari'] = f"{tari * 1e6:.2f}"
    result['speed'] = speed
    result['tid_word_size'] = tid_word_size
    result['reader_offset'] = reader_offset
    result['tag_offset'] = tag_offset
    result['altitude'] = altitude
    result['power'] = power
    return result


def call_estimate_rates(d):
    return estimate_rates(**d)


if __name__ == '__main__':
    cli()
