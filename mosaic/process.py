#This is the processing portion of the library
#Different substeps are given to portion out the code and
#allow better 'plug-and-play' functionality

from collections.abc import Callable
import time

import numpy as np
from skimage import exposure, draw, morphology, filters, util
import scipy.ndimage as ndi

from .data_strcutures import FrameObject, ProcessingProps

def vec_to_toolpath(fro: FrameObject, pntList: np.array):
    #Format of the pntList is [[Frame1, x1, y1],[Frame2, x2, y2], ...etc]
    #To have a turn around, the Frame3 must have x3=x2 and y3=y2
    totalFrames = fro.openedFrameNums
    frameChange = pntList[:,0]
    diffPnts = np.concatenate((np.array([[0, 0, 0]]), np.diff(pntList, axis = 0), np.array([[0, 0, 0]])), axis = 0)
    pntList = np.concatenate((np.array([pntList[0]]), pntList, np.array([pntList[-1]])), axis = 0)
    toolpathArr = np.zeros((len(totalFrames), 3))
    changeNum = 0
    counter = 0
    changeIdx = np.concatenate((np.nonzero(frameChange[:, None] == totalFrames)[1], np.array([0])))
    for i in range(toolpathArr.shape[0]):
        dX = diffPnts[changeNum, 1]/np.max([diffPnts[changeNum, 0], 1])
        dY = diffPnts[changeNum, 2]/np.max([diffPnts[changeNum, 0], 1])
        toolpathArr[i] = np.array([totalFrames[i],
                                   pntList[changeNum, 1] + counter*dX,
                                   pntList[changeNum, 2] + counter*dY])
        if i == changeIdx[changeNum]:
            changeNum += 1
            counter = 1
        else:
            counter += 1
    fro.procProps.toolpathFile = 'generated'
    fro.procProps.toolpathArr = toolpathArr.astype(np.int32)
    return fro


def default_smooth_img(img: np.array, props: ProcessingProps) -> np.array:
    butterworth = filters.butterworth(img, 
                                      cutoff_frequency_ratio = props.butterworthCutoff, 
                                      high_pass=False)
    imgMean, imgStd = np.nanmean(butterworth), np.nanstd(butterworth)
    rescale = exposure.rescale_intensity(butterworth,
                                         in_range = (imgMean - props.rescaleIntens[0]*imgStd,
                                                     imgMean + props.rescaleIntens[1]*imgStd),
                                         out_range = (0, 1))
    if props.useMedian:
        median = filters.median(rescale, morphology.disk(props.medianSize))
        postMedian = exposure.rescale_intensity(median, out_range = (0, 1))
        return postMedian
    else:
        return rescale

def crop_img_stack(fro: FrameObject, processFrames: np.array):
    #Toolpath array headers should be frame_num, x_loc, y_loc
    #Crop parameters are set based on toolpath relative values: (x_0, y_0, x_ext, y_ext)
    if fro.procProps.isMoving:
        toolpathArr = fro.procProps.toolpathArr
        framesToolpath = toolpathArr[:,0]
        frameShape = fro.frameShape
        cropProps = fro.procProps.window

        maskTool = np.nonzero(processFrames[:, None] == framesToolpath)[1]

        if np.all(maskTool == False):
            raise Exception("ERROR: No valid toolpath points are available. Please regenerate toolpath \n OR ... set 'isMoving' to false in .json file")
        
        toolpathValid = toolpathArr[maskTool, :]
        negXPad = int(np.clip(-1*(np.min(toolpathValid[:,1]) + cropProps[0]), a_min=0, a_max=None))
        negYPad = int(np.clip(-1*(np.min(toolpathValid[:,2]) + cropProps[1]), a_min=0, a_max=None))
        posXPad = int(np.clip(np.max(toolpathValid[:,1]) + cropProps[0] + cropProps[2] - frameShape[1], a_min=0, a_max=None))
        posYPad = int(np.clip(np.max(toolpathValid[:,2]) + cropProps[1] + cropProps[3] - frameShape[0], a_min=0, a_max=None))
        maskStack = np.nonzero(processFrames[:, None] == fro.openedFrameNums)[1]
        rawProcStack = fro.openFrames[maskStack, :, :]
        toProcStack = np.pad(rawProcStack, pad_width=((0,0),(negYPad, posYPad),(negXPad, posXPad)))
        maskStack = np.zeros(toProcStack.shape, dtype=bool)
        for i in range(len(processFrames)):
            crop_wind = (np.clip(toolpathValid[i, 2] + cropProps[1] + negYPad, a_min=0, a_max=maskStack.shape[1]),
                        np.clip(toolpathValid[i, 1] + cropProps[0] + negXPad, a_min=0, a_max=maskStack.shape[2]))
            rr, cc = draw.rectangle(start=crop_wind, extent = (cropProps[3], cropProps[2]), shape=toProcStack.shape[1:])
            maskStack[i, rr, cc] = True
        cropShape = (cropProps[3], cropProps[2])
    else:
        maskFrames = np.nonzero(processFrames[:, None] == fro.openedFrameNums)[1]
        toProcStack = fro.openFrames[maskFrames, :, :]
        maskStack = np.ones(toProcStack.shape, dtype=bool)
        cropShape = toProcStack.shape[1:]
    
    return maskStack, toProcStack, cropShape

def single_img_process(img: np.array, background: np.array, 
                       props: ProcessingProps, 
                       smooth_func: Callable[[np.array, ProcessingProps], np.array],
                       mask: np.array, cropShape: tuple):
    if props.useAbs:
        diffImg_full = np.abs(img - background)
    else:
        diffImg_full = img - background
    
    diffImg_full = exposure.rescale_intensity(diffImg_full, out_range=(0,1))
    
    if props.invertVal:
        diffImg_full = util.invert(diffImg_full)

    diffImg = diffImg_full[mask].reshape((cropShape[0], cropShape[1]))
    start = time.perf_counter()
    processedImg = smooth_func(diffImg, props)
    end = time.perf_counter()
    return processedImg, (end - start)

def match_background(fro: FrameObject, toProcStack: np.array, processFrameNums: np.array):
    match fro.procProps.backgroundType:
            case "uniform":
                background = ndi.uniform_filter(toProcStack,
                                                size=(fro.procProps.backgroundProp1, 1, 1))
            case "mean_excluded":
                diffImgs = np.diff(toProcStack, axis = 0)
                stdVals = np.array([np.std(frame) for frame in diffImgs])
                toInclude = stdVals < stdVals.mean() + fro.procProps.backgroundProp1*np.std(stdVals)
                toIncludeIdx = np.nonzero(toInclude)[0]
                fro.toExcludeFrames = processFrameNums[toIncludeIdx]
                background = np.mean(toProcStack[toIncludeIdx], axis = 0)
            case "mean_all":
                background = np.mean(toProcStack, axis = 0)
            case "median_all":
                background = np.median(toProcStack, axis = 0)
            case _:
                background = np.zeros(toProcStack.shape)
    return background
    
def img_stack_process(fro: FrameObject, processFrameNums: np.array = None, smooth_func = default_smooth_img):
    #Smooth function can be anything, but must take in image as np.array, props as ProcessingProps class.
    #Smooth function must output an np.array the same size as the input

    if processFrameNums is None:
        processFrameNums = fro.openedFrameNums

    maskStack, toProcStack, cropShape = crop_img_stack(fro, processFrameNums)
    fro.maskStack = maskStack
    fro.cropShape = cropShape
    background = match_background(fro, toProcStack, processFrameNums)
    
    
    proccedStack = np.zeros((toProcStack.shape[0], cropShape[0], cropShape[1]))
    timeOut = 0

    for i in range(toProcStack.shape[0]):
        imgFront = toProcStack[i]
        if len(background.shape) > 2:
            imgBack = background[i]
        else:
            imgBack = background
        proccedStack[i], time_i = single_img_process(imgFront,
                                                     imgBack,
                                                     fro.procProps,
                                                     smooth_func,
                                                     fro.maskStack[i],
                                                     cropShape)
        timeOut += time_i
    
    fro.procFrameNums = processFrameNums
    fro.procFrames = proccedStack
    fro.numFramesProc = len(processFrameNums)
    if fro.procProps.timeFunc:
        fro.timeMeasured = timeOut/len(processFrameNums)

    return fro