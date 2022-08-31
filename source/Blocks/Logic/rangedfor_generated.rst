rangedfor
=========

.. _rangedfor:

**Description**

Instantly sends N events, from zero to N-1, when triggered.

**Inputs, output and other parts**

*Set* (jolt input) Triggers the process of sending jolts from 0 to N-1 (where N is set by the received jolt value).

*Output* (jolt output) Emits jolts from zero to N-1.

*Knob* (interactive) Sets N, the number of jolt to output when triggered.

*Button* (interactive) Triggers the process of sending jolts from 0 to N-1 (where N is set by the knob).

**See also:**

:ref:`nth <nth>`

