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