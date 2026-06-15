from dataclasses import dataclass
import numpy as np
import re

@dataclass
class FileObject:
    #Generate a file object to keep track of files in use
    basePath: str
    fileExtension: str
    regexFile: re.Pattern
    numFiles: int
    listFiles: list[str]
    listFrameNums: np.array

@dataclass
class ProcessingProps:
    #Used to maintain the properties for the given image set being processed
    isMoving: bool
    toolpathFile: str
    toolpathArr: np.array
    window: tuple #(x_window_offset, y_window_offset, x_window_extent, y_window_extent)
    backgroundType: str
    backgroundProp1: float
    includeBackground: np.array
    butterworthCutoff: float
    rescaleIntens: tuple #(lower_bound, upper_bound)
    useMedian: bool
    medianSize: float
    timeFunc: bool
    useAbs: bool
    invertVal: bool

@dataclass
class SegmentationProps:
    #Used to maintain the properties for the given images set being segmented
    stationaryImgType: str
    excludeImg: bool
    excludeMinSpan: int
    numLevels: int
    numBins: int
    initMaskLevels: tuple
    remvPepperThresh: int
    fillHolesThresh: int
    sepOpeningRad: float
    overlapThres: float
    expDilationRad: float


@dataclass
class FrameObject:
    #Generate the necessary object to keep track of images being analyzed
    files: FileObject
    procProps: ProcessingProps
    segProps: SegmentationProps
    frameShape: tuple
    numFramesOpen: int
    openedFrameNums: np.array
    openFrames: np.array
    toExcludeFrames: np.array
    background: np.array
    toProcStack: np.array
    numFramesProc: int
    procFrameNums: np.array
    procFrames: np.array
    statFrame: np.array
    numFramesSeg: int
    segFrameNums: np.array
    segFrames: np.array
    segTime: float
    timeMeasured: float
    maskStack: np.array
    cropShape: np.array


