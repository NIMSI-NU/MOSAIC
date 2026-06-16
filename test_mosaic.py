import numpy as np
import mosaic
import matplotlib.pyplot as plt

#Folder containing your images
imgPath = r"C:\Users\default\Documents\Folder_of_Experimental_Images"
#Image file extension
file_ext = '*.tif'
#Regex string to pull the file numbers (e.g. expName_00001, expName_00002,...)
#Follow the regex string formatting convention
file_regex = r'\d+'
#Properties .json file. Change 'isMoving' to true once you have a non-empty toolpath!
propsPath = 'default_props.json'
#Empty toolpath file. Frame number is in reference to Regex number found
toolpathFile = 'toolpath_empty.txt'

#if you have pixel points where the object is located for at least two frames
#toolpathVec = [[frame1, x1, y1], [frame2, x2, y2],...]

#Frame range in relation to file naming convention
frameRange = np.range(1, 100)

#Individual callouts for grouped functions. Can be useful for diagnosing issues
fo, fro = mosaic.core.init_load_images(imgPath, frameRange, verbose=True, extension=file_ext, regex_str=file_regex)
fro = mosaic.core.load_configs(fro, propsPath, toolpathFile, verbose=True)

#If using given points, use the following
#fro = mosaic.core.load_configs(fro, propsPath, verbose=True)
#fro = mosaic.process.vec_to_toolpath(fro, toolpathVec)
#Recommended to set non-moving axis (e.g. y axis in APS data) to 0, then use window property to crop

fro = mosaic.core.run_preprocessing(fro, frameRange)
fro = mosaic.core.run_segmentation(fro, frameRange)
plt.figure()
plt.imshow(fro.procFrames[10])
plt.figure()
plt.imshow(fro.segFrames[10])
plt.show()

#Total run file and save
#_, fro = mosaic.core.run_mosaic(imgPath, frameRange, propsJSON=propsPath, toolpath=toolpathFile, verbose=True, coerceLowerBitDepth = True)
#mosaic.core.save_proc_img(fro)
#mosaic.core.save_seg_img(fro)