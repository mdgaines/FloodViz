import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

from glob import glob

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import rioxarray as rxr
import rasterio as rio
from rasterio.crs import CRS
from osgeo import gdal
from shapely.geometry import box
import geopandas as gpd


import earthpy.plot as ep

from raster_class_viz.scripts.gee_seasonal_jrc_download import download_seasonal_jrc_imgs
from raster_class_viz.scripts.geetasks import check_on_tasks_in_queue, wait_for_local_sync
from raster_class_viz.scripts.calculate_classes import calc_classes
# from cli import parse_viz_floods

def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


def reproj(fld_rstr, gswe_path):

    img_name = os.path.basename(gswe_path)[:-4] + '_reproj.tif'
    out_path = f'./raster_class_viz/data/GSWE_HLS/reprojected/{img_name}'
    
    fld_bounds = fld_rstr.rio.bounds()
    destCRS = CRS.from_string(f'EPSG:{fld_rstr.rio.crs.to_epsg(60)}')

    # bbox = box(fld_bounds[0], fld_bounds[1], fld_bounds[2], fld_bounds[3])
    # geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=destCRS)
    # coords = getFeatures(geo)

    gswe_reproj = gdal.Warp(out_path, gswe_path, dstSRS=destCRS, 
                            xRes=30, yRes=30, 
                            outputBounds=fld_bounds, format='GTiff',
                            outputType=gdal.GDT_UInt16)
    
    gswe_reproj = None

    return out_path



def plot_flood_permanent_seasonal(class_path:Path):

    img_path = f'./raster_class_viz/imgs/{os.path.basename(class_path)[:-4]}.png'
    if os.path.exists(img_path):
        print(f'{os.path.basename(img_path)} exists.')
        # return

    class_labels = ['Non-water', 'Permanent Water', 'Seasonal Water', 'Flood Water', 'No Data']

    # fld_src_arr = rxr.open_rasterio(rstr_path, masked=True).squeeze()
    class_src_arr = rxr.open_rasterio(class_path, masked=True).squeeze()

    # Plot data using nicer colors
    colors = ['#abafb0', '#002b9c', '#7494e4', '#47eeff', 'black']
    class_bins = [-0.5, 0.5, 1.5, 2.5, 3.5, 256]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(class_bins, 
                        len(colors))

    # Plot newly classified and masked raster
    f, ax = plt.subplots(figsize=(10, 7.55))
    im = class_src_arr.plot.imshow(cmap=cmap,
                            norm=norm,
                            add_colorbar=False)
    
    # Add legend using earthpy
    ep.draw_legend(im,
                titles=class_labels[0:4])
    
    ax.set(title="Classified Floodwater")
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(img_path, dpi=300, format='png', )
    plt.close(f)
    # plt.show()

    return


def plot_flood_permanent(fl_path:Path):

    return


def make_dirs():
    if not os.path.exists('./raster_class_viz/data/GSWE_HLS'):
        os.makedirs('./raster_class_viz/data/GSWE_HLS')
    
    if not os.path.exists('./raster_class_viz/data/CLASS'):
        os.makedirs('./raster_class_viz/data/CLASS')
    
    if not os.path.exists('./raster_class_viz/imgs'):
        os.makedirs('./raster_class_viz/imgs')

    return
    

def raster_class_plot(input_dir:Path):

    # args = parse_viz_floods()

    # input_dir = args.input_dir
    # seasonal = args.seasonal

    make_dirs()

    # flood_fl_lst = glob('G:/.shortcut-targets-by-id/1-Owv0cvb_maGj6CjU3lJDrnx_wofctRz/flood_examples_mollie/*/*.tif')
    # Q:/.shortcut-targets-by-id/1vBEdUNq5Muhbh7WU8S4us5iJy0ZGpw1B/selected_flood_results_vini
    flood_fl_lst = glob(f'{input_dir}/**/*.json', recursive=True)

    flood_rstr_lst = glob(f'{input_dir}/**/*.tif', recursive=True)

    for i in range(len(flood_fl_lst)):
        fl = flood_fl_lst[i]
        rstr_path = flood_rstr_lst[i]

        with open(fl) as json_data:
            data = json.load(json_data)
        img_name = data['id']
        fld_date = data['properties']['datetime'].split('T')[0]
        # bounds = data['bbox']
        try:
            gswe_path = glob(f'./raster_class_viz/data/GSWE_HLS/reprojected/{img_name}_*_JRC_reproj.tif')[0]
        except IndexError:
            try:
                fld_src_arr = rxr.open_rasterio(rstr_path, masked=True).squeeze()
                gswe_path = glob(f'./raster_class_viz/data/GSWE_HLS/{img_name}_*_JRC.tif')[0]
            except IndexError:
            # if not os.path.exists(gswe_path):
                crs_wgs84 = CRS.from_string('EPSG:4326')
                fld_reproj = fld_src_arr.rio.reproject(crs_wgs84, nodata=255)
                bounds = fld_reproj.rio.bounds()

                task, gswe_path, date_info = download_seasonal_jrc_imgs(flood_date=fld_date, bounds=bounds, dt_set='HLS', img_name=img_name)#, tile=tile)
                check_on_tasks_in_queue([task])
                wait_for_local_sync(f'./raster_class_viz/data{gswe_path}')
                gswe_path = glob(f'./raster_class_viz/data/GSWE_HLS/{img_name}_*_JRC.tif')[0]

            gswe_path = reproj(fld_rstr=fld_src_arr, gswe_path=gswe_path)

        with rio.open(gswe_path) as src:
            profile = src.profile

        calc_classes('HLS', img_name, './raster_class_viz/data/CLASS/', profile, rstr_path, gswe_path)

        # if seasonal:
        plot_flood_permanent_seasonal(Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'))

        plot_flood_permanent(Path(fl))

    return
