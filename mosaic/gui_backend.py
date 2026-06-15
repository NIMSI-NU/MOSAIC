#This file is similar to core.py but with noteable changes to
#allow  for better control from the GUI interface of MOSAIC
#Importing libraries under the standard Python library
import logging
import os

import numpy as np
from PIL import Image

#Importing local libraries (TO DO)
from .process import crop_img_stack, match_background, single_img_process, default_smooth_img
from .segment import exclude_imgs, stationary_img, multi_level_otsu, single_img_segment
from .data_strcutures import FrameObject

def gui_run_processing(fro: FrameObject, preprocessList: np.array, idxNum: int):
    if idxNum == 0:
        maskStack, toProcStack, cropShape = crop_img_stack(fro, preprocessList)
        fro.toProcStack = toProcStack
        fro.maskStack = maskStack
        fro.cropShape = cropShape
        background = match_background(fro, toProcStack, preprocessList)
        fro.background = background
        fro.procFrames = np.zeros((toProcStack.shape[0], cropShape[0], cropShape[1]))
        if len(background.shape) > 2:
            backImg = background[0]
        else:
            backImg = background
        frontImg = toProcStack[0]
        fro.procFrames[0], time = single_img_process(frontImg,
                                                     backImg,
                                                     fro.procProps,
                                                     default_smooth_img,
                                                     fro.maskStack[idxNum],
                                                     fro.cropShape)
        fro.procFrameNums = np.array([preprocessList[0]])
        fro.numFramesProc = 1
        return fro, time
    else:
        mask = fro.maskStack[idxNum]
        frontImg = fro.toProcStack[idxNum]
        if len(fro.background.shape) > 2:
            backImg = fro.background[idxNum]
        else:
            backImg = fro.background
        fro.procFrames[idxNum], time = single_img_process(frontImg,
                                                          backImg,
                                                          fro.procProps,
                                                          default_smooth_img,
                                                          mask,
                                                          fro.cropShape)
        fro.procFrameNums = np.concatenate((fro.procFrameNums, [preprocessList[idxNum]]))
        fro.numFramesProc += 1
        return fro, time
    
def gui_run_segmentation(fro: FrameObject, segmentList: np.array, idxNum: int):
    if idxNum == 0:
        if fro.segProps.excludeImg:
            segmentList = exclude_imgs(fro, segmentList)
        maskStack = np.nonzero(segmentList[:, None] == fro.procFrameNums)[1]
        statFrameRaw = stationary_img(fro.procFrames[maskStack, :, :], fro)
        fro.statFrame = multi_level_otsu(statFrameRaw,
                                         numLevels=fro.segProps.numLevels,
                                         bins=fro.segProps.numBins)
        segImg1 = multi_level_otsu(fro.procFrames[maskStack[0], :, :],
                                   numLevels=fro.segProps.numLevels,
                                   bins=fro.segProps.numBins)
        fro.segFrames = np.zeros((len(maskStack), fro.procFrames.shape[1], fro.procFrames.shape[2]))
        fro.numFramesSeg = len(maskStack)
        fro.segFrameNums = np.zeros(len(maskStack))
        fro.segFrameNums[0] = fro.procFrameNums[maskStack[0]]
        fro.segFrames[0] = single_img_segment(segImg1, fro.statFrame, fro.segProps)
        fro.numFramesSeg = 1
        return fro
    else:
        idxProc = np.nonzero(segmentList[idxNum] == fro.procFrameNums)[0][0]
        print(idxProc)
        segImgi = multi_level_otsu(fro.procFrames[idxProc, :, :],
                                   numLevels=fro.segProps.numLevels,
                                   bins=fro.segProps.numBins)
        fro.segFrameNums[idxNum] = fro.procFrameNums[idxProc]
        fro.segFrames[idxNum] = single_img_segment(segImgi, fro.statFrame, fro.segProps)
        fro.numFramesSeg += 1
        return fro