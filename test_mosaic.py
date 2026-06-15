import numpy as np
import mosaic
import matplotlib.pyplot as plt

imgPath = r"E:\AMPL\cube_subset"
propsPath = 'default_props.json'
toolpathFile = 'toolpath_empty.txt'
frameRange = np.arange(600, 620)

#fo, fro = mosaic.file_io.load_cine_file(r"E:\AMPL\Kyle APS Data\xray_exp490.cine", frameRange)
#print(fro.frameShape)
#plt.imshow(fro.openFrames[10])
#plt.show()

#Individual callouts for grouped functions. Can be useful for diagnosing issues
fo, fro = mosaic.core.init_load_images(imgPath, frameRange, verbose=True)
fro = mosaic.core.load_configs(fro, propsPath, toolpathFile, verbose=True)
fro = mosaic.core.run_preprocessing(fro, frameRange)
fro = mosaic.core.run_segmentation(fro, frameRange)
plt.figure()
plt.imshow(fro.procFrames[10])
plt.figure()
plt.imshow(fro.segFrames[10])
plt.show()
#fro = mosaic.core.sort_images(fro, verbose=True)

#Total run file and save
#_, fro = mosaic.core.run_mosaic(imgPath, frameRange, propsJSON=propsPath, toolpath=toolpathFile, verbose=True, coerceLowerBitDepth = True)
#mosaic.core.save_proc_img(fro)
#mosaic.core.save_seg_img(fro)