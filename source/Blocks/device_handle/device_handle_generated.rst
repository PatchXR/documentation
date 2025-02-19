device_handle
=============

.. _device_handle:

**Description**

Allows you to build devices that will replace your controllers when grabbed. Must be put inside a group or device to work properly.

When you grab a group or device with a device_handle inside your controller will be hidden, and the entire device will be reoriented to replace your controller.

**Inputs, output and other parts**

*Grip* (jolt output) Sends out a 1 when you grab the handle and 0 when you let go.

*Trigger* (jolt output) Sends out a 1 when you press the trigger while grabbing the handle and 0 when you release. Continuous output can be enabled via the inspector.

*Hand side* (jolt output) Sends 0 for right, 1 for left, when the handle is grabbed.

*Button A Pressed* Send 1 when A button is pressed, 0 when released.

*Button B Pressed* Send 1 when B button is pressed, 0 when released.

*Thumbstick X* Output thumbstick horizontal position.
-1 is left
+1 is right

*Thumbstick Y* Output thumbstick vertical position.
-1 is down
+1 is up

