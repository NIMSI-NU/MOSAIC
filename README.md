# MOSAIC   

<img width="66" height="53" alt="image" src="https://github.com/user-attachments/assets/779bf708-413e-436a-8ace-0df89a4932ec" />

MOSAIC, or Moving Object Segmentation under Adverse Imaging Conditions, is a Python library (and soon to be application) that allows for segmentation of high-speed images when imaging conditions change or are unknown. The output is a binary mask of the region that is of interest.
## Installation
Installation of MOSAIC is currently under development and has not been tested on macOS/Linux systems. Please notify the authors if issues arise.
The necessary libraries are included in the setup.py file.

Below is a simple method for installation using a conda env and pip
```
$ git clone https://github.com/Garrett-Mathesen/MOSAIC.git
$ conda create -n mosaic-env
$ conda activate mosiac-env
$ pip install -e .
```

## Basic Usage
Included in the repository is a 'test_mosaic.py' file, which will run MOSAIC on a folder with given frame numbers. It is important that that the image files in the folder have a format of 'any_file_name_#####.tif'. Otherwise, you will need to create a new regex expression to account for the name change. There is no limit on the number of digits, but the frame numbers you reference will be the same as the file number. It must be an integer.

An important file is the 'props.json' file, which defines the properties of the processing and segmentation. A wiki is under development to explain the exact function of each variable. If the variable 'isMoving' is 'True', then the 'toolpathFile' variable or a 'toolpathVec' must be given or else the program will throw an error.

The files that are processed will be saved to the same experimental folder for simplicity, with a new folder being generated for the process images and segmentation images separately.

## GUI Status
A beta of the gui is available for use, but is in an experimental state. Tkinter will be required to run the GUI properly. To ensure that the program does not crash or throw an error, please ignore all '(optional)' flags for text descriptions of the variables. This is currently under development and should be optional in the future, but is currently not working properly.

## Citation

This work has been submitted to the International Symposium on Flexible Automation 2026. A full peer-reviewed publication is expected in the coming months. In the meantime, please check back to this GitHub page (star it!) for updated DOI information. 

See the arXiv link for the preprint of the paper! https://doi.org/10.48550/arXiv.2606.16186
