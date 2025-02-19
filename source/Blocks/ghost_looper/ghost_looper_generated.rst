ghost_looper
============

.. _ghost_looper:

**Description**

Let you record yourself. A copy of your avatar will then playback your movements on instruments.



**Inputs, output and other parts**

*Ghost loop ended* This triggers when ghost loop reached the end.

*Trigger Recording / Playback* Play / Record the ghost sequence.

*Offset Time* Will offset the ghost sequence playback, with a duration given in beat count.

*Pause On/Off* Send 0 to pause and hide the ghost. 1 to continue playing.

*Is Recording* 0  - Recording just started
x  - Time of recording
-1 - Recording Cancelled

*Recording duration* How long will be the recording in bar (4 beats).

*State* 0 Empty - 1 Standby - 2 Recording - 3 FinishingRecording - 4 Playback

*Progress* Progress time of the playback in beats.

*Record/Play Button* Hit the button once, get in position, then press "A" button on our controller to actually start the recording.
When a ghost is recorded, hit this button to play/pause the recording.

*Record Voice* Should we also record the voice from the microphone ?

*Record Voice on/off* Should we also record the voice from the microphone ?

*Loop on/off* Makes the recording to loop when finished.

*Loop on/off* Makes the recording to loop when finished.

*Clear* Delete the ghost recording.

*Cancel* Abort recording.

*Rewind* Rewind recording to the beginning.

