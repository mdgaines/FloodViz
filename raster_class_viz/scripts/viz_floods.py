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

import earthpy.plot as ep
import geemap
from geemap import cartoee
import cartopy
import cartopy.mpl.geoaxes
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon
import contextily as cx

from raster_class_viz.scripts.gee_seasonal_jrc_download import download_seasonal_jrc_imgs
from raster_class_viz.scripts.geetasks import check_on_tasks_in_queue, wait_for_local_sync
from raster_class_viz.scripts.calculate_classes import calc_classes
# from gee_seasonal_jrc_download import download_seasonal_jrc_imgs
# from geetasks import check_on_tasks_in_queue, wait_for_local_sync
# from calculate_classes import calc_classes


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


# def plot_location(class_src_arr):
#     """ use cartopy to plot the region (defined as a namedtuple object)
#     """
#     lonmin, latmin, lonmax, latmax = get_bounds(class_src_arr)

#     ax = plt.axes(projection=ccrs.PlateCarree())
#     ax.set_extent([lonmin-12, lonmax+12, latmin-12, latmax+12])

#     # Put a background image on for nice sea rendering.
#     ax.stock_img()
#     # SOURCE = 'Natural Earth'
#     # LICENSE = 'public domain'

#     # ax.add_feature(cfeature.LAND)
#     ax.add_feature(cfeature.COASTLINE)
#     ax.add_feature(cfeature.BORDERS, linestyle=':')

#     # Create a Rectangle patch
#     # create a sample polygon, `pgon`
#     pgon = Polygon(((lonmin, latmin),
#             (lonmin, latmax),
#             (lonmax, latmax),
#             (lonmax, latmin),
#             (lonmin, latmin)))

#     # Add the patch to the Axes
#     ax.add_geometries([pgon], crs=ccrs.PlateCarree(), facecolor='lack', edgecolor='black', alpha=0.5)

#     plt.show()

#     return fig, ax



def plot_flood_permanent_seasonal(class_path:Path):

    img_path = f'./raster_class_viz/imgs/{os.path.basename(class_path)[:-4]}.png'
    if os.path.exists(img_path):
        print(f'{os.path.basename(img_path)} exists.')
        # return

    class_labels = ['Non-water', 'Permanent Water', 'Seasonal Water', 'Flood Water', 'No Data']

    # fld_src_arr = rxr.open_rasterio(rstr_path, masked=True).squeeze()
    class_src_arr = rxr.open_rasterio(class_path, masked=True).squeeze()
    class_arr_wm = class_src_arr.rio.reproject(CRS.from_string('EPSG:3857'), nodata=255) # reproject to Web Mercator for basemap
    rxr_crs = class_src_arr.rio.crs.to_epsg()
    dist_meters = get_scalebar_dist(rxr_crs)
    lonmin, latmin, lonmax, latmax = get_bounds(class_src_arr) # for inset map


    # Plot data using nicer colors
    colors = ['#FFabafb0', '#002b9c', '#7494e4', '#47eeff', 'black']
    class_bins = [-0.5, 0.5, 1.5, 2.5, 3.5, 256]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(class_bins, 
                        len(colors))
    rgba_lin = cmap(np.arange(cmap.N))
    rgba_lin[:,-1] = [0, 1, 1, 1, 1]
    cmap_alpha = ListedColormap(rgba_lin)

    # Plot newly classified and masked raster
    f, ax = plt.subplots(figsize=(11, 7.55))
    im = class_src_arr.plot.imshow(cmap=cmap_alpha,
                            norm=norm,
                            add_colorbar=False,
                            ax=ax)
    
    # add basemap
    cx.add_basemap(ax, crs=class_src_arr.rio.crs.to_string(), source=cx.providers.NASAGIBS.ASTER_GDEM_Greyscale_Shaded_Relief, alpha=0.5)
    cx.add_basemap(ax, crs=class_src_arr.rio.crs.to_string(), source=cx.providers.CartoDB.PositronNoLabels, alpha=0.5)
    cx.add_basemap(ax, crs=class_src_arr.rio.crs.to_string(), source=cx.providers.CartoDB.PositronOnlyLabels, zoom=10)
    
    im = class_src_arr.plot.imshow(cmap=cmap_alpha,
                            norm=norm,
                            add_colorbar=False,
                            ax=ax)
    
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
    
    # Add legend using earthpy
    ep.draw_legend(im,
                titles=class_labels[0:5],
                classes=[0,1,2,3,4],
                bbox=(1.08, 0.5))
    
    ax.set(title="Classified Floodwater")

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

    ax.set_axis_off()
    # plt.tight_layout()
    # plt.savefig(img_path, dpi=300, format='png', )
    # plt.close(f)
    plt.show()

    return


def plot_flood_permanent(class_path:Path):

    img_path = f'./raster_class_viz/imgs/{os.path.basename(class_path)[:-4]}.png'
    if os.path.exists(img_path):
        print(f'{os.path.basename(img_path)} exists.')
        # return

    class_labels = ['Non-water', 'Permanent + Seasonal Water', 'Flood Water', 'No Data']

    # fld_src_arr = rxr.open_rasterio(rstr_path, masked=True).squeeze()
    class_src_arr = rxr.open_rasterio(class_path, masked=True).squeeze()

    # Plot data using nicer colors
    colors = ['#abafb0', '#002b9c', '#47eeff', 'black']
    class_bins = [-0.5, 0.5, 2.5, 3.5, 256]
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
                titles=class_labels[0:4],
                classes=[0,1,2,3])
    
    ax.set(title="Classified Floodwater")
    ax.set_axis_off()
    plt.tight_layout()
    # plt.savefig(img_path, dpi=300, format='png', )
    # plt.close(f)
    plt.show()

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
    

def raster_class_plot(input_dir:Path):

    # args = parse_viz_floods()

    # input_dir = args.input_dir
    # seasonal = args.seasonal
    # gdrive = args.gdrive
    gdrive = 'Q:/My Drive' # basepath for local GDrive

    make_dirs()

    # flood_fl_lst = glob('Q:/.shortcut-targets-by-id/1-Owv0cvb_maGj6CjU3lJDrnx_wofctRz/flood_examples_mollie/*/*.tif')
    input_dir = 'Q:/.shortcut-targets-by-id/1iXFDnM6JEC6f0gm4-HjYgreTPUJc6Rat/selected_flood_results_vini_backup'
    # flood_fl_lst = glob(f'{input_dir}/**/*.json', recursive=True)

    flood_rstr_lst = glob(f'{input_dir}/**/*.tif', recursive=True)
    flood_fl_lst = [glob(f'{os.path.dirname(os.path.dirname(i))}/*.json') for i in flood_rstr_lst]

    for i in range(len(flood_fl_lst)):
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
                wait_for_local_sync(f'{gdrive}/{gswe_path}.tif')
                move_gsw_tif(src=f'{gdrive}/{gswe_path}.tif', dst=f'./raster_class_viz/data/{gswe_path}.tif')
                gswe_path = glob(f'./raster_class_viz/data/GSWE_HLS/{img_name}_*_JRC.tif')[0]

            gswe_path = reproj(fld_rstr=fld_src_arr, gswe_path=gswe_path)

        with rio.open(gswe_path) as src:
            profile = src.profile

        calc_classes('HLS', img_name, './raster_class_viz/data/CLASS/', profile, rstr_path, gswe_path)

        # if seasonal:
        plot_flood_permanent_seasonal(class_path=Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'))

        plot_flood_permanent(Path(f'./raster_class_viz/data/CLASS/HLS_{img_name}_CLASS.tif'))

    return
