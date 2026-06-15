# MOSAIC   

<img width="66" height="53" alt="image" src="https://github.com/user-attachments/assets/6b4c3be1-dd28-4a74-8813-a2bea1dc341f" />

MOSAIC, or Moving Object Segmentation under Adverse Imaging Conditions, is a Python library (and soon to be application) that allows for segmentation of high-speed images when imaging conditions change or are unknown. The output is a binary mask of the region that is of interest.
## Installation
Installation of MOSAIC is currently under development and has not been tested on macOS/Linux systems. Please notify the authors if issues arise.
The necessary libraries are PIL, scikit-image, scipy, and numpy. Matplotlib is another recommended library, but it is not necessary for basic usage at this time.

Below is a simple method for installation using PyPI
```
$ git clone https://github.com/Garrett-Mathesen/MOSAIC.git
$ pip install -e .
```
It is as simple as that, in theory

## Basic Usage
Included in the repository is a 'test_mosaic.py' file, which will run MOSAIC on a folder with given frame numbers. It is important that that the image files in the folder have a format of 'any_file_name_#####.tif'. There is no limit on the number of digits, but the frame numbers you reference will be the same as the file number. It must be an integer.

An important file is the 'props.json' file, which defines the properties of the processing and segmentation. If the variable 'isMoving' is 'True', then the 'toolpathFile' variable must be given or else the program will throw an error. Details on the formatting for the props.json and toolpath file are given in another section.

The files that are processed will be saved to the same experimental folder for simplicity, with a new folder being generated for the process images and segmentation images separately.
