nth
===

.. _nth:

**Description**

Sends only one event every N events it receives.

**Inputs, output and other parts**

*N value* (stream input) Sets the value at which the counter will reset, start counting from zero again and trigger the output.

*Input* (jolt input) Counter increment trigger. Each received jolt triggers the count to increase by one.

*Set* (jolt input) Sets current count value.

*Output* (jolt output) Emits a jolt every time the count has reached the N value.

**See also:**

:ref:`rangedfor <rangedfor>`, :ref:`counter <counter>`

