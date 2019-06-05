# DRMgr Plugin

This PCBNEW plugin lets you save and restore the board settings for a PCB.
This is useful for storing the design rules of a particular PCB fab and then
applying them to an existing or new project.

* Free software: MIT license


## Features

* Save current PCBNEW board settings into a file.
* Apply board settings from a file into a current PCBNEW session.


## Installation

Just copy `DRMgr.py` file to one of the following directories:

* Windows: `kicad/share/kicad/scripting/plugins`.
* Linux: `kicad/scripting/plugins`.

You will also have to install the [KinJector Python package](https://github.com/xesscorp/kinjector) using these
[instructions](https://xesscorp.github.io/kinjector/docs/_build/singlehtml/index.html).



## Usage

The plugin is started by pressing the `Tools => External Plugins... => DRMgr` button.
This adds a button to the PCBNEW window for each of the four WireIt tools:

![](WireIt_buttons.png)

### Saving Board Settings

### Applying Saved Board Settings
 
### Example

The video below demonstrates the use of the DRMgr tool:

[![DRMgr Demo](video_thumbnail.png)](https://youtu.be/-FPzxCktdcs)

## Credits

### Development Lead

* XESS Corp. <info@xess.com>

### Contributors

None yet. Why not be the first?


## History

### 0.1.0 (2019-06-05)

* First release.
