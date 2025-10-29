import os
from pathlib import Path

import numpy as np
import rasterio as rio


def calc_classes(dt_set: str, s2_name: str, out_dir: str, profile, gt_path=None, jrc_path=None, s2_path=None):
    """Calculate flood classifications and save the result to the output directory.
    Classification coding:
          0 - land/non-water
          1 - permanent water
          2 - seasonal water
          3 - flood
          9 - cloud
        255 - No data
    """
    # generate path for reprojected S2 image in the output directory
    out_path = os.path.join(out_dir, '_'.join([dt_set, s2_name, 'CLASS.tif']))
    if os.path.exists(out_path):
        print(f'\t{out_path} already exists.')
        # print('Running anyway')
        return
    if gt_path:
        with rio.open(gt_path) as src:
            gt = src.read(1).astype('int')
            # print('gt type:', type(gt[0]))
    else:
        print('No ground truth... exiting without bands.')
        return
    if s2_path: 
        with rio.open(s2_path) as src:
            s2 = src.read(1).astype('int')
    if not jrc_path:
        print(f'We are missing JRC Yearly and Seasonal data for {s2_name}...')
        return
    else:
        with rio.open(jrc_path) as src:
            jrc = src.read(1)
        if dt_set == 'world_floods':
            non_water = np.where(gt == 1, 0, 0)
            perm_water = np.where((gt == 2) & (jrc == 2), 1, 0)
            szn_water = np.where((gt == 2) & (jrc == 1), 2, 0)
            flood = np.where((gt == 2) & (jrc < 1), 3, 0)
            cloud = np.where(gt == 3, 9, 0)
            no_data = np.where(gt == 0, 255, 0)
            all_classes = non_water + perm_water + szn_water + flood + cloud + no_data
        elif dt_set == 'sen1_floods11':
            non_water = np.where(gt == 0, 0, 0)
            perm_water = np.where((gt == 1) & (jrc == 2), 1, 0)
            # dataset has its own jrc with only perm water
            szn_water = np.where((gt == 1) & (jrc == 1), 2, 0)
            flood = np.where((gt == 1) & (jrc < 1), 3, 0)
            no_data = np.where(gt == -1, 255, 0)
            all_classes = non_water + perm_water + szn_water + flood + no_data
        elif dt_set == 'usgs':
            non_water = np.where(gt == 2, 0, 0)
            perm_water = np.where((gt == 1) & (jrc == 2), 1, 0)
            szn_water = np.where((gt == 1) & (jrc == 1), 2, 0)
            flood = np.where((gt == 1) & (jrc < 1), 3, 0)
            cloud = np.where(gt == 4, 9, 0)
            no_data = np.where(gt == 0, 255, 0)
            all_classes = non_water + perm_water + szn_water + flood + cloud + no_data
        elif dt_set == 'unosat':
            perm_water = np.where((gt == 1) & (jrc == 2), 1, 0)
            szn_water = np.where((gt == 1) & (jrc == 1), 2, 0)
            flood = np.where((gt == 1) & (jrc < 1), 3, 0)
            no_data = np.where(gt == 0, 255, 0)
            all_classes = perm_water + szn_water + flood + no_data
        elif dt_set == 'S2':
            perm_water = np.where((gt == 2) & (jrc == 2), 1, 0)
            szn_water = np.where((gt == 2) & (jrc == 1), 2, 0)
            flood = np.where((gt == 2) & (jrc < 1), 3, 0)
            no_data = np.where(gt == 0, 255, 0)
            all_classes = perm_water + szn_water + flood + no_data
        elif dt_set == 'HLS':
            perm_water = np.where((gt == 2) & (jrc == 2), 1, 0)
            szn_water = np.where((gt == 2) & (jrc == 1), 2, 0)
            flood = np.where((gt == 2) & (jrc < 1), 3, 0)
            no_data = np.where((gt == 1) & (s2 == 0), 255, 0)
            all_classes = perm_water + szn_water + flood + no_data
        elif dt_set == 'floodsnet':
            perm_water = np.where((gt == 1) & (jrc == 2), 1, 0)
            szn_water = np.where((gt == 1) & (jrc == 1), 2, 0)
            flood = np.where((gt == 1) & (jrc < 1), 3, 0)
            no_data = np.where((gt == 0) & (s2 == 0), 255, 0)
            all_classes = perm_water + szn_water + flood + no_data

    # write classified raster to output directory
    profile.update(
        dtype='uint8',
        count=1,
        nodata=255,
        compress='lzw',
        interleave='band',
        blockxsize= 256, 
        blockysize= 256,
        tiled=True,
    )
    with rio.open(out_path, 'w', **profile) as dst:
        dst.write(all_classes.astype(np.uint8), 1)
        dst.set_band_description(1, 'CLASS')

    print(f'\t{out_path} saved.')
    return
