divide_jolt
===========

.. _divide_jolt:

**Description**

Divides incomming jolt number by the set stream value and outputs the result as jolt. Remember to avoid dividing by zero.

**Inputs, output and other parts**

*Calculate* (jolt input) Receives value which will be divided by the stream value, triggers the calculation.

*toggle* Toggle

*Result* (jolt output) Emits calculated value as jolt.

*Divider* (stream input) Sets the value by which the jolt input value will be divided (without triggering the output). Must not be zero.

**See also:**

:ref:`multiply_jolt <multiply_jolt>`, :ref:`add_jolt <add_jolt>`, :ref:`subtract_jolt <subtract_jolt>`, :ref:`divide <divide>`

