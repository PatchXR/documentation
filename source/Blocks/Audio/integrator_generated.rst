integrator
==========

.. _integrator:

**Description**

A leaky integrator with separate constants for the rise and fall time. This block can be used to smooth out an incoming signal so that the change in the signal level cannot exceed a certain value per second. Combine with the 'abs' block to create an envelope follower.

**Inputs, output and other parts**

*Signal input* (stream input) The signal to integrate.

*Rise control* (stream input) The integration constant to use when the signal is rising.

*Fall control* (stream input)  The integration constant to use when the signal is falling.

