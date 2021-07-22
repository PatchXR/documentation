delay_jolt
==========

.. _delay_jolt:

**Description**

Delay a jolt by some amount of time.

**Inputs, output and other parts**

*input* (jolt input) The jolt to delay.

*speed_of_time* (stream input) A multiplier for the delay constant.

*delay_time* (stream input) How much to delay the jolt.

*output* (jolt output) Sends out the same jolt as received through 'input', but delayed by the time set via the 'delay_time' stream input.

