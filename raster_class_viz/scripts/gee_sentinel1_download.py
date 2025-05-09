import ee


# Modified from WorldFloods GitHub:
# https://github.com/spaceml-org/ml4floods/blob/main/ml4floods/data/ee_download.py
def _get_collection(collection_name, date_start, date_end, bounds, polarisation):
    collection = ee.ImageCollection(collection_name)
    collection_filtered = collection.filterDate(
                                     date_start, date_end
                                     ).filterBounds(
                                     bounds
                                     ).filter(
                                     ee.Filter.listContains('transmitterReceiverPolarisation', polarisation)
                                     ).filter(
                                     ee.Filter.eq('instrumentMode', 'IW')
                                     ).select(polarisation)
    n_images = int(collection_filtered.size().getInfo())
    return collection_filtered, n_images


def download_s1_imgs(date_start: str, date_end: str, bounds: ee.Geometry, dt_set: str, img_name: str,
                     collection_name: str = "COPERNICUS/S1_GRD", tile: str = ''):
    '''
        Use GEE API to batch download S1 images.
        Downloading VV and VH from IW
        Add a max of 2 days after date start
        Check how many floods we get/miss on the flood date
    '''

    dt_set_fldr = {
        'world_floods': 'S1_WORLDFLOODS',
        'sen1_floods11': 'S1_SEN1FLOODS11',
        'usgs': 'S1_usgs',
        'unosat': 'S1_unosat'
    }
    fldr = dt_set_fldr.get(dt_set)
    task_lst = []
    file_name_lst = []
    n_images_col_total = 0
    for polarisation in ['VV', 'VH']:
        img_col_all, n_images_col = _get_collection(collection_name, date_start, date_end,
                                                    bounds, polarisation)
        n_images_col_total += n_images_col
        if n_images_col <= 0:
            print(f"No images found for collection {collection_name} date start: {date_start} date end: {date_end}")
            # return(task_lst, n_images_col)
            continue
        collection_List = img_col_all.toList(img_col_all.size())
        for i in range(n_images_col):
            img = ee.Image(collection_List.get(i)).clip(bounds)
            date_info = (img.get('system:id').getInfo()).split('_')[5]
            orbit_info = img.get('orbitProperties_pass').getInfo()
            if tile != '':
                desc = f'{img_name}_{date_info}_{polarisation}_{orbit_info}_{tile}_S1'
            else:
                desc = f'{img_name}_{date_info}_{polarisation}_{orbit_info}_S1'
            # print('folder where S1 data is being dowloaded is ', fldr, pathlib.Path(fldr).resolve())
            print('folder where S1 data is being dowloaded is ', fldr)
            task = ee.batch.Export.image.toDrive(
                img,
                folder=fldr,
                description=desc,
                scale=10,
                # dataType ='float',
                region=bounds,
                maxPixels=1e13,
                fileFormat="GeoTIFF"
                # verbose=True
            )
            task.start()
            task_lst.append(task)
            file_name_lst.append(desc)
    print('s1 total:', n_images_col_total)
    return task_lst, n_images_col_total, file_name_lst
