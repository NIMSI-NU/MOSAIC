#MOSAIC: Moving Object Segmenation under Adverse Imaging Conditions
#This is the core library that is needed to run MOSAIC
#Principle code development performed by Garrett Mathesen
#Additional Contributors to this intellectual property include: Kyle Mumm, Carter Taylor, and Prof. Jian Cao
#This library serves as a way for experimental data to be extracted from complex images

#Importing libraries under the standard Python library
import logging
import os

import numpy as np
from PIL import Image

#Importing local libraries (TO DO)
from .file_io import load_props, load_img_file, init_img_file_obj, load_toolpath, start_props, save_props
from .process import img_stack_process
from .segment import img_stack_segment
from .data_strcutures import FrameObject

def run_mosaic(loadFolder: str, openFrameNums: np.array, procFrameNums: np.array = None,
              segFrameNums: np.array = None, propsJSON: str = None, toolpath: str = None,
              verbose: bool = False, coerceLowerBitDepth: bool = False, **kwargs):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    logging.getLogger("PIL").propagate = False
    logging.info('Running MOSAIC')
    fo = init_img_file_obj(loadFolder, **kwargs)
    fro = load_img_file(fo, openFrameNums, coerceLowerBitDepth=coerceLowerBitDepth)
    logging.debug('Image files are loaded')
    if propsJSON is None:
        fro = start_props(fro)
        save_props(fro)
    else:
        fro = load_props(fro, propsJSON)
    logging.debug('Property file has been loaded/generated')
    if toolpath is not None:
        fro = load_toolpath(fro, toolpath)
        print('Toolpath file has been loaded')
    logging.debug('Starting to process images...')
    fro = img_stack_process(fro, procFrameNums, **kwargs)
    logging.debug('Preprocessing Done! Segmenting images')
    fro = img_stack_segment(fro, segFrameNums)
    logging.debug('Segmentation of images complete')
    logging.info('MOSIAC calculations complete')
    logging.disable()
    return fo, fro

def init_load_images(loadFolder: str, openFrameNums: np.array, verbose: bool = False, **kwargs):
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s', force=True)
    logging.getLogger("PIL").propagate = False
    logging.debug('Initiating file object')
    fo = init_img_file_obj(loadFolder, **kwargs)
    logging.debug('Initialization complete, loading images')
    fro = load_img_file(fo, openFrameNums)
    logging.debug('Image loading complete')
    logging.disable()
    return fo, fro

def load_configs(fro: FrameObject, propsJSON: str = None, toolpath: str = None, verbose: bool = False):
    if propsJSON is None and toolpath is None:
        print('WARNING: Empty configuration file paths. Nothing done')
        return fro
    elif propsJSON is None:
        fro = load_toolpath(fro, toolpath)
        if verbose:
            print('DEBUG: Toolpath has been loaded. No property file loaded')
    elif toolpath is None:
        fro = load_props(fro, propsJSON)
        if verbose:
            print('DEBUG: Property file loaded. No toolpath file loaded')
    else:
        fro = load_props(fro, propsJSON)
        fro = load_toolpath(fro, toolpath)
        if verbose:
            print('DEBUG: Both property and toolpath files have been loaded') 
    logging.disable()
    return fro

def run_preprocessing(fro: FrameObject, preprocessList: np.array, **kwargs):
    if not hasattr(fro, 'openFrames'):
        print('WARNING: There are no pictures to process. Please load images. Returning')
        return fro
    
    if not hasattr(fro, 'procProps'):
        print('WARNING: There are no processing properties')
        print('Would you like to load the default settings?')
        response = input('y/n [n]: ') or 'n'
        if response.lower() == 'y':
            fro = start_props(fro)
            save_props(fro)
            print('View default settings at ./temp/temp_props.json')
        else:
            print('No action taken. Returning')
            return fro
    
    fro = img_stack_process(fro, preprocessList, **kwargs)
    return fro

def run_segmentation(fro: FrameObject, segmentationList: np.array, **kwargs):
    if not hasattr(fro, 'procFrames'):
        print('WARNING: There are no processed images to segment')
        print('Would you like to process the images?')
        response = input('y/n [y]') or 'y'
        if response.lower() == 'y':
            fro = run_preprocessing(fro, segmentationList, **kwargs)
        else:
            print('No action taken. Returning')
            return fro
         
    fro = img_stack_segment(fro, segmentationList)
    return fro

def sort_images(fro: FrameObject, verbose: bool):
    if hasattr(fro, 'openFrames') and hasattr(fro, 'openedFrameNums'):
        indSort = np.argsort(fro.openedFrameNums)
        fro.openedFrameNums = fro.openedFrameNums[indSort]
        fro.openFrames = fro.openFrames[indSort]
        if verbose:
            print('INFO: Raw Images have been sorted')
    else:
        print('WARNING: Opened Frames is not sorted. Issues may exist!')
    
    if hasattr(fro, 'procFrames') and hasattr(fro, 'procFrameNums'):
        indSort = np.argsort(fro.procFrameNums)
        fro.procFrameNums = fro.procFrameNums[indSort]
        fro.procFrames = fro.procFrames[indSort]
        if verbose:
            print('INFO: Processed Images have been sorted')
    elif verbose:
        print('WARNING: Processed frames do not exist. They were not sorted')

    if hasattr(fro, 'segFrames') and hasattr(fro, 'segFrameNums'):
        indSort = np.argsort(fro.segFrameNums)
        fro.segFrameNums = fro.segFrameNums[indSort]
        fro.segFrames = fro.segFrames[indSort]
        if verbose:
            print('INFO: Segmented Images have been sorted')
    elif verbose:
        print('WARNING: Segmented frames do not exist. They were not sorted')
    
    return fro

def save_proc_img(fro: FrameObject, folderTitle: str = 'processedImages', fileType: str = '.tif'):
    fileFolder = os.path.join(fro.files.basePath, folderTitle)
    os.makedirs(fileFolder, exist_ok=True)
    procFrameNums = fro.procFrameNums
    procFrames = fro.procFrames
    for i in range(len(procFrameNums)):
        file_i = os.path.join(fileFolder, f'proccessedImage_{procFrameNums[i]}' + fileType)
        img_i = Image.fromarray((255*procFrames[i]).astype(np.uint8), 'L')
        img_i.save(file_i)
    
def save_seg_img(fro: FrameObject, folderTitle: str = 'segmentedImages', fileType: str = '.tif'):
    fileFolder = os.path.join(fro.files.basePath, folderTitle)
    os.makedirs(fileFolder, exist_ok=True)
    segFrameNums = fro.segFrameNums
    segFrames = fro.segFrames
    for i in range(len(segFrameNums)):
        file_i = os.path.join(fileFolder, f'segmentatedImage_{segFrameNums[i]}' + fileType)
        img_i = Image.fromarray((255*segFrames[i]).astype(np.uint8), mode='L')
        img_i.save(file_i)


