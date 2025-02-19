cyclecounter
============

.. _cyclecounter:

**Description**

Counts the number of received jolts in a looping manner.



**Inputs, output and other parts**

*cyclecounter* 

*Cycle size* (stream input) Sets the value at which the counter will reset and start counting from zero again.

*Output* (jolt output) Emits the current count value as a jolt.

*Increment* (jolt input) Counter increment trigger. Each received jolt triggers the count to increase by one.

*Set* (jolt input) Sets current count value and triggers the output.

**See also:**

:ref:`counter <counter>`

