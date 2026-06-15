#This file is used for input and output of files in the core MOSAIC library
#Additional file types can be added here when desired

#Importing the base libraries necessary
import os
import re
import glob
import json

#Importing other critical libraries that should be installed by the user
from PIL import Image
import numpy as np
import cinereader as cine
import pyMRAW
from .data_strcutures import FileObject, FrameObject, ProcessingProps, SegmentationProps

#We want to make a file object initiator
def init_img_file_obj(basePath: str, extension: str = '*.tif', regex_str: str = r'\d+'):
    fo = FileObject
    fo.basePath = basePath
    fo.fileExtension = extension
    fo.regexFile = re.compile(regex_str)
    #Now we need to open the folder to see what might be inside
    total_ext_file_list = glob.glob(os.path.join(basePath, extension))
    #We assume that the final number in the string is the frame number
    frameNums = []
    filesValid = []
    for file in total_ext_file_list:
        if fo.regexFile.search(file) is not None:
            frameNums = frameNums + [int(fo.regexFile.findall(file)[-1])]
            filesValid = filesValid + [file]

    frameNums = np.array(frameNums)
    fo.numFiles = len(filesValid)
    fo.listFiles = filesValid
    fo.listFrameNums = frameNums
    
    return fo

def load_img_file(fo: FileObject, frameNums: np.array = None, coerceLowerBitDepth: bool = True):
    if frameNums is None:
        frameNums = fo.listFrameNums
    #Determine the frame size based on first frame
    listFilesReq = np.nonzero(frameNums[:,None] == fo.listFrameNums)[1]
    img_size = np.shape(Image.open(fo.listFiles[listFilesReq[0]]))
    #Generate images from files
    img_stack = np.zeros((len(listFilesReq), img_size[0], img_size[1]))
    #check img bitdepth
    img1 = Image.open(fo.listFiles[listFilesReq[0]])
    isHighBit = img1.mode in {'I', 'F'}
    for i in range(len(listFilesReq)):
        if coerceLowerBitDepth and isHighBit:
            img_i = np.array(Image.open(fo.listFiles[listFilesReq[i]]), dtype=np.int16)
        else:
            img_i = np.array(Image.open(fo.listFiles[listFilesReq[i]]))
        if np.all(img_size == img_i.shape):
            img_stack[i] = img_i
        else:
            print("Error in loading image. Sizes are different")
    fro = FrameObject
    fro.files = fo
    fro.openedFrameNums = fo.listFrameNums[listFilesReq]
    fro.frameShape = img_size
    fro.openFrames = img_stack
    fro.numFramesOpen = len(frameNums)

    return fro

def load_cine_file(filePath: str, frameNums: np.array = None):

    metadata = cine.read_metadata(filePath)
    img_count = metadata.ImageCount
    first_img = metadata.FirstImageNo

    if frameNums is None:
        _, images, _ = cine.read(filePath, start=first_img, count=img_count-1)
        frameNums = np.arange(first_img, first_img + img_count)
        toSave = np.array(images)
    else:
        if frameNums.min() < first_img or frameNums.max() > img_count:
            raise Exception("Issue with the frame numbers given and the .cine file meta data")
        else:
            _, images, _ = cine.read(filePath, start=frameNums.min(), count=len(frameNums))
            toSave = np.array(images)
    
    fo = FileObject
    fo.basePath = filePath
    fo.fileExtension = '*.cine'
    fo.listFrameNums = frameNums
    fo.numFiles = 1

    fro = FrameObject
    fro.files = fo
    fro.frameShape = [metadata.ImHeight, metadata.ImWidth]
    fro.openedFrameNums = frameNums
    fro.numFramesOpen = len(frameNums)
    fro.openFrames = toSave

    return fo, fro

def load_mraw_file(cih_filePath: str, frameNums: np.array = None):
    cih = pyMRAW.get_cih(cih_filePath)
    name = os.path.splitext(cih_filePath)[0]
    mrawFile = name + '.mraw'
    h, w, N = cih['Image Height'], cih['Image Width'], cih['Total Frame']
    bit = cih['Color Bit']
    totalImages = pyMRAW.load_images(mrawFile, h, w, N, bit, roll_axis=False)
    totalImgList = np.arange(N+1)
    fo = FileObject
    fo.basePath = cih_filePath
    fo.fileExtension = '*.mraw'
    fo.numFiles = 1
    fo.listFrameNums = totalImgList
    
    fro = FrameObject
    fro.files = fo
    fro.frameShape = [h, w]

    if frameNums is None:
        fro.openedFrameNums = totalImgList
        fro.openFrames = totalImages
        fro.numFramesOpen = len(totalImgList[mask])
    else:
        mask = np.nonzero(frameNums[:, None] == totalImgList)[1]
        fro.openFrames = totalImages[mask]
        fro.openedFrameNums = frameNums[mask]
        fro.numFramesOpen = len(frameNums[mask])
    
    return fo, fro

def load_toolpath(fro: FrameObject, toolpathFile: str):
    file_load = np.loadtxt(toolpathFile, delimiter=',', skiprows=1, ndmin=2)
    fro.procProps.toolpathArr = file_load
    fro.procProps.toolpathFile = toolpathFile
    return fro

def load_props(fro: FrameObject, propsFile: str):
    if propsFile is None:
        fro.procProps = ProcessingProps
        fro.segProps = SegmentationProps
        return fro
    f = open(propsFile)
    dataJSON = json.load(f)
    procProps = dataJSON["processing_props"]
    segProps = dataJSON["segmentation_props"]
    #Now assign the properties
    genProcProps = ProcessingProps
    genSegProps = SegmentationProps

    genProcProps.isMoving = procProps.get("isMoving", False)
    genProcProps.window = procProps.get("window",[0, 0, 0, 0])
    genProcProps.backgroundType = procProps.get("backgroundType", 'uniform')
    genProcProps.backgroundProp1 = procProps.get("backgroundProp1", 1)
    genProcProps.butterworthCutoff = procProps.get("butterworthCutoff", 0.2)
    genProcProps.rescaleIntens = procProps.get("rescaleItens", [1, 1])
    genProcProps.useMedian = procProps.get("useMedian", True)
    genProcProps.medianSize = procProps.get("medianSize", 3)
    genProcProps.timeFunc = procProps.get("timeFunc", True)
    genProcProps.useAbs = procProps.get("useAbs", False)
    genProcProps.invertVal = procProps.get("invertVal", False)

    genSegProps.stationaryImgType = segProps.get("stationaryImgType", 'median')
    genSegProps.excludeImg = segProps.get("excludeImg", False)
    genSegProps.excludeMinSpan = segProps.get("excludeMinSpan", 50)
    genSegProps.numLevels = segProps.get("numLevels", 5)
    genSegProps.numBins = segProps.get("numBins", 25)
    genSegProps.initMaskLevels = segProps.get("initMaskLevels", [3, 3, 1])
    genSegProps.remvPepperThresh = segProps.get("remvPepperThres", 64)
    genSegProps.fillHolesThresh = segProps.get("fillHolesThresh", 600)
    genSegProps.sepOpeningRad = segProps.get("sepOpeningRad", 2)
    genSegProps.overlapThres = segProps.get("overlapThres", 0.1)
    genSegProps.expDilationRad = segProps.get("expDilationRad", 5)

    fro.procProps = genProcProps
    fro.segProps = genSegProps
    f.close()

    return fro

def start_props(fro: FrameObject):
    empty = {"processing_props":{}, "segmentation_props":{}}
    os.makedirs('temp', exist_ok=True)
    f = open(os.path.join('temp','temp_props.json'), mode='w')
    json.dump(empty,f,indent=3)
    f.close()
    fro = load_props(fro, os.path.join('temp','temp_props.json'))
    return fro

def save_props(fro: FrameObject, file: str = os.path.join('temp','temp_props.json')):
    dictProcProps = {key:value for key, value in fro.procProps.__dict__.items() if not key.startswith('__') and not callable(key)}
    dictSegProps = {key:value for key, value in fro.segProps.__dict__.items() if not key.startswith('__') and not callable(key)}
    fullProps = {"processing_props": dictProcProps, "segmentation_props": dictSegProps}
    f = open(file, mode='w')
    json.dump(fullProps, f, indent=3)
    f.close()
