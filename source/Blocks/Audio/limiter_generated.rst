limiter
=======

.. _limiter:

**Description**

Applies brick wall limiting to the incoming signal, to control the amplitude.

**Inputs, output and other parts**

*Signal input* (stream input) The signal to which the limiting will be applied.

*Release time* (stream input) How fast the limiter will stop suppressing the input signal once the threshold is no longer crossed.

*Look-ahead time* (stream input) Time 'ahead' at which the limiter will start suppressing the signal once the threshold has been crossed.

*Attack time* (stream input) How fast the limiter will start suppressing the input signal once the threshold level has been crossed.

*Threshold level* (stream input) The signal level above which the limiting will be applied. Set in linear units. (0-1 range)

