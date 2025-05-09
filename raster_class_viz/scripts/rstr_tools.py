import re
import os
import time
import warnings
from hashlib import sha256
from pathlib import Path

import pandas as pd
from osgeo import gdal
from osgeo import gdalconst
from rasterio.crs import CRS


def getFeatures(gdf):
    """Function to parse features from GeoDataFrame in such a manner that rasterio wants them"""
    import json
    return [json.loads(gdf.to_json())['features'][0]['geometry']]


def reproj(fld_rstr, gswe_path, dataset):

    img_name = os.path.basename(gswe_path)[:-4] + '_reproj.tif'
    out_path = f'./raster_class_viz/data/{dataset}/reprojected/{img_name}'
    
    fld_bounds = fld_rstr.rio.bounds()
    destCRS = CRS.from_string(f'EPSG:{fld_rstr.rio.crs.to_epsg(60)}')
    destRes = fld_rstr.rio.transform()[0]

    # bbox = box(fld_bounds[0], fld_bounds[1], fld_bounds[2], fld_bounds[3])
    # geo = gpd.GeoDataFrame({'geometry': bbox}, index=[0], crs=destCRS)
    # coords = getFeatures(geo)

    gswe_reproj = gdal.Warp(out_path, gswe_path, dstSRS=destCRS, 
                            xRes=destRes, yRes=destRes, 
                            outputBounds=fld_bounds, format='GTiff',
                            outputType=gdal.GDT_UInt16)
    
    gswe_reproj = None

    return out_path


def get_info_key(fp, key, findn=1):
    finfo = gdal.Info(fp)
    ftype = re.findall(rf'({key}\s?=\s?\w+)', finfo)
    ftype = [f.split('=')[1].strip() for f in ftype]
    if findn != 'all':
        ftype = ftype[:findn]
    return ftype

def get_tiff_type(fp):
    """Uses gdalinfo to retrieve the data type within the dataset located in the `fp` path."""
    ftypes = pd.unique(get_info_key(fp, 'Type', 'all'))
    if len(ftypes) > 1:
        warnings.warn(f'The file {fp} has more than one data type: {ftypes}. Using only the first one ({ftypes[0]}).')
    return ftypes[0]

def get_tiff_interleave(fp):
    return get_info_key(fp, 'INTERLEAVE')[0]


def get_tiff_descriptions(fp):
    return get_info_key(fp, 'Description', 'all')

def compress_tiff(fp, outfp=None, ftype=None, compress_method='LZW', interleave='BAND'):
    """Compresses a tiff file. Defaults to LZW. ZSTD requires GDAL >= 2.3.
        Uses gdal_translate: https://gdal.org/programs/gdal_translate.html
        GeoTiff creation options: https://gdal.org/drivers/raster/gtiff.html#creation-options
        """
    fp = str(fp)
    outfp = str(outfp) if outfp is not None else fp[:-4] + '_zstd.tif'

    ftype = ftype if ftype is not None else get_tiff_type(fp)

    if 'float' in ftype.lower():
        predictor = 3
    else:
        predictor = 2

    translate_options = gdal.TranslateOptions(format='GTiff', strict=True,
                                              creationOptions=[
                                                  'TFW=NO',
                                                  # 'COMPRESS=ZSTD',
                                                  f'COMPRESS={compress_method}',
                                                  f'INTERLEAVE={interleave}',
                                                  'NUM_THREADS=ALL_CPUS',
                                                  f'PREDICTOR={predictor}',
                                                  'ZSTD_LEVEL=15',
                                                  'TILED=YES',
                                              ])

    ds = gdal.Translate(outfp, fp, options=translate_options)
    ds = None
    return outfp



def gdal_merge_compressed(out_path, in_path, interleave=None, **kwargs):
    vrt = './raster_class_viz/data/temp.vrt'
    # g = gdal.Warp(vrt, in_path, **kwargs)
    vrt = gdal.BuildVRT(vrt, in_path, **kwargs)
    interleave = interleave if interleave is not None else get_tiff_interleave(in_path)
    compress_tiff(vrt, out_path,
                  ftype=get_tiff_type(in_path),
                  interleave=interleave,
                  )
    g = None
    gdal.Unlink(vrt)
    return out_path
