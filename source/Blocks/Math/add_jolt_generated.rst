add_jolt
========

.. _add_jolt:

**Description**

Adds number from stream input to the jolt input and outputs the sum as jolt.

**Inputs, output and other parts**

*Add* (stream input) Sets the value that will be added to the incoming value from the jolt input (without triggering the output).

*Result* (jolt output) Emits sum of jolt and stream values on each received jolt.

*Calculate* (jolt input) Receives value to which the value set in the stream input will be added, triggers the calculation.

**See also:**

:ref:`subtract_jolt <subtract_jolt>`, :ref:`multiply_jolt <multiply_jolt>`, :ref:`divide_jolt <divide_jolt>`, :ref:`add <add>`

