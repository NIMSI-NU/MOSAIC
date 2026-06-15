#This is the segmentation portion of the library
#Different substeps are given to portion out the code and
#allow better 'plug-and-play' functionality

import numpy as np
from skimage import measure, morphology, filters
from scipy.ndimage import distance_transform_edt
import time

from .data_strcutures import FrameObject, SegmentationProps

def multi_level_otsu(img: np.array, numLevels: int = 5, bins: int = 25):
    levels = filters.threshold_multiotsu(img, numLevels, bins)
    outImg = np.zeros(img.shape)
    for i in range(int(numLevels - 1)):
        outImg += 1*(img > levels[i])
    return outImg

def stationary_img(stationaryImgStack: np.array, fro: FrameObject):
    match fro.segProps.stationaryImgType:
        case "median":
            outImg = np.median(stationaryImgStack, axis = 0)
        case "mean":
            outImg = np.mean(stationaryImgStack, axis = 0)
        case _:
            outImg = np.zeros(stationaryImgStack.shape[1:])
    return outImg

def single_img_segment(procImg: np.array, coreImg: np.array, segProps: SegmentationProps):
    #Generate necessary 2D masks
    relaxMask = np.logical_or(procImg > segProps.initMaskLevels[0],
                              coreImg > segProps.initMaskLevels[1])
    coreMask = np.logical_and(procImg == segProps.numLevels - 1,
                              coreImg == segProps.numLevels - 1)
    avoidMask = np.logical_not(procImg <= segProps.initMaskLevels[2])
    initMask = np.logical_and(relaxMask, avoidMask)
    overlapMask = np.zeros(procImg.shape)
    #Modify mask before iteration
    remvPepper = morphology.remove_small_objects(initMask, max_size=segProps.remvPepperThresh)
    fillHoles = morphology.remove_small_holes(remvPepper, max_size=segProps.fillHolesThresh)
    maskOpened = morphology.opening(fillHoles, morphology.disk(segProps.sepOpeningRad))
    labelsOpened = measure.label(maskOpened)
    #Perform Single Step labelling
    area_L = np.bincount(labelsOpened.ravel())
    area_M = np.sum(coreMask)
    intersection_counts = np.bincount(labelsOpened[coreMask])
    intersections = np.zeros_like(area_L)
    intersections[:len(intersection_counts)] = intersection_counts
    unions = area_L + area_M - intersections
    with np.errstate(divide='ignore', invalid='ignore'):
        ious = intersections / unions
    ious[0] = 0
    valid_labels = np.where(ious >= segProps.overlapThres)[0]
    overlapMask = np.isin(labelsOpened, valid_labels)
    #Now expand to include new regions
    expandMask = morphology.dilation(overlapMask, morphology.disk(segProps.expDilationRad))
    fullMask = np.logical_and(expandMask, fillHoles)
    cleanMask = morphology.remove_small_objects(fullMask, max_size=segProps.remvPepperThresh)
    bloatMask =  morphology.dilation(cleanMask, morphology.disk(segProps.sepOpeningRad))
    distMask = distance_transform_edt(bloatMask)
    outMask = np.logical_or(fullMask, distMask > segProps.sepOpeningRad)

    return outMask

def exclude_imgs(fro: FrameObject, segFrameNums: np.array = None):
    excludeFrameOverlaps = np.nonzero(segFrameNums[:, None] == fro.toExcludeFrames)[1]
    excludeFramesSeg = fro.toExcludeFrames[excludeFrameOverlaps]
    jumps = np.diff(excludeFramesSeg) > 1
    changePoints = np.concatenate(([0], np.where(jumps)[0] + 1, [len(excludeFramesSeg)]))
    runLengths = np.diff(changePoints)
    excludeLengths = np.repeat(runLengths, runLengths)
    reducedExcludeMask = excludeLengths > fro.segProps.excludeMinSpan
    reducedExclude = excludeFramesSeg[reducedExcludeMask]
    newSegFrameNums = segFrameNums[~np.isin(segFrameNums, reducedExclude)]
    return newSegFrameNums
    
    

def img_stack_segment(fro: FrameObject, segFrameNums: np.array = None):
    if segFrameNums is None:
        segFrameNums = fro.procFrameNums

    if fro.segProps.excludeImg:
        segFrameNums = exclude_imgs(fro, segFrameNums)
    
    maskStack = np.nonzero(segFrameNums[:, None] == fro.procFrameNums)[1]
    toSegStack = fro.procFrames[maskStack, :, :]
    coreImgRaw = stationary_img(toSegStack, fro)
    coreImg = multi_level_otsu(coreImgRaw,
                               numLevels=fro.segProps.numLevels,
                               bins = fro.segProps.numBins)
    
    time_total = 0
    segStack = np.zeros(toSegStack.shape)
    for i in range(segStack.shape[0]):
        procImg = multi_level_otsu(toSegStack[i],
                                   numLevels=fro.segProps.numLevels,
                                   bins = fro.segProps.numBins)
        time_start = time.perf_counter()
        segStack[i] = single_img_segment(procImg, coreImg, fro.segProps)
        time_end = time.perf_counter()
        time_total += time_end - time_start
    
    fro.segTime = time_total/len(segFrameNums)
    fro.segFrameNums = segFrameNums
    fro.numFramesSeg = len(segFrameNums)
    fro.segFrames = segStack

    return fro

     