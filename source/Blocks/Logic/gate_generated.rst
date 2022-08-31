gate
====

.. _gate:

**Description**

Allows or disallows jolts to pass based on the set stream value.

**Inputs, output and other parts**

*Output* (jolt output) Emits the received jolt value as a jolt if gate value is equal or greater than 0.5

*Gate* (stream input) Sets the gate state. Values equal or greater than 0.5 will set gate state to 'open'.

*Input* (jolt input) Receives jolt value which will be passed to the output if gate value is equal or greater than 0.5

**See also:**

:ref:`sequence <sequence>`

