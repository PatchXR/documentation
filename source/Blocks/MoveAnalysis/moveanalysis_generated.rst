moveanalysis
============

.. _moveanalysis:

**Description**

Outputs values of selected movement efforts according to Laban movement analysis

Efforts calculations are based on the movement of the controllers and HMD. Features an auto scaling option (max never exceeds 1) that resets on patch reload. Can be used to extract higher level descriptors of the user's movements. Try searching for Laban movement analysis on YouTube to see movement examples for each effort.

**Inputs, output and other parts**

*Weight effort* (jolt output) Can be interpreted as weight of the movement. Strong movement corresponds to higher values.

*Time effort* (jolt output) Can be interpreted as timing of the movement. Quick, sudden movement corresponds to higher values.

*Space effort* (jolt output) Can be interpreted as directness of the movement. Indirect movement corresponds to higher values.

*Flow effort* (jolt output) Can be interpreted as smoothness of the movement. Chaotic movement corresponds to higher values.

*Left hand movement radius* (jolt output) Bigger radius of the left controller movement corresponds to higher values.

*Right hand movement radius* (jolt output) Bigger radius of the right controller movement corresponds to higher values.

**See also:**

:ref:`controloutput <controloutput>`, :ref:`controllerposition <controllerposition>`, :ref:`controllerrotation <controllerrotation>`, :ref:`hapticcontrol <hapticcontrol>`

