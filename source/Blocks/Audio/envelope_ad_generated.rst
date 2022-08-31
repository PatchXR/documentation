envelope_ad
===========

.. _envelope_ad:

**Description**

A two-stage, Attack-Decay envelope with linear response. Attack begins from 0 and rises to 1. Decay begins from 1 and falls to 0. Connect the 'End of attack' output to the 'Decay trigger' input to trigger the decay stage right after attack finishes.

**Inputs, output and other parts**

*Attack time* (stream input) Attack stage time (in seconds).

*Decay time* (stream input) Decay stage time (in seconds).

*End of attack* (jolt output) Emits jolt once the attack stage finishes. Connect to the 'Decay trigger' input to trigger the decay stage right after attack finishes.

*End of decay* (jolt output) Emits jolt once the decay stage finishes.

*Attack trigger* (jolt input) Triggers the attack stage of the envelope.

*Decay trigger* (jolt input) Triggers the decay stage of the envelope.

**See also:**

:ref:`decay <decay>`

