import unittest as ut
import numpy as np
import time
import io
import sys

import pysim.simulator as sim


class EchoModel(ut.TestCase):
    #
    # First we define handlers for Client and Server:
    # run_echo_model() - initialize the model and start the execution
    # receive_request() - simulate a server receiving a message
    # receive_response() - simulate a client receiving a response
    # generate_request() - send a request to the server and schedule next ont
    #
    # We also define a class where the execution results will be stored.
    # It would be attached to the kernel, so methods could use it without
    # explicitly sending lots of parameters to each other.
    #
    class ModelContext:
        num_requests_received = 0
        num_responses_received = 0
        messages = None
        request_index = 0
        loop_messages = False
        call_stop_on_stop_string = False
        stop_string = None

        def reset(self):
            self.num_requests_received = 0
            self.num_responses_received = 0
            self.messages = None
            self.request_index = 0
            self.stop_string = None

    @staticmethod
    def run_echo_model(kernel, interval):
        kernel.print_line("MODEL STARTED")
        kernel.call(EchoModel.send_next_message, interval)

    @staticmethod
    def receive_request(kernel, message):
        kernel.print_line("--> server received '{}'".format(message))
        kernel.context.num_requests_received += 1
        kernel.call(EchoModel.receive_response, message)

    @staticmethod
    def receive_response(kernel, message):
        kernel.print_line("<-- client received '{}'".format(message))
        kernel.context.num_responses_received += 1

    @staticmethod
    def send_next_message(kernel, interval):
        ctx = kernel.context
        if ctx.request_index >= len(ctx.messages) > 0 and ctx.loop_messages:
            ctx.request_index = 0
        if ctx.request_index < len(ctx.messages):
            message = ctx.messages[ctx.request_index]
            if (kernel.context.call_stop_on_stop_string and
                    message == kernel.context.stop_string):
                kernel.stop()
            kernel.call(EchoModel.receive_request, message)
            dt = np.random.uniform(interval[0], interval[1])
            ctx.request_index += 1
            kernel.schedule(dt, EchoModel.send_next_message, interval)

    #
    # One day Alice wanted to check the simplest ever possible Echo client-
    # server model. She wants to use the simulator to evaluate it.
    #
    def test_echo_model(self):
        # Alice creates the kernel
        kernel = sim.Kernel()

        # Alice is making sure that kernel is in READY state, for any reason
        self.assertIs(kernel.state, kernel.State.READY)

        # Now Alice provides the simulator with her context by setting it up
        # in the kernel (all parts of the model will use it)
        kernel.context = self.ModelContext()
        kernel.context.messages = ['Hello', 'World', 'from', 'PyONS']

        # After everything was prepared, Alice launches the model
        sys.stdout = io.StringIO()
        kernel.run(self.run_echo_model, (5.0, 10.0))

        # WHen the model finished, Alice want to check that it is really in
        # the STOP state.
        self.assertIs(kernel.state, kernel.State.STOPPED)

        # Now Alice looks at the output and makes sure that all messages
        # expected to be print were really print by the kernel
        lines = sys.stdout.getvalue().split('\n')
        self.assertIn('MODEL STARTED', lines[0])
        line_index = 1
        for word in kernel.context.messages:
            self.assertIn("server received '{}'".format(word),
                          lines[line_index])
            self.assertIn("client received '{}'".format(word),
                          lines[line_index + 1])
            line_index += 2
        sys.stdout = sys.__stdout__

        # Afterwards, Alice checks that all messages were processed
        self.assertEqual(kernel.context.num_requests_received, 4)
        self.assertEqual(kernel.context.num_responses_received, 4)
        self.assertEqual(kernel.context.request_index, 4)

        # She also checks that kernel time was increased properly
        self.assertGreaterEqual(kernel.time, 20.0)
        self.assertLessEqual(kernel.time, 40.0)

        # After Alice ran her EchoModel, Bob wanted to use the same kernel
        # for the same task. Make sure he can not.
        with self.assertRaises(RuntimeError):
            kernel.run(self.run_echo_model, (1, 10))

    #
    # Here we check that the simulation may be stopped via the simulation
    # time limit
    #
    def test_model_can_be_stopped_via_simulation_time_limit(self):
        # Creating the kernel
        kernel = sim.Kernel()

        # Setting up the simulation context (an object used to synchronize
        # model parts)
        ctx = self.ModelContext()
        kernel.context = ctx
        ctx.messages = ['Hello', 'World', 'from', 'PyONS']
        ctx.loop_messages = True

        # Launch with max simulation time limit
        kernel.max_simulation_time = 21.0

        # Launching without stop conditions
        sys.stdout = io.StringIO()
        kernel.run(self.run_echo_model, (2.000, 2.001))
        sys.stdout = sys.__stdout__

        # Making sure that after execution kernel status is STOPPED
        self.assertIs(kernel.state, kernel.State.STOPPED)

        # Check that all messages were processed and simulation stopped in the
        # right place
        self.assertEqual(ctx.num_requests_received, 11)
        self.assertGreaterEqual(kernel.time, 20.0)
        self.assertLessEqual(kernel.time, 25)

    #
    # Now we want to check that simulation can be stopped via the real-time
    # limit.
    #
    def test_model_can_be_stopped_via_real_time_limit(self):
        # Creating the kernel
        kernel = sim.Kernel()

        # Setting up the simulation context (an object used to synchronize
        # model parts)
        ctx = self.ModelContext()
        kernel.context = ctx
        ctx.messages = ['Hello', 'World', 'from', 'PyONS']
        ctx.loop_messages = True

        # Launch with real time limit
        kernel.max_real_time = 0.01
        kernel.max_simulation_time = 1e5

        sys.stdout = io.StringIO()
        t0 = time.time()
        kernel.run(self.run_echo_model, (2.00, 2.001))
        time_elapsed = time.time() - t0
        sys.stdout = sys.__stdout__

        self.assertGreaterEqual(time_elapsed, 0.009)
        self.assertLessEqual(time_elapsed, 0.011)

    #
    # Finally we want to test whether a kernel can be stopped from inside
    # via stop() method call.
    #
    def test_model_can_be_stopped_via_stop_method_call(self):
        # Creating the kernel
        kernel = sim.Kernel()

        # Setting up the simulation context (an object used to synchronize
        # model parts)
        ctx = self.ModelContext()
        kernel.context = ctx
        ctx.messages = ['Hello', 'World', 'from', 'PyONS']
        ctx.call_stop_on_stop_string = True
        ctx.stop_string = 'from'

        # Running the simulation
        sys.stdout = io.StringIO()
        kernel.run(self.run_echo_model, (2, 10))
        sys.stdout = sys.__stdout__

        # Check that only the first two messages were send
        self.assertEqual(kernel.context.num_requests_received, 2)
