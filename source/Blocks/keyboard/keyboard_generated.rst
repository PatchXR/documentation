keyboard
========

.. _keyboard:

**Description**

A keyboard interface that can be used to play notes by pressing the keys or to play music from a specific scale using the jolt input.



**Inputs, output and other parts**

*MIDI Out* (jolt output) Outputs the MIDI-number of the key you press, or the corresponding note if you send a jolt to INPUT.

*Num. notes* (jolt output) Ouputs the number of notes in the selected scale.

*Input* (jolt input) Send a jolt to make the keyboard output the MIDI-number of the corresponding note in the scale, starting form zero. E.g. sending 0 will send out the root note, or if you have a major or minor scale selected sending a 2 will output the third.

*Root note* (knob) Sets the root note of the keyboard and scale. Maps "C" key to choosen note.

*Root note* (jolt input) Send a jolt to set the root note of the keyboard and scale. Maps "C" key to choosen note.

*Use Global Scale* (jolt input) Will share the same notes as other global keyboards.

*Play/Scale Toggle*  Switch between Play/Scale edit mode.

