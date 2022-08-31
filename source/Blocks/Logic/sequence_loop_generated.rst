sequence_loop
=============

.. _sequence_loop:

**Description**

Routes an incoming jolt to one of many outputs in a looping manner.

**Inputs, output and other parts**

*Input* (jolt input) Receives the jolt which will be routed to the currently selected output and proceed to the next output.

*Pull* (interactive) Pull to set the number of output gates.

*Select output* (jolt input) Select which output should be used next time an input is received.

*Output* (jolt output) Emits the routed jolt value. One of the possible outputs the input may be routed to.

**See also:**

:ref:`sequence <sequence>`, :ref:`sequence_random <sequence_random>`

