block_watcher
=============

.. _block_watcher:

**Description**

Attaches to other blocks and emits jolts when stuff happens.



**Inputs, output and other parts**

*Selector* (selector) Pull out sticks to attach blocks to be watched. 

*Hover* (jolt output) Emits a jolt when you start or stop hovering your controller over an attached block.

*Grab* (jolt output) Emits a jolt when you grab or release an attached block.

*Hit* (jolt output) Emits the velocity of the controller when you hit and attached block (if it's hittable).

*Marble* (jolt output) Emits the velocity of the marble when an attached block gets hit by a marble (if it supports marble hits).

