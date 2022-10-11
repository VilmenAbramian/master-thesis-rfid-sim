import unittest
import pysim.simulator as sim
import sys
import io


class TestEventQueue(unittest.TestCase):

    def test_queue_is_empty_when_created(self):
        q = sim.EventQueue()
        self.assertEqual(len(q), 0)
        self.assertTrue(q.empty)

    def test_single_push_and_pop(self):
        # 1) Push a single item (string), store the ID and tests
        # that queue length is 1
        q = sim.EventQueue()
        push_id = q.push(1, "tests")

        self.assertEqual(len(q), 1)
        self.assertFalse(q.empty)

        # 2) Pop a value and examine the returned time, ID nad value;
        # then also check that queue is empty after pop()
        t, pop_id, value = q.pop()

        self.assertEqual(value, "tests")
        self.assertAlmostEqual(t, 1.0)
        self.assertEqual(push_id, pop_id)
        self.assertTrue(q.empty)

    def test_pushed_events_popped_in_right_order(self):
        q = sim.EventQueue()
        q.push(2.0, "msg-1")
        q.push(1.0, "msg-2")
        q.push(1.5, "msg-3")

        self.assertEqual(len(q), 3)

        t, msg_id, msg = q.pop()
        self.assertEqual(msg, "msg-2")

        t, msg_id, msg = q.pop()
        self.assertEqual(msg, "msg-3")

        t, msg_id, msg = q.pop()
        self.assertEqual(msg, "msg-1")

        self.assertEqual(len(q), 0)

    def test_pop_from_empty_queue_cases_error(self):
        q = sim.EventQueue()
        with self.assertRaises(IndexError):
            q.pop()

    def test_cancel_even_from_the_head(self):
        q = sim.EventQueue()
        id1 = q.push(2.0, "msg-1")
        id2 = q.push(1.0, "msg-2")
        id3 = q.push(0.0, "msg-3")
        q.cancel(id3)  # removing the first event at t=0.0
        self.assertEqual(q.ids(), [id2, id1])


class TestKernel(unittest.TestCase):
    def test_kernel_creation(self):
        kernel = sim.Kernel()
        self.assertEqual(kernel.state, kernel.State.READY)

    # noinspection PyPropertyAccess
    def test_state_can_not_be_changed_outside_kernel(self):
        kernel = sim.Kernel()
        with self.assertRaises(AttributeError):
            kernel.state = kernel.State.STOPPED
        self.assertEqual(kernel.state, kernel.State.READY)

    def test_kernel_context_setter_and_getter(self):
        kernel = sim.Kernel()
        self.assertTrue(hasattr(kernel, 'context'))
        ctx = {'x': 10}
        kernel.context = ctx
        self.assertIs(kernel.context, ctx)

    def test_kernel_provide_run_method(self):
        kernel = sim.Kernel()
        kernel.context = {'x': 0}

        # noinspection PyShadowingNames
        def increment(kernel):
            kernel.context['x'] += 1
            self.assertEqual(kernel.state, kernel.State.RUNNING)

        kernel.run(increment)
        self.assertEqual(kernel.context['x'], 1)

    def test_kernel_manage_simulation_time(self):
        #
        # 1) Create a kernel with context dictionary {'x': 0}
        # 2) Define a model:
        #   init --10s--> increment x --10s--> ... --10s--> increment x END.
        # 3) make sure that time is equal to number of increments * 10
        #
        kernel = sim.Kernel()
        kernel.context = {'x': 0}
        self.assertAlmostEqual(kernel.time, 0.0)

        # noinspection PyShadowingNames
        def increment(kernel, rest):
            kernel.context['x'] += 1
            if rest > 1:
                kernel.schedule(10.0, increment, rest - 1)

        # noinspection PyShadowingNames
        def start_simulation(kernel, num_increments):
            kernel.schedule(10.0, increment, num_increments)

        num_increments = 5
        kernel.run(start_simulation, num_increments)
        self.assertEqual(kernel.context['x'], num_increments)
        self.assertAlmostEqual(kernel.time, 10.0 * num_increments)

    # noinspection PyPropertyAccess
    def test_time_cant_be_changed_outside_kernel(self):
        kernel = sim.Kernel()
        with self.assertRaises(AttributeError):
            kernel.time = 20.0

    def test_kernel_provides_call_method_keeping_time_the_same(self):
        kern = sim.Kernel()
        kern.context = {'x': 0}

        def set_x(kernel, value, arg_name=None):
            kernel.context[arg_name] = value

        def start_simulation(kernel, value, arg_name=None):
            kernel.call(set_x, value, arg_name=arg_name)

        kern.run(start_simulation, 10, arg_name='x')
        self.assertEqual(kern.context['x'], 10)

    def test_kernel_provide_cancel_method(self):
        kernel = sim.Kernel()
        kernel.context = {'x': 0}

        def set_x(k, value, arg_name=None):
            k.context[arg_name] = value

        def start_simulation(k, value, arg_name=None):
            event_id = k.call(set_x, value, arg_name=arg_name)
            k.cancel(event_id)
            event_id = k.schedule(1.0, set_x, value + 10, arg_name=arg_name)
            k.cancel(event_id)

        kernel.run(start_simulation, 10, arg_name='x')
        self.assertEqual(kernel.context['x'], 0)

    def test_kernel_provides_print_method(self):
        kernel = sim.Kernel()
        self.assertTrue(hasattr(kernel, 'print'))
        sys.stdout = io.StringIO()
        kernel.print_line("Hello", "New")
        kernel.print_line("World")
        value = sys.stdout.getvalue()
        lines = value.split('\n')
        self.assertIn('Hello', lines[0])
        self.assertIn('New', lines[0])
        self.assertIn('World', lines[1])
        sys.stdout = sys.__stdout__
