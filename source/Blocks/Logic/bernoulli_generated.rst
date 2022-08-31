bernoulli
=========

.. _bernoulli:

**Description**

Routes an incoming jolt to either of two outputs based on probability. With probability value set closer to 0 the jolt will more like go though output A, while if value will be set closer to 1 - though output B.

**Inputs, output and other parts**

*Probability* (stream input) Probability distribution value.

*Output A* (jolt output) Emits jolt value based on set probability.

*Output B* (jolt output) Emits jolt value based on set probability.

*Input* (jolt input) Receives jolt value which will be passed to either of the outputs.

**See also:**

:ref:`random <random>`, :ref:`sequence_random <sequence_random>`

