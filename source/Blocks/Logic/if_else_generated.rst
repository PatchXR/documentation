if_else
=======

.. _if_else:

**Description**

Compares a jolt value with a stream value and outputs a jolt value through one of the two outputs, depending on whether the condition is met or not

**Inputs, output and other parts**

*SetTypeReciever* 

*Input* (jolt input) Receives value which will be compared with value set in the stream input, triggers the comparison.

*Comparison operation* (interactive) Sets the type of the comparison operation.

*Compare with* (stream input) Sets the value that will be compared with the incoming value from the jolt input (without triggering the output).

* Output if* (jolt output) Emits received jolt value if the condition is met.

* Output else* (jolt output) Emits received jolt value if the condition is not met.

**See also:**

:ref:`compare <compare>`

