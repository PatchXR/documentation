compare
=======

.. _compare:

**Description**

Compares a jolt value with a stream value and outputs result of the comparison in the form of a boolean value (false - 0, true - 1).

**Inputs, output and other parts**

*Output* (jolt output) Emits boolean result (false - 0, true - 1) of jolt and stream values comparison on each received jolt.

*Compare with* (stream input) Sets the value that will be compared with the incoming value from the jolt input (without triggering the output).

*Input* (jolt input) Receives value which will be compared with value set in the stream input, triggers the comparison.

*Comparison operation* (interactive) Sets the type of the comparison operation.

*SetTypeREciever* 

**See also:**

:ref:`if_else <if_else>`

