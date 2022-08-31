interaction_box
===============

.. _interaction_box:

**Description**

A highly flexible interface for building different kinds of interactions.

A box-shaped area that can be divided into segments along each axis. Provides a variety of different jolt outputs for each controller inside the interaction area, and lets you control the controller's haptics.

**Inputs, output and other parts**

*Resize handle* (interactive) Drag to resize the interaction area.

*Right X* (jolt output) Emits the X position of the right controller.

*Right Y* (jolt output) Emits the Y position of the right controller.

*Right Z* (jolt output) Emits the Z position of the right controller.

*Right present* (jolt output) Emits a 1 when the right controller enters the area and 0 when it leaves.

*Right trigger* (jolt output) Emits a value between 0 and 1 depending on how much the right controller trigger button is pressed. If 'Continous trigger' is turned off via the inspector it sends out 1/0 when the trigger is pressed/released.

*Left X* (jolt output) Emits the X position of the left controller.

*Left Y* (jolt output) Emits the Y position of the left controller.

*Left Z* (jolt output) Emits the Z position of the left controller.

*Left present* (jolt output) Emits a 1 when the left controller enters the area and 0 when it leaves.

*Left trigger* (jolt output) Emits a value between 0 and 1 depending on how much the left controller trigger button is pressed. If 'Continous trigger' is turned off via the inspector it sends out 1/0 when the trigger is pressed/released.

*Segments X* (knob) Controls the number of segments in the X direction.

*Segments X* (jolt input) Controls the number of segments in the X direction.

*Segments Y* (knob) Controls the number of segments in the Y direction.

*Segments Y* (jolt input) Controls the number of segments in the Y direction.

*Segments Z* (knob) Controls the number of segments in the Z direction.

*Segments Z* (jolt input) Controls the number of segments in the Z direction.

*Haptics left* (stream input) Controls the vibration strength of the left controller.

*Haptics right* (stream input) Controls the vibration strength of the right controller:

