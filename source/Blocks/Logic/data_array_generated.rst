data_array
==========

.. _data_array:

**Description**

Store and retrieve values from an array using indices to build presets, sequencers, etc..

The data_array block can be used to store values to be recalled later. Sending an index

**Inputs, output and other parts**

*Read index* (jolt input) Send a jolt to read the value at a given index.

*Write index* (jolt input) Send a jolt to select which index will be written to next time a value is received.

*value* (jolt input) Send a jolt to write a value to the index selected via the 'Write index' input

*value* (jolt output) Emit the stored value when a jolt is received through the 'Read index' jolt input.

