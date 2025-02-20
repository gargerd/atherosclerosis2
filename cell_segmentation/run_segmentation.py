#!/usr/bin/env python

from methods import segment_binning, segment_cellpose, segment_nuclei
import tifffile
from pyometiff import OMETIFFReader
import squidpy as sq
from scipy import ndimage
import skimage.io
import skimage.measure
import skimage.segmentation
import numpy as np
import argparse
import os
import torch 

if __name__ == '__main__':

    #Parse arguments
    parser = argparse.ArgumentParser(description='Segment DAPI images')
    parser.add_argument('-i', '--input', required=True, type=str, help='Input image file')
    parser.add_argument('-o', '--output', required=True, type=str, help='Output directory')
    parser.add_argument('-b', '--binary', action='store_true',
        help='If the input image is a segmented, binary image (e.g. watershed via ImageJ)')
    parser.add_argument('-s', '--segment', required=True, type=str,
        help='Segmentation method to be used')
    parser.add_argument('-id', '--id_code', required=True, type = str,
        help='ID of method to be used for saving')
    parser.add_argument('-p', '--hyperparams', default=None, type=str,
        help='Dictionary of hyperparameters') 
    parser.add_argument('-e', '--expand', default="0", type=str,
        help='Amount of pixels to expand each segment by- can be used to approximate cell boundary') 
    
    args = parser.parse_args()

    image_file = args.input
    output = args.output
    binary = args.binary
    segmentation_method = args.segment
    id_code = args.id_code
    hyperparams = eval(args.hyperparams)
    expand_nuclear_area = eval(args.expand)
    
       
    #Create output folder if needed
    if not os.path.exists(output):
        os.makedirs(output)

    #If unsegmented, segment image
    print('Running segmentation')
    if(not binary):
        if(segmentation_method == 'binning'):
            #img = tifffile.imread(image_file)
            reader=OMETIFFReader(fpath=image_file)
            img,metadata,xml_metadata=reader.read()
            if hyperparams is None or hyperparams['bin_size'] is None:
                img_arr=segment_binning(img, 20)
            else:
                img_arr = segment_binning(img, hyperparams['bin_size'])
        elif(segmentation_method=='cellpose'):
            img = tifffile.imread(image_file)
            reader=OMETIFFReader(fpath=image_file)
            img,metadata,xml_metadata=reader.read()

            #from cellpose import models, io
            #filename='/data/gpfs/projects/punim2121/Atherosclerosis/xenium_data/at3_1m4_01.tif'
            #img = io.imread(filename)
            #print((img))

            img_arr=segment_cellpose(img,hyperparams)
        else:
            img = sq.im.ImageContainer(image_file)
            if hyperparams is not None:
                segment_nuclei(img, layer = 'image', method=segmentation_method, **hyperparams)
            else:
                segment_nuclei(img, layer = 'image', method=segmentation_method)
            img_arr = img[f'segmented_{segmentation_method}'].to_numpy()[:,:,0,0]
        
    
    #If already segmented, label
    else:
        img_arr = skimage.io.imread(image_file)
        img_arr = skimage.measure.label(img_arr, connectivity=1)

    del img

    # Convert micrometers to pixels using the DAPI image pixel_width information from the .ome.tif file
    pixel_width_um=np.float32(metadata['PhysicalSizeX'])
    expand_nuclear_area=np.float32(int(expand_nuclear_area)/pixel_width_um)

    #  Expand nuclear area to reflect whole cell area
    print('Expanding nuclear area')
    if expand_nuclear_area is not None and expand_nuclear_area != 0:
        img_arr = skimage.segmentation.expand_labels(img_arr, distance=expand_nuclear_area)

    #Save as .tif file
    print('Saving segmented image')
    skimage.io.imsave(f'{output}/segments_{segmentation_method}-{id_code}.tif', img_arr)

    #Calculate and save areas
    (unique, counts) = np.unique(img_arr, return_counts=True)
    del img_arr
    areas = np.asarray((unique, counts)).T
    np.savetxt(f'{output}/areas_{segmentation_method}-{id_code}.csv', areas, delimiter=",")
    