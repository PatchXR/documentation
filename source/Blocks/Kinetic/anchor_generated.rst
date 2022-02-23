anchor
======

.. _anchor:

**Description**

Sets player position and rotation to the position and rotation of the anchor block when triggered. Sending a zero will transport the player instantly, while sending any positive number will transport the player gradually over time - time (in ms) is set by received value.

**Inputs, output and other parts**

*Direction* (pointer) Sets the direction of the player's view accourding to the direction of the elongated tube. Once the action is completed, the player's head will end up where the block is located.

*Teleport* (jolt input) Sets and triggers the time it takes for the player to reach the new position and rotation in milliseconds.

