rhythm
======

.. _rhythm:

**Description**

Outputs events at musical intervals. The master beat_time is used as the default clock, unless something is attached to the clock stream input. Also outputs a normalized stream value indicating how far along we are in the period.

**Inputs, output and other parts**

*offset* (knob) How many beats the output event is offset in time compared to the input clock.

*period* (knob) How many subdivisions there are pr. period. E.g. a value of 3 will cause an event to fire every third subdivision.

*subdivision* (knob) How many times to divide the beat when counting a period. E.g. a value of 2 will count two times every beat.

*clock* (stream input) Usually an increasing counter, counting the beats that determine when the period_begin should fire.

*period_begin* (event output) Emits an event whenever a new period starts.

*Sphere* 

