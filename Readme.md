# PatchXR Documentation

This repository contains the source files for the PatchXR documentation. Some of it
is generated automatically from the PatchXR source code, some is written by hand.

## TL;DR

To generate the documentation from scratch, run these commands:
```
$ python build_rst_from_blocks_json.py --clean
$ python build_rst_from_blocks_json.py
```

And then (Windows)
```
$ .\make.bat html
```

Or unix
```
$ make html
```

## Installing and Building

To build the documentation you must first install [Sphinx](https://www.sphinx-doc.org/).
This is easily done via PyPi with the command

```
$ pip install -U sphinx
```

You also need to install the Read the Docs HTML Theme by running

```
$ pip install sphinx-rtd-theme
```

You can then build the documentation on Unix-like systems with

```
$ make html
```

And on Windows with

```
$ .\make.bat html
```

## Generating Block Documentation

The documentation for the indivisual blocks is generated from the .json files residing
in *NewPatch/Assets/Blocks/**. We convert these to .rst files using the *build_rst_from_blocks_json.py* script.

To use it, make sure that this (the documentation) repository and the NewPatch repository are
cloned to the same parent directory and that you've pulled the latest changes.

Now run the command
```
$ python build_rst_from_blocks_json.py
```
On success it will finish without output (unix style).

If you want to see what the script is doing, give it the `-v` flag
```
$ python build_rst_from_blocks_json.py -v
```

You can clean the files in the *source/Blocks/* directory with
```
$ python build_rst_from_blocks_json.py --clean
```

## Documentation Format

Here is an example of the documentation for s_mul with added comments (even though JSON
doesn't support comments)-

```
{
    "name": "s_mul",    # The name of the block.
    "menuPath": "Math", # The category of the block and where it will be placed in the printer/documentation.
    "description": "Multiplies two streams and outputs the result (a * b)", # A longer description of what the block does and its outputs.
    "examplePatch": "", # Name of the example patch, which shows how to use the block.
    "blockType": 1,     # Legacy field from old documentation system, not used.
    "active": true,     # True if the block should be available within the game.
    "includeInWebDocumentation": true,  # True if the block should be included in the online documentation.
    "parts": [      # List of info about all the inputs, outputs, and other parts of the block.
        {
            "name": "a",    #                   # The name of the part as shown to the user.
            "description": "The first stream",  # A longer description of the part.
            "type": "stream input",             # The type of the part. See next section for a list of accepted types.
            "unityName": "a"                    # The name of the part within unity, do not change unless you know what you're doing.
        },
        {
            "name": "b",
            "description": "The second stream",
            "type": "stream input",
            "unityName": "b"
        }
    ],
    "relatedBlocks": [  # List of blocks that the user might also be interested when reading about this block.
        {
            "name": "s_add" # The name of the related block
        },
                {
            "name": "s_sub"
        }
    ]
}
```

## Documentation Guidelines

To ensure a consistent style in the documentation, please follow these guidelines.

- All blocks, inputs, and outputs should be named with *under_scores*.
- All block, input, output and other part descriptions should start with a 
  captial letter and end on a period.
- If a part has a type, use one of the standard types with correct casing (lowercase).
  Please contact Pelle if you want to add another type. The standard types are:
  - knob
  - stream input
  - event input
  - event output
- Do not change the name of a block. The name is the samed as the one used in unity and
  in the .patch files, so changing the name requires editing stuff in the unity project.