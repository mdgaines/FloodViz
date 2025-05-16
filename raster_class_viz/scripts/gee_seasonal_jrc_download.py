# copy of seasonal_water_jrc.py from master branch on 7/21/2023

import os
import ee

# from .timeout_decorator import timeout
# from tenacity import retry, stop_after_attempt, wait_fixed

ee.Initialize()


# Modified from WorldFloods GitHub:
# https://github.com/spaceml-org/ml4floods/blob/main/ml4floods/data/ee_download.py
def _get_collection(collection_name, date_start, bounds, season=True):
    collection = ee.ImageCollection(collection_name)
    if season:
        yr = int(date_start[:4])
        mnth = int(date_start[5:])
        if mnth < 12:
            collection_filtered = collection.filter(
                ee.Filter.calendarRange(
                    mnth, mnth+2, 'month')).filter(
                ee.Filter.calendarRange(
                    yr-2, yr-1, 'year')).filterBounds(bounds)
        # yr-2,yr-1 to look at the two years before the current flood
        else:  # for winter floods
            filtered_col_1 = collection.filter(
                             ee.Filter.calendarRange(12, 2, 'month')).filter(
                             ee.Filter.calendarRange(yr-1, yr-1, 'year')).filterBounds(
                             bounds)
            filtered_col_2 = collection.filter(
                             ee.Filter.calendarRange(1, 2, 'month')).filter(
                             ee.Filter.calendarRange(yr, yr, 'year')).filterBounds(
                             bounds)
            filtered_col_3 = collection.filter(
                             ee.Filter.calendarRange(12, 12, 'month')).filter(
                             ee.Filter.calendarRange(yr-2, yr-2, 'year')).filterBounds(
                             bounds)
            merged_filtered_col = filtered_col_1.merge(filtered_col_2)
            collection_filtered = merged_filtered_col.merge(filtered_col_3)
        n_images = int(collection_filtered.size().getInfo())
        return collection_filtered, n_images
    else:
        collection_filtered = collection.filterDate(date_start).filterBounds(bounds)

        n_images = int(collection_filtered.size().getInfo())
        return collection_filtered.first(), n_images


# @retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
# @timeout(15)
def download_seasonal_jrc_imgs(flood_date: str, bounds: tuple,
                               collection_name: str = "JRC/GSW1_4/MonthlyHistory",
                               dt_set: str = '', img_name: str = '',
                               tile=None, monthly=False):
    '''
        Use GEE Python API to batch download JRC images
    '''
    dt_set_fldr = {
        'world_floods': 'JRC_WORLDFLOODS',
        'sen1_floods11': 'JRC_SEN1FLOODS11',
        'usgs': 'JRC_usgs',
        'unosat': 'JRC_unosat',
        'HLS' : 'GSWE_HLS',
        'S2' : 'GSW_S2',
        'GSW' : 'GSW'
    }
    fldr = dt_set_fldr.get(dt_set)
    if dt_set == 'unosat':
        aoi = list(bounds.bounds.values)[0]
        bounds = ee.Geometry.BBox(aoi[0], aoi[1], aoi[2], aoi[3])
    elif (dt_set == 'HLS') or (dt_set == 'S2') or (dt_set == 'GSW'):
        bounds = ee.Geometry.BBox(bounds[0], bounds[1], bounds[2], bounds[3])
    # flood_date is in YYYY-MM-DD format
    flood_yr = flood_date[:4]
    flood_month = flood_date[5:7]
    if int(flood_yr) > 2021:
        flood_yr = '2021'
    yr_2_prev = str(int(flood_yr) - 2)
    yr_1_prev = str(int(flood_yr) - 1)

    # yearly permanent
    img_2_prev_yr, n_images_col_2 = _get_collection(collection_name='JRC/GSW1_4/YearlyHistory',
                                                    date_start=yr_2_prev, bounds=bounds, season=False)
    img_1_prev_yr, n_images_col_1 = _get_collection(collection_name='JRC/GSW1_4/YearlyHistory',
                                                    date_start=yr_1_prev, bounds=bounds, season=False)
    # (no data, not water, seasonal, permanent)
    jrc_2_prev_yr = img_2_prev_yr.remap([0, 1, 2, 3], [3, 0, 0, 1], 5)
    jrc_1_prev_yr = img_1_prev_yr.remap([0, 1, 2, 3], [3, 0, 0, 1], 5)

    jrc_sum_prev_yr = jrc_2_prev_yr.add(jrc_1_prev_yr)

    jrc_yearly_perm = jrc_sum_prev_yr.remap([2, 4], [2, 2], 0)

    if monthly:
        date_2_prev = '-'.join([yr_2_prev, flood_month])
        date_1_prev = '-'.join([yr_1_prev, flood_month])
        img_2_prev, n_images_col_2 = _get_collection(collection_name, date_2_prev, bounds, season=False)
        img_1_prev, n_images_col_1 = _get_collection(collection_name, date_1_prev, bounds, season=False)
        if (n_images_col_2 + n_images_col_1) <= 0:
            print(f"Not images found for collection {collection_name} flood date: {flood_date}")
        # (no data, not water, water)
        jrc_2_prev = img_2_prev.remap([0, 1, 2], [3, 0, 1], 5)
        jrc_1_prev = img_1_prev.remap([0, 1, 2], [3, 0, 1], 5)
        jrc_sum_prev = jrc_1_prev.add(jrc_2_prev)
        jrc_monthly = jrc_sum_prev.remap([2, 4], [1, 1], 0)
        jrc_monthly_perm_sum = jrc_monthly.add(jrc_yearly_perm)
        jrc_monthly_perm = jrc_monthly_perm_sum.remap([1, 2, 3], [1, 2, 2], 0).clip(bounds).int()
        date_info = ''.join([flood_yr, flood_month])
        if dt_set == 'unosat':
            jrc_name = f'{img_name}_{date_info}_{tile}_Monthly_JRC'
        else:
            jrc_name = f'{img_name}_{date_info}_Monthly_JRC'
        print('before  task = ee.batch.Export.image.toDrive( jrc_monthly_perm,')              
        task = ee.batch.Export.image.toDrive(
                jrc_monthly_perm,
                folder=fldr,
                # description = f'{img_name}_{date_info}_Monthly_JRC',
                description=jrc_name,
                # namePattern= f'{img_name}_{date_info}_JRC',
                scale=10,
                # dataType ='int',
                region=bounds,
                maxPixels=1e13,
                fileFormat="GeoTIFF"
            )
        task.start()
        print('after  task = ee.batch.Export.image.toDrive( jrc_monthly_perm,')
    else:
        flood_month = int(flood_month)
        # set season
        if flood_month >= 3 and flood_month < 6:  # spring
            season_mnth = '3'
        elif flood_month >= 6 and flood_month < 9:  # summer
            season_mnth = '6'
        elif flood_month >= 9 and flood_month < 12:  # fall
            season_mnth = '9'
        elif flood_month <= 2 or flood_month == 12:  # winter
            season_mnth = '12'
        date_y_m = '-'.join([flood_yr, season_mnth])
        # go with > 0.67
        img_col_all, n_images_col_tile = _get_collection(collection_name, date_y_m, bounds)

        def water_remapper(img):
            return img.remap([2], [1], 0)

        def nonna_remapper(img):
            return img.remap([1, 2], [1, 1], 0)

        water_col = img_col_all.map(water_remapper)  # img_col_all.remap([2],[1],0)#.sum()
        water_img = water_col.sum()
        non_na_col = img_col_all.map(nonna_remapper)  # .remap([1,2],[1],0).sum()
        non_na_img = non_na_col.sum()
        fr = water_img.divide(non_na_img).multiply(100).int()
        print('before  from_lst = ee.List.sequence(0, 66)')
        from_lst = ee.List.sequence(0, 66)
        to_lst = ee.List.sequence(0, 0, 1, 67)
        print('after  from_lst = ee.List.sequence(0, 66)')        
        jrc_seasonal = fr.remap(from_lst, to_lst, 1).clip(bounds).int()
        jrc_seasonal_perm_sum = jrc_seasonal.add(jrc_yearly_perm)
        jrc_seasonal_perm = jrc_seasonal_perm_sum.remap([1, 2, 3], [1, 2, 2], 0).clip(bounds).int()
        date_info = ''.join([flood_yr, season_mnth])
        if dt_set == 'unosat':
            jrc_name = f'{img_name}_{date_info}_{tile}_Seasonal_JRC'
        else:
            jrc_name = f'{img_name}_{date_info}_Seasonal_GSW'
        print('before  task = ee.batch.Export.image.toDrive( jrc_seasonal_perm,')

        task = ee.batch.Export.image.toDrive(
                jrc_seasonal_perm,
                folder=fldr,
                # description = f'{img_name}_{date_info}_Seasonal_JRC',
                description=jrc_name,
                # namePattern= f'{img_name}_{date_info}_JRC',
                scale=10,
                # dataType ='int',
                region=bounds,
                maxPixels=1e13,
                fileFormat="GeoTIFF"
            )
        task.start()
        print('after  task = ee.batch.Export.image.toDrive( jrc_seasonal_perm,')

    return task, os.path.join(fldr, jrc_name), date_info