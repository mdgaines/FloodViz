import ee

# from .timeout_decorator import timeout
# from tenacity import retry, stop_after_attempt, wait_fixed


# from WorldFloods GitHub https://github.com/spaceml-org/ml4floods/blob/main/ml4floods/data/ee_download.py
def _get_collection(collection_name, date_start, date_end, bounds, add_filter=False):
    collection = ee.ImageCollection(collection_name)
    if add_filter:
        collection_filtered = collection.filterDate(
                                         date_start, date_end
                                         ).filterBounds(
                                         bounds
                                         ).filterMetadata('MGRS_TILE', 'EQUALS', add_filter)
    else:
        collection_filtered = collection.filterDate(
                                         date_start, date_end
                                         ).filterBounds(bounds)
    n_images = int(collection_filtered.size().getInfo())
    return collection_filtered, n_images


def _make_gee_task(img, fldr, img_name, sys_id, bounds):
    task = ee.batch.Export.image.toDrive(
        img.select(['B2', 'B3', 'B4', 'B8']),
        folder=fldr,
        description=f'{img_name}_{sys_id}_S2',
        scale=10,
        # dataType ='float',
        region=bounds,
        maxPixels=1e13,
        fileFormat="GeoTIFF"
        # verbose=True
    )
    task.start()
    return task


def _s2_download(n_images_col_tile, collection_name, date_start, date_end, img_col_all, bounds, fldr, img_name, tile=''):

    task_lst = []
    file_name_lst = []
    if n_images_col_tile <= 0:
        print(f"No images found for collection {collection_name} date start: {date_start} date end: {date_end} tile: {tile}")
        return [], []

    collection_List = img_col_all.toList(img_col_all.size())
    for j in range(n_images_col_tile):
        img = ee.Image(collection_List.get(j)).clip(bounds).toInt()
        sys_id = img.get('system:id').getInfo().split('/')[-1]
        desc = f'{img_name}_{sys_id}_S2'  # output file name
        try:
            task = _make_gee_task(img, fldr, img_name, sys_id, bounds)
            task_lst.append(task)
            file_name_lst.append(desc)
        except:
            continue

    return task_lst, file_name_lst



def download_s2_imgs(date_start: str, date_end: str, bounds: ee.Geometry,
                     collection_name: str = "COPERNICUS/S2_HARMONIZED",
                     dt_set: str = '', img_name: str = '', hls_tiles=None):
    '''
        Use GEE Python API to batch download S2 images
            S2_HARMONIZED : S2 L1C data
                            After 2022-01-25, Sentinel-2 scenes with
                            PROCESSING_BASELINE '04.00' or above
                            have their DN (value) range shifted by 1000.
                            The HARMONIZED collection shifts
                            data in newer scenes to be in the same
                            range as in older scenes.
            S2_SR         : S2 L2A data
    '''
    dt_set_fldr = {
        'world_floods': 'S2_WORLDFLOODS',
        'sen1_floods11': 'S2_SEN1FLOODS11',
        'usgs': 'S2_usgs',
        'unosat': 'S2_unosat',
        'HLS' : 'S2_HLS',
        'S2' : 'S2'
    }
    if (dt_set == 'HLS') or (dt_set == 'S2'):
        bounds = ee.Geometry.BBox(bounds[0], bounds[1], bounds[2], bounds[3])
    fldr = dt_set_fldr.get(dt_set)
    if hls_tiles is None:
        img_col_all, n_images_col = _get_collection(collection_name, date_start, date_end, bounds)
        print('hls_tiles is None')
        task_lst, file_name_lst = _s2_download(n_images_col, collection_name, date_start, date_end, img_col_all, bounds, fldr, img_name)
        return task_lst, n_images_col, file_name_lst
    else:
        n_images_col = 0
        task_lst = []
        file_name_lst = []
        for i in range(len(hls_tiles)):
            tile = hls_tiles[i]
            img_col_all, n_images_col_tile = _get_collection(collection_name,
                                                             date_start,
                                                             date_end,
                                                             bounds,
                                                             add_filter=tile)
            task_lst_temp, file_name_lst_temp = _s2_download(n_images_col_tile, collection_name,
                                                             date_start, date_end, img_col_all,
                                                             bounds, fldr, img_name, tile)
            task_lst.extend(task_lst_temp)
            file_name_lst.extend(file_name_lst_temp)
            n_images_col += n_images_col_tile
        return task_lst, n_images_col, file_name_lst
