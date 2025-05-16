import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

from glob import glob

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib_scalebar.scalebar import ScaleBar
import rioxarray as rxr
import rasterio as rio
from rasterio.crs import CRS
from osgeo import gdal
from shapely.geometry import box
import geopandas as gpd
import datetime

import earthpy.plot as ep
import cartopy
import cartopy.mpl.geoaxes
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon
import contextily as cx

from raster_class_viz.scripts.gee_seasonal_jrc_download import download_seasonal_jrc_imgs
from raster_class_viz.scripts.gee_sentinel2_download import download_s2_imgs
from raster_class_viz.scripts.geetasks import check_on_tasks_in_queue, wait_for_local_sync
from raster_class_viz.scripts.calculate_classes import calc_classes
from raster_class_viz.scripts.rstr_tools import gdal_merge_compressed, reproj

# from gee_seasonal_jrc_download import download_seasonal_jrc_imgs
# from gee_sentinel2_download import download_s2_imgs
# from geetasks import check_on_tasks_in_queue, wait_for_local_sync
# from calculate_classes import calc_classes
# from rstr_tools import gdal_merge_compressed, reproj

# from cli import parse_viz_floods

def get_scalebar_dist(rxr_crs:int):
    POINTS = gpd.GeoSeries(
        [Point(-73.5, 40.5), Point(-74.5, 40.5)], crs=4326
    )  # Geographic WGS 84 - degrees

    POINTS = POINTS.to_crs(rxr_crs)  # Projected WGS 84 - meters

    dist_meters = POINTS[0].distance(POINTS[1])
    return dist_meters


def get_bounds(class_src_arr):

    crs_wgs84 = CRS.from_string('EPSG:4326')
    arr_wgs84 = class_src_arr.rio.reproject(crs_wgs84, nodata=255)

    lonmin, latmin, lonmax, latmax = arr_wgs84.rio.bounds()
    del arr_wgs84

    return lonmin, latmin, lonmax, latmax 


def add_basemap(class_src_arr, ax):

    cx.add_basemap(ax, crs=class_src_arr.rio.crs.to_string(), source=cx.providers.NASAGIBS.ASTER_GDEM_Greyscale_Shaded_Relief, alpha=1)
    cx.add_basemap(ax, crs=class_src_arr.rio.crs.to_string(), source=cx.providers.CartoDB.PositronNoLabels, alpha=0)
    cx.add_basemap(ax, crs=class_src_arr.rio.crs.to_string(), source=cx.providers.CartoDB.PositronOnlyLabels, zoom=10)

    return ax


def add_scalebar_Narrow(ax):
    # Add scalebar
    ax.add_artist(ScaleBar(dx=1, location='lower right', 
                           box_alpha=0, border_pad = 0, 
                           bbox_to_anchor=(1.3, 0.07),
                           bbox_transform=ax.transAxes))
    ax.set_aspect(1)

    # Add N arrow
    x, y, arrow_length = 1.4, 0.2, 0.1
    ax.annotate('N', xy=(x, y), xytext=(x, y-arrow_length),
                arrowprops=dict(arrowstyle='fancy', facecolor='black'),# width=5, headwidth=15),
                ha='center', va='center', fontsize=26,
                xycoords=ax.transAxes)
    return ax


def add_location_inset(class_src_arr, ax):
    """ use cartopy to plot the region (defined as a namedtuple object)
    """
    lonmin, latmin, lonmax, latmax = get_bounds(class_src_arr)

    axins = inset_axes(ax, width=2.5, height=2.5,  
                           bbox_to_anchor=(1.5, 1),
                           bbox_transform=ax.transAxes,
                    axes_class=cartopy.mpl.geoaxes.GeoAxes, 
                    axes_kwargs=dict(projection=cartopy.crs.PlateCarree()))
    
    axins.set_extent([lonmin-12, lonmax+12, latmin-12, latmax+12])

    # Put a background image on for nice sea rendering.
    axins.stock_img()
    # SOURCE = 'Natural Earth'
    # LICENSE = 'public domain'

    # axins.add_feature(cfeature.LAND)
    axins.add_feature(cfeature.COASTLINE)
    axins.add_feature(cfeature.BORDERS, linestyle=':')

    # Create a Rectangle patch
    # create a sample polygon, `pgon`
    pgon = Polygon(((lonmin, latmin),
            (lonmin, latmax),
            (lonmax, latmax),
            (lonmax, latmin),
            (lonmin, latmin)))

    # Add the patch to the Axes
    axins.add_geometries([pgon], crs=ccrs.PlateCarree(), facecolor='black', edgecolor='black', alpha=0.5)

    axins.add_feature(cartopy.feature.COASTLINE)

    return ax



def plot_flood_permanent_seasonal(class_path:Path, false_color:str='', true_color:str=''):

    img_path = f'./raster_class_viz/imgs/{os.path.basename(class_path)[:-4]}.png'
    if os.path.exists(img_path):
        print(f'{os.path.basename(img_path)} exists.')
        # return

    class_labels = ['Non-water', 'Permanent Water', 'Seasonal Water', 'Flood Water', 'No Data']

    class_src_arr = rxr.open_rasterio(class_path, masked=True).squeeze()

    # Plot data using nicer colors
    colors = ['#abafb0', '#002b9c', '#7494e4', '#47eeff', 'black']
    class_bins = [-0.5, 0.5, 1.5, 2.5, 3.5, 256]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(class_bins, 
                        len(colors))
    rgba_lin = cmap(np.arange(cmap.N))
    rgba_lin[:,-1] = [0, 1, 1, 1, 1]
    cmap_alpha = ListedColormap(rgba_lin)

    # Plot newly classified and masked raster
    if (false_color and true_color):                # both additional images
        img_src_arr = rxr.open_rasterio(true_color, masked=True).squeeze()
        f, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(19.5, 13), constrained_layout=True)
        ep.plot_rgb(img_src_arr.values,
            rgb=[2, 1, 0],
            ax=ax1,
            title="True Color",
            stretch=True,
            str_clip=5) 
        ep.plot_rgb(img_src_arr.values,
            rgb=[3, 2, 1],
            ax=ax2,
            title="False Color",
            stretch=True,
            str_clip=5) 
    elif false_color:                               # false color additional images
        img_src_arr = rxr.open_rasterio(false_color, masked=True).squeeze()
        f, (ax2, ax3) = plt.subplots(1, 2, figsize=(14, 13), constrained_layout=True)
        ep.plot_rgb(img_src_arr.values,
            rgb=[3, 2, 1],
            ax=ax2,
            title="False Color",
            stretch=True,
            str_clip=5) 
    elif true_color:                                # true color additional images
        img_src_arr = rxr.open_rasterio(true_color, masked=True).squeeze()
        f, (ax1, ax3) = plt.subplots(1, 2, figsize=(14, 13), constrained_layout=True)
        ep.plot_rgb(img_src_arr.values,
            rgb=[2, 1, 0],
            ax=ax1,
            title="True Color",
            stretch=True,
            str_clip=5) 
    elif not (false_color and true_color):          # no additional images
        f, ax3 = plt.subplots(figsize=(11, 7.55))

    im = class_src_arr.plot.imshow(cmap=cmap_alpha,
                            norm=norm,
                            add_colorbar=False,
                            ax=ax3)
    
    # add basemap
    ax3 = add_basemap(class_src_arr, ax3)
    
    im = class_src_arr.plot.imshow(cmap=cmap_alpha,
                            norm=norm,
                            add_colorbar=False,
                            ax=ax3)
    
    # add scalebar and North arrow
    ax3 = add_scalebar_Narrow(ax3)
    
    # Add legend using earthpy
    ep.draw_legend(im,
                titles=class_labels[0:5],
                classes=[0,1,2,3,4],
                bbox=(1.08, 0.5))
    
    # add title
    ax3.set(title="Classified Floodwater")

    # Add inset
    ax3 = add_location_inset(class_src_arr, ax3)

    ax3.set_axis_off()
    plt.savefig(img_path, dpi=300, format='png', )
    plt.close(f)
    # plt.show()

    return


def plot_flood_permanent(class_path:Path, false_color:str='', true_color:str=''):

    img_path = f'./raster_class_viz/imgs/{os.path.basename(class_path)[:-4]}.png'
    if os.path.exists(img_path):
        print(f'{os.path.basename(img_path)} exists.')
        # return

    class_labels = ['Non-water', 'Permanent +\nSeasonal Water', 'Flood Water', 'No Data']

    class_src_arr = rxr.open_rasterio(class_path, masked=True).squeeze()

    # Plot data using nicer colors
    colors = ['#abafb0', '#002b9c', '#47eeff', 'black']
    class_bins = [-0.5, 0.5, 2.5, 3.5, 256]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(class_bins, 
                        len(colors))
    rgba_lin = cmap(np.arange(cmap.N))
    rgba_lin[:,-1] = [0, 1, 1, 1]
    cmap_alpha = ListedColormap(rgba_lin)

    # Plot newly classified and masked raster
    if (false_color and true_color):                # both additional images
        img_src_arr = rxr.open_rasterio(true_color, masked=True).squeeze()
        f, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(19.5, 13), constrained_layout=True)
        ep.plot_rgb(img_src_arr.values,
            rgb=[2, 1, 0],
            ax=ax1,
            title="True Color",
            stretch=True,
            str_clip=5) 
        ep.plot_rgb(img_src_arr.values,
            rgb=[3, 2, 1],
            ax=ax2,
            title="False Color",
            stretch=True,
            str_clip=5) 
    elif false_color:                               # false color additional images
        img_src_arr = rxr.open_rasterio(false_color, masked=True).squeeze()
        f, (ax2, ax3) = plt.subplots(1, 2, figsize=(14, 13), constrained_layout=True)
        ep.plot_rgb(img_src_arr.values,
            rgb=[3, 2, 1],
            ax=ax2,
            title="False Color",
            stretch=True,
            str_clip=5) 
    elif true_color:                                # true color additional images
        img_src_arr = rxr.open_rasterio(true_color, masked=True).squeeze()
        f, (ax1, ax3) = plt.subplots(1, 2, figsize=(14, 13), constrained_layout=True)
        ep.plot_rgb(img_src_arr.values,
            rgb=[2, 1, 0],
            ax=ax1,
            title="True Color",
            stretch=True,
            str_clip=5) 
    elif not (false_color and true_color):          # no additional images
        f, ax3 = plt.subplots(figsize=(11, 7.55))

    im = class_src_arr.plot.imshow(cmap=cmap_alpha,
                            norm=norm,
                            add_colorbar=False,
                            ax=ax3)
    
    # add basemap
    ax3 = add_basemap(class_src_arr, ax3)
    
    im = class_src_arr.plot.imshow(cmap=cmap_alpha,
                            norm=norm,
                            add_colorbar=False,
                            ax=ax3)
    
    # add scalebar and North arrow
    ax3 = add_scalebar_Narrow(ax3)
    
    # Add legend using earthpy
    ep.draw_legend(im,
                titles=class_labels[0:4],
                classes=[0,1,2,3],
                bbox=(1.08, 0.5))
    
    # add title
    ax3.set(title="Classified Floodwater")

    # Add inset
    ax3 = add_location_inset(class_src_arr, ax3)

    ax3.set_axis_off()
    plt.savefig(img_path, dpi=300, format='png', )
    plt.close(f)
    # plt.show()

    return


def move_gsw_tif(src:str, dst:str):
    '''
        Move GSW .tif data from base drive GSWE_HLS folder to FloodViz/raster_class_viz/data/GSWE_HLS directory
    '''
    src_path = Path(src)
    dst_path = Path(dst)
    os.rename(src_path, dst_path)
    return

def make_dirs():
    if not os.path.exists('./raster_class_viz/data/GSWE_HLS'):
        os.makedirs('./raster_class_viz/data/GSWE_HLS')
    
    if not os.path.exists('./raster_class_viz/data/CLASS'):
        os.makedirs('./raster_class_viz/data/CLASS')
    
    if not os.path.exists('./raster_class_viz/imgs'):
        os.makedirs('./raster_class_viz/imgs')

    return


def get_gee_img_reproj(img_name, rstr_path, fld_date, gdrive, dataset):
    '''
        Download and reproject images from GEE (e.g., GSW or S2 imagery)
    '''

    try:
        img_path = glob(f'./raster_class_viz/data/{dataset}/reprojected/{img_name}_*_{dataset}_reproj.tif')[0]
    except IndexError:
        try:
            fld_src_arr = rxr.open_rasterio(rstr_path, masked=True).squeeze()
            img_path = glob(f'./raster_class_viz/data/{dataset}/{img_name}_*_{dataset}.tif')[0]
        except IndexError:
        # if not os.path.exists(img_path):
            crs_wgs84 = CRS.from_string('EPSG:4326')
            fld_reproj = fld_src_arr.rio.reproject(crs_wgs84, nodata=255)
            bounds = fld_reproj.rio.bounds()

            if dataset == 'GSW':
                task, img_path, date_info = download_seasonal_jrc_imgs(flood_date=fld_date, bounds=bounds, dt_set=dataset, img_name=img_name)#, tile=tile)
            elif dataset == 'S2':
                tile = rstr_path.split('.')[3][1:] # for when we have the tile name in the image path. will need to be updated
                date_end = (datetime.datetime.strptime(fld_date, "%Y-%m-%d") + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                task, n_imgs, img_path_lst = download_s2_imgs(date_start=fld_date, date_end=date_end, bounds=bounds, dt_set=dataset, img_name=img_name, hls_tiles=[tile])
                img_path = 'S2/' + img_path_lst[0]

            check_on_tasks_in_queue([task])
            wait_for_local_sync(f'{gdrive}/{img_path}.tif')

            dwnld_path_lst = glob(f'{gdrive}/{img_path}*.tif')
            if len(dwnld_path_lst) > 1:
                gdal_merge_compressed(f'{gdrive}/{img_path}.tif', dwnld_path_lst)

            move_gsw_tif(src=f'{gdrive}/{img_path}.tif', dst=f'./raster_class_viz/data/{img_path}.tif')
            img_path = glob(f'./raster_class_viz/data/{dataset}/{img_name}_*_{dataset}.tif')[0]
        
        img_path = reproj(fld_rstr=fld_src_arr, gswe_path=img_path, dataset='S2')

    return img_path


def raster_class_plot(
        input_dir:Path, 
        seasonal:bool, 
        gdrive:Path,
        false_color:bool,
        true_color:bool,
        n:int
        ):

    # args = parse_viz_floods()

    # input_dir = args.input_dir        # directory with classified imagery
    # seasonal = args.seasonal          # True/False
    # gdrive = args.gdrive              # Google Drive base path (e.g., 'Q:/My Drive')
    # false_color = args.false_color    # True/False
    # true_color = args.true_color      # True/False
    # n = args.number                   # Number of images to loop through in the FOR loop
    # gdrive = 'Q:/My Drive' # basepath for local GDrive
    # false_color = True
    # true_color = True

    make_dirs()

    # flood_fl_lst = glob('Q:/.shortcut-targets-by-id/1-Owv0cvb_maGj6CjU3lJDrnx_wofctRz/flood_examples_mollie/*/*.tif')
    # input_dir = 'Q:/.shortcut-targets-by-id/1iXFDnM6JEC6f0gm4-HjYgreTPUJc6Rat/selected_flood_results_vini_backup'
    # flood_fl_lst = glob(f'{input_dir}/**/*.json', recursive=True)

    flood_rstr_lst = glob(f'{input_dir}/**/*.tif', recursive=True)
    flood_fl_lst = [glob(f'{os.path.dirname(os.path.dirname(i))}/*.json') for i in flood_rstr_lst]

    for i in range(len(flood_fl_lst)):
        if i > n:
            print(f'{n} images rendered.')
            return
        rstr_path = flood_rstr_lst[i]
        try:
            fl = flood_fl_lst[i][0]
        except IndexError:
            print(f'missing corresponding .json for {os.path.basename(os.path.dirname(os.path.dirname(rstr_path)))}')
            continue

        with open(fl) as json_data:
            data = json.load(json_data)
        img_name = data['id']
        fld_date = data['properties']['datetime'].split('T')[0]
        # bounds = data['bbox']
        
        gswe_path = get_gee_img_reproj(img_name, rstr_path, fld_date, gdrive, 'GSW')

        if (false_color or true_color):
            img_path = get_gee_img_reproj(img_name, rstr_path, fld_date, gdrive, 'S2')

        with rio.open(gswe_path) as src:
            profile = src.profile

        calc_classes('HLS', img_name, './raster_class_viz/data/CLASS/', profile, rstr_path, gswe_path)

        if seasonal:
            if false_color and true_color:
                plot_flood_permanent_seasonal(class_path=Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'), false_color=img_path, true_color=img_path)
            elif false_color:
                plot_flood_permanent_seasonal(class_path=Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'), false_color=img_path)
            elif true_color:
                plot_flood_permanent_seasonal(class_path=Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'), true_color=img_path)
            else:
                plot_flood_permanent_seasonal(class_path=Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'))

        else:
            if false_color and true_color:
                plot_flood_permanent(class_path=Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'), false_color=img_path, true_color=img_path)
            elif false_color:
                plot_flood_permanent(class_path=Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'), false_color=img_path)
            elif true_color:
                plot_flood_permanent(class_path=Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'), true_color=img_path)
            else:
                plot_flood_permanent(class_path=Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'))

    return
