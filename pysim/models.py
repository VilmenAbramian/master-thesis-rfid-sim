from dataclasses import dataclass
from typing import Callable
import numpy as np
from tabulate import tabulate

import pysim.handlers as handlers
from pysim.objects import Reader, Model, Antenna, Generator, Medium
import pysim.epcstd as std
import pysim.simulator as sim


KMPH_TO_MPS_MUL = 1.0 / 3.6


@dataclass
class Settings:
    """
    Настройки модели.

    При вызове модели simulate_tags() можно передать готовый объект
    Settings() (например, заполненный в результате чтения JSON или строки
    из CSV-файла). По-умолчанию, используются значения параметров, которые
    настроены тут.

    Также при вызове simulate_tags() можно переопределить некоторые параметры.
    В этом случае у аргументов simulate_tags() приоритет над значениями,
    которые хранятся в объекте класса Settings.
    """
    # --- Настройки кодировки команд считывателя (PIE) ---
    delim: float = 12.5e-6  # длительность символа-разделителя (константа), сек.
    tari: float = 6.25e-6  # длительность Tari, сек. (6.25, 12.5, 18.75, 25 мкс)
    rtcal_tari_mul: float = 3.0  # множитель RTcal, см. get_rtcal()
    trcal_rtcal_mul: float = 2.5  # множитель TRcal, см. get_trcal()
    temp: std.TempRange = std.TempRange.NOMINAL  # температурный диапазон

    @property
    def rtcal(self):
        return self.get_rtcal(self.tari)

    def get_rtcal(self, tari):
        return tari * self.rtcal_tari_mul

    @property
    def trcal(self):
        return self.get_trcal(self.rtcal)

    def get_trcal(self, rtcal):
        return rtcal * self.trcal_rtcal_mul


    # --- Геометрия и траектория движения ---
    speed: float = 10 * KMPH_TO_MPS_MUL       # скорость метки, м/с
    initial_distance_to_reader: float = 10.0  # как далеко метка от ридера, м
    travel_distance: float = 20.0  # как далеко метка летит до уничтожения, м

    reader_antenna_x: float = 5.0  # расстояние от ридера до стены по оси OX, м
    reader_antenna_z: float = 5.0  # высота дрона (ридера) по оси OZ, м
    tag_antenna_x: float = 5.0     # расстояние от метки до стены по оси OX, м
    tag_antenna_z: float = 0.0     # высота антенны метки по оси OZ, м

    # Направление, куда смотрит антенна ридера:
    reader_antenna_direction: np.ndarray = np.asarray([0, 0, -1])

    # Направление, куда смотрит антенна метки:
    tag_antenna_direction: np.ndarray = np.asarray([0, 0, 1])

    # Как часто обновлять координаты (модельные часы):
    update_interval: float = 0.01

    # --- Энергетические параметры ---
    reader_power: float = 31.5  # мощность трансмиттера считывателя, дБм
    reader_antenna_gain: float = 6.0  # усиление антенны считывателя, дБ
    reader_cable_loss: float = -2.0   # потери в антенном кабеле ридера, дБ
    tag_antenna_gain: float = 3.0     # усиление антенны метки, дБ
    tag_modulation_loss: float = -12.0  # потери на модуляции на метке, дБ
    tag_sensitivity: float = -18.0  # чувствительность (чтения) метки, дБ

    # Шумы внутри считывателя от трансмиттера постоянного сигнала (то, что
    # просачивается на ресивер) и от источника питания, дБ.
    reader_noise: float = -80.0

    # --- Настройки модели распространения сигнала ---
    ber_distribution: str = 'rayleigh'  # модель BER: 'rayleigh' or 'awgn'
    frequency: float = 860 * 1e6   # несущая частота ридера, МГц
    permittivity: float = 15.0  # диэлектрическая проницаемость стены
    conductivity: float = 0.03  # проводимость материала стены
    polarization_loss: float = -3.0  # дБ

    # Способ расчета коэффициента отражения ('reflection', 'const')
    # - Если задано значение 'reflection', то коэффициент отражения будет
    #   рассчитываться в зависимости от свойств материала, угла падения и
    #   поляризации сигнала;
    # - Если задано значение 'const', то коэффициент равен единице.
    ground_reflection_type: str = 'reflection'
    use_doppler: bool = True  # учитывать ли эффект Доплера

    # --- Управление питанием считывателя ---
    reader_switch_power: bool = True  # должен ли ридер периодически отключаться
    reader_power_on_duration: float = 2.0  # сколько считыватель включен, сек.
    reader_power_off_duration: float = 0.1  # сколько считыватель выключен, сек.

    # Интервал переключения антенн считывателя.
    # В текущей модели не используется, так как у ридера только одна антенна.
    reader_antenna_switching_interval: float = 10

    # Следует ли начинать работу всегда с антенны под номером 1.
    # В текущей модели не используется, так как у ридера только одна антенна.
    reader_always_start_with_first_antenna: bool = False

    # --- Настройки раунда инвентаризации ---
    read_tid_bank: bool = True  # нужно ли читать банк данных

    # Сколько машинных слов данных запрашивает ридер.
    # Считаем, что в метке размер банка данных всегда не меньше, чем число
    # запрашиваемых слов.
    tid_word_size: int = 8

    q: int = 2  # значение параметра Q
    encoding: std.TagEncoding = std.TagEncoding.M4  # способ кодирования ответов
    dr: std.DivideRatio = std.DivideRatio.DR_8  # коэффициент DR (8 или 64/3)
    sel: std.SelFlag = std.SelFlag.ALL  # флаг Sel (не используется в модели)
    session: std.Session = std.Session.S0  # номер сессии, в которой идет опрос
    trext: bool = True  # использовать ли в ответах расширенную преамбулу

    # Значение поля Target команды Query, то есть флаг сессии, по которому
    # идет опрос меток. Ответ будут передавать только те метки, которые хранят
    # флаг сессии, совпадающий с target. После каждого ответа на команду ACK
    # метка инвертирует свой флаг сессии с A на B и наоборот.
    # Если метка передала свой EPCID в ответ на ACK, и в следующем раунде
    # ридер запрашивает тот же флаг Target, метка не будет участвовать в раунде.
    #
    # Параметр target используется, если target_strategy = "const".
    # Если target_strategy = "switch", ридер будет чередовать значения Target
    # и менять его с A на B и обратно каждые rounds_per_target раундов.
    target: std.InventoryFlag = std.InventoryFlag.A

    # Стратегия выбора флага сессии. Возможные значения 'switch' и 'const'.
    # - 'const': опрос всегда ведется по значению параметра target
    # - 'switch': ридер чередует опрос по флагу A и B, и меняет значение
    #   каждые rounds_per_target раундов.
    target_strategy: str = "switch"  # Опрашиваем поочередно по Target=A,B

    # Если target_strategy = "swtich", то это поле показывает, как часто
    # ридер меняет флаг опроса (Target).
    rounds_per_target: int = 1

    # --- Настройки памяти метки ---
    epc_bitlen: int = 96  # Длина идентификатора EPCID в битах

    @property
    def tid_bitlen(self):
        # Длина данных в битах, хранящиеся на метке. Вычисляем, так, чтобы
        # это число было не меньше, чем запрашивает ридер в команде Read.
        return self.get_tid_bitlen(self.tid_word_size)

    def get_tid_bitlen(self, tid_word_size):
        return tid_word_size * 16

    # Следующие поля определяют, через сколько времени без питания метка
    # сбросит в A хранящийся флаг сессии. Для сессии S0 такого параметра нет,
    # так как по стандарту EPC Class 1 Gen.2 метка должна сбросить в A
    # флаг сессии S0 сразу после потери питания.

    s1_persistence: float = 2.0  # сколько хранить флаг в сессии S1, сек.
    s2_persistence: float = 2.0  # сколько хранить флаг в сессии S2, сек.
    s3_persistence: float = 2.0  # сколько хранить флаг в сессии S3, сек.

    # --- Настройки генератора ---

    # Функция и ее параметры, возвращающая интервал, через который появится
    # новая метка. Если параметров у функции нет, то это просто кортеж с одним
    # элементом - функцией без аргументов.
    # Если у функции есть N обязательных параметров, то их значения должны
    # быть указаны в 1, 2, ..., N элементах кортежа.
    # Например, если в качестве функции используется `numpy.random.exponential`,
    # то в качестве аргумента можно передать среднее: (exponential, 42.0).
    generation_interval: tuple = (lambda: 1.0, )

    num_tags: int = 10  # сколько меток нужно сгенерировать

    # --- Настройки статистики ---
    # Сохранять ли данные о мощностях сигналов
    collect_power_statistics: bool = False

    def get_power_control_mode(self, reader_switch_power=None):
        x = reader_switch_power if reader_switch_power is not None \
            else self.reader_switch_power
        return Reader.PowerControlMode.PERIODIC if x else \
            Reader.PowerControlMode.ALWAYS_ON


def simulate_tags(settings=None, verbose=False, **kwargs):
    """Run simulation.

    Possible kwargs (if value not given, use from settings):
    - speed: float
    - encoding: int
    - tari: float
    - tid_word_size: int
    - reader_offset: float
    - tag_offset: float
    - altitude: float
    - power: float
    - num_tags: int
    - sim_time_limit: float
    - real_time_limit: float
    - log_level: sim.Logger.Level
    """
    if settings is None:
        settings = Settings()

    # 0) Building the model

    model = Model()
    model.max_tags_num = kwargs.get('num_tags', settings.num_tags)
    model.update_interval = settings.update_interval
    model.statistics.use_power_statistics = settings.collect_power_statistics

    # 1) Building the reader

    reader = Reader()
    model.reader = reader

    reader.tari = kwargs.get('tari', settings.tari)
    reader.tag_encoding = kwargs.get('encoding', settings.encoding)
    reader.q = settings.q
    reader.rtcal = settings.get_rtcal(reader.tari)
    reader.trcal = settings.get_trcal(reader.rtcal)
    reader.delim = settings.delim
    reader.temp = settings.temp
    reader.session = settings.session
    reader.target = settings.target
    reader.sel = settings.sel
    reader.dr = settings.dr
    reader.trext = settings.trext
    reader.target_strategy = settings.target_strategy
    reader.rounds_per_target = settings.rounds_per_target
    reader.power_control_mode = settings.get_power_control_mode()
    reader.max_power = kwargs.get('power', settings.reader_power)
    reader.power_on_duration = settings.reader_power_on_duration
    reader.power_off_duration = settings.reader_power_off_duration
    reader.noise = settings.reader_noise
    reader.read_tid_words_num = \
        kwargs.get('tid_word_size', settings.tid_word_size)
    reader.read_tid_bank = \
        settings.read_tid_bank if reader.read_tid_words_num > 0 else False
    reader.always_start_with_first_antenna = \
        settings.reader_always_start_with_first_antenna
    reader.antenna_switch_interval = settings.reader_antenna_switching_interval

    reader_antenna_x = kwargs.get('reader_offset', settings.reader_antenna_x)
    reader_antenna_z = kwargs.get('altitude', settings.reader_antenna_z)
    tag_antenna_x = kwargs.get('tag_offset', settings.tag_antenna_x)
    tag_antenna_z = settings.tag_antenna_z

    # 2) Attaching antennas to reader
    ant = Antenna()
    ant.pos = np.asarray([reader_antenna_x, 0, reader_antenna_z])
    ant.direction_theta = settings.reader_antenna_direction
    ant.gain = settings.reader_antenna_gain
    ant.cable_loss = settings.reader_cable_loss
    reader.attach_antenna(ant)

    # 3) Setting up medium
    medium = Medium()
    model.medium = medium

    medium.ber_distribution = settings.ber_distribution
    medium.ground_reflection_type = settings.ground_reflection_type
    medium.frequency = settings.frequency
    medium.permittivity = settings.permittivity
    medium.conductivity = settings.conductivity
    medium.polarization_loss = settings.polarization_loss
    medium.use_doppler = settings.use_doppler

    # 4) Generator settings
    generator = Generator()
    model.generators.append(generator)
    generator.pos0 = np.asarray([
        tag_antenna_x,
        -settings.initial_distance_to_reader,
        tag_antenna_z
    ])
    generator.velocity = kwargs.get('speed', settings.speed)
    generator.direction = np.asarray([0, 1, 0])
    generator.tag_antenna_direction = settings.tag_antenna_direction
    generator.travel_distance = settings.travel_distance

    generator.epc_prefix = 'A' * 4
    generator.tid_prefix = 'A' * 4
    generator.epc_bitlen = settings.epc_bitlen
    generator.tid_bitlen = settings.get_tid_bitlen(reader.read_tid_words_num)

    generator.max_tags_generated = model.max_tags_num
    generator.antenna_gain = settings.tag_antenna_gain
    generator.modulation_loss = settings.tag_modulation_loss
    generator.sensitivity = settings.tag_sensitivity

    generator.set_interval(
        settings.generation_interval[0],
        *settings.generation_interval[1:])

    # 5) Launching simulation
    kernel = sim.Kernel()

    kernel.max_simulation_time = kwargs.get('sim_time_limit', None)
    kernel.max_real_time = kwargs.get('real_time_limit', None)
    kernel.context = model
    kernel.logger.level = kwargs.get('log_level', sim.Logger.Level.WARNING)

    if verbose:
        print("# MODEL SETTINGS:")
        print_model_settings(model, kernel)

    kernel.run(handlers.start_simulation)

    return {
        'rounds_per_tag': model.statistics.average_rounds_per_tag(),
        'inventory_prob': model.statistics.inventory_probability(),
        'read_tid_prob': model.statistics.read_tid_probability()
    }


def print_model_settings(model: Model, kernel: sim.Kernel):
    """Вспомогательный метод для вывода на печать параметров настроенной
       модели.
    """
    reader = model.reader
    medium = model.medium
    generator = model.generators[0]

    us = lambda sec: f"{sec * 1e6:.2f} us"

    rows = [
        # --- Model ----
        ("model", "max_tags_num", model.max_tags_num),
        ("model", "update_interval", model.update_interval),
        ("model", "statistics.use_power_statistics",
         model.statistics.use_power_statistics),
        # --- Reader ---
        ("reader", "tari", us(reader.tari)),
        ("reader", "tag_encoding", reader.tag_encoding),
        ("reader", "q", reader.q),
        ("reader", "rtcal", us(reader.rtcal)),
        ("reader", "trcal", us(reader.trcal)),
        ("reader", "delim", us(reader.delim)),
        ("reader", "temp", reader.temp),
        ("reader", "session", reader.session),
        ("reader", "target", reader.target),
        ("reader", "sel", reader.sel),
        ("reader", "dr", reader.dr),
        ("reader", "trext", reader.trext),
        ("reader", "target_strategy", reader.target_strategy),
        ("reader", "rounds_per_target", reader.rounds_per_target),
        ("reader", "power_control_mode", reader.power_control_mode),
        ("reader", "max_power", reader.max_power),
        ("reader", "power_on_duration", reader.power_on_duration),
        ("reader", "power_off_duration", reader.power_off_duration),
        ("reader", "noise", reader.noise),
        ("reader", "read_tid_words_num", reader.read_tid_words_num),
        ("reader", "read_tid_bank", reader.read_tid_bank),
        ("reader", "always_start_with_first_antenna",
         reader.always_start_with_first_antenna),
        ("reader", "antenna_switch_interval", reader.antenna_switch_interval),
        ("reader antenna", "pos", reader.antenna.pos),
        ("reader antenna", "direction_theta", reader.antenna.direction_theta),
        ("reader antenna", "gain", reader.antenna.gain),
        ("reader antenna", "cable_loss", reader.antenna.cable_loss),
        # --- Medium ---
        ("medium", "ber_distribution", medium.ber_distribution),
        ("medium", "ground_reflection_type", medium.ground_reflection_type),
        ("medium", "frequency", medium.frequency),
        ("medium", "permittivity", medium.permittivity),
        ("medium", "conductivity", medium.conductivity),
        ("medium", "polarization_loss", medium.polarization_loss),
        ("medium", "use_doppler", medium.use_doppler),
        # --- Generator and tag ---
        ("tag", "pos0", generator.pos0),
        ("tag", "velocity", generator.velocity),
        ("tag", "direction", generator.direction),
        ("tag", "antenna_direction", generator.tag_antenna_direction),
        ("tag", "travel_distance", generator.travel_distance),
        ("tag", "epc_bitlen", generator.epc_bitlen),
        ("tag", "tid_bitlen", generator.tid_bitlen),
        ("tag", "antenna_gain", generator.antenna_gain),
        ("tag", "modulation_loss", generator.modulation_loss),
        ("tag", "sensitivity", generator.sensitivity),
        ("generator", "num_tags", generator.max_tags_generated),
        # --- Kernel ---
        ("kernel", "max_simulation_time", kernel.max_simulation_time),
        ("kernel", "max_real_time", kernel.max_real_time),
        ("kernel", "logger_level", kernel.logger.level),
    ]
    print(tabulate(rows))
