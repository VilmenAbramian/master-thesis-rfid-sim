import itertools
import heapq
import enum
import time


class Singleton(type):
    """
    Simple singleton implementation. To use it, set ``Singleton`` as a
    metaclass of the class.
    """
    instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.instance


class EventQueue:
    """
    Simple event queue
    """
    def __init__(self):
        self._next_id = itertools.count()
        self._heap = []
        self._dict = {}

    def push(self, t, item):
        event_id = next(self._next_id)
        record = [t, event_id, item]
        heapq.heappush(self._heap, record)
        self._dict[event_id] = record
        return event_id

    def pop(self):
        if self.empty:
            raise IndexError("pop from empty queue")
        t_fire, event_id, item = heapq.heappop(self._heap)
        while item is None:
            t_fire, event_id, item = heapq.heappop(self._heap)
        self._dict.pop(event_id)  # remove the record from the dictionary
        return t_fire, event_id, item

    @property
    def empty(self):
        return len(self._dict) == 0

    def cancel(self, event_id):
        if event_id is not None and event_id in self._dict:
            # record is [t, event_id, item]
            record = self._dict.pop(event_id)
            record[-1] = None  # setting record.item = None

    def __len__(self):
        return len(self._dict)

    def clear(self):
        self._dict.clear()
        self._heap.clear()

    def as_list(self):
        l = list(self._heap)
        l.sort()
        return l

    def ids(self):
        return [event_id for t, event_id, msg in self.as_list() if event_id
                in self._dict]


class Logger:
    class Level(enum.Enum):
        TRACE = 0
        DEBUG = 1
        INFO = 2
        WARNING = 3
        ERROR = 4

    def __init__(self, kernel, level=None):
        self._kernel = kernel
        self.level = level if level is not None else Logger.Level.DEBUG

    @property
    def kernel(self):
        return self._kernel

    def write(self, level, *args):
        if level.value >= self.level.value:
            print("{:016.9f} [{:7s}] {}".format(
                self.kernel.time, level.name,
                " ".join(str(arg) for arg in args)))

    def trace(self, *args):
        self.write(Logger.Level.TRACE, *args)

    def debug(self, *args):
        self.write(Logger.Level.DEBUG, *args)

    def info(self, *args):
        self.write(Logger.Level.INFO, *args)

    def warning(self, *args):
        self.write(Logger.Level.WARNING, *args)

    def error(self, *args):
        self.write(Logger.Level.ERROR, *args)


class Kernel:
    """
    Simulation kernel. The generic workflow looks like:

    1) create the kernel:

        `kernel = Kernel()`

    2) set the simulation context (an object used by the model parts to store
    and synchronize data), say `ModelContext` or anything user-provided:

        `kernel.context = ModelContext()`

    3) if the simulation should be limited in simulation or real-time, set
    these limitations given in seconds (one or both of the following):

        `kernel.max_simulation_time = 100.0`
        `kernel.max_real_time = 10.0`

    4) start the execution:

        `kernel.run(user_provided_function, x, y, arg='value')`

    Any function expecting kernel as the first argument may be called by
    `run()` method. Arguments are provided after the function (x, y and arg
    in this example)

    To stop the simulation any handler can call `kernel.stop()`.

    Methods `schedule()` and `call()` are used to transfer control to another
    handler. The control will be transferred when current handler execution
     finishes and the target handler will be in the head of the event queue.
    """
    class State(enum.Enum):
        READY = 0
        STOPPED = 1
        RUNNING = 2

    def __init__(self):
        self.context = None
        self.max_simulation_time = None
        self.max_real_time = None

        self._state = self.State.READY
        self._queue = EventQueue()
        self._sim_time = 0.0
        self._user_stop = False

        self._t_start = None
        self._t_stop = None
        self._num_events_served = 0
        self._logger = Logger(self)

    @property
    def state(self):
        return self._state

    @property
    def time(self):
        return self._sim_time

    @property
    def logger(self):
        return self._logger

    def run(self, f, *args, **kwargs):
        if self.state is not self.State.READY:
            raise RuntimeError('kernel already running')
        self._state = self.State.RUNNING
        self._num_events_served = 0
        self._t_start = time.time()
        self._queue.push(0.0, (f, args, kwargs))

        while not self._queue.empty and not self._test_stop_conditions():
            t, event_id, item = self._queue.pop()
            self._sim_time = t
            f, args, kwargs = item
            f(self, *args, **kwargs)
            self._num_events_served += 1

        self._state = self.State.STOPPED
        self._t_stop = time.time()

    def schedule(self, dt, f, *args, **kwargs):
        if dt is not None:
            return self._queue.push(self._sim_time + dt, (f, args, kwargs))
        else:
            return None

    def call(self, f, *args, **kwargs):
        return self._queue.push(self._sim_time, (f, args, kwargs))

    def cancel(self, event_id):
        self._queue.cancel(event_id)

    def print_line(self, *args):
        print("{:016.9f} {}".format(
            self.time, " ".join(str(arg) for arg in args)))

    def stop(self):
        self._user_stop = True

    @property
    def real_time_elapsed(self):
        if self.state is self.State.READY:
            return 0.0
        elif self.state is self.State.RUNNING:
            return time.time() - self._t_start
        else:
            return self._t_stop - self._t_start

    @property
    def queue_size(self):
        return len(self._queue)

    @property
    def num_events_served(self):
        return self.num_events_served

    def _test_stop_conditions(self):
        return ((self.max_simulation_time is not None and
                 self.time > self.max_simulation_time) or
                (self.max_real_time is not None and
                 self.real_time_elapsed > self.max_real_time) or
                self._user_stop)
