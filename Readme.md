# PatchXR Documentation

This repository contains the source files for the PatchXR documentation. Some of it
is generated automatically from the PatchXR source code, some is written by hand.

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