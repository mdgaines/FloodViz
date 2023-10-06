import argparse
from pathlib import Path



def parse_viz_floods():
    '''
        Parse the expected command-line arguments for viz_floods.py
    '''
    parser = argparse.ArgumentParser(description='Plots and saves images of classified flood events.')

    # parser.add_help()

    parser.add_argument('-in', '--input_dir', type=Path,
                        # default='all',
                        help='Input base path that has flood classified rasters of interest.')
    
    # parser.add_argument('-s', '--seasonal', type=bool,
    #                     default=True,
    #                     help='Set to True for seasonal classification images.\nSet to False for annual classification images.')

    # parser.add_argument('-o', '--out_dir', type=str,
    #                     default='../open_source_training/',
    #                     help='Output directory for where files will be saved.')
    # parser.add_argument('-p', '--path',
    #                     default=DOWNLOADED_IMG_PATH,
    #                     help='Path where the flood training datasets have been downloaded')

    return(parser.parse_args())



def parse_viz_script():
    '''
        Parse the expected command-line arguments for viz_floods.py
    '''
    parser = argparse.ArgumentParser(description='Plots and saves images of classified flood events.')

    # parser.add_help()

    parser.add_argument('-s', '--script', type=str,
                        # default='all',
                        help='Input the name of the flood visualizations you want. \
                            (raster_class OR flood_freq)')

    parser.add_argument('-in', '--input_dir', type=Path,
                        help='Input base path that has flood classified rasters of interest.')
    
    # parser.add_argument('-o', '--out_dir', type=str,
    #                     default='../open_source_training/',
    #                     help='Output directory for where files will be saved.')
    # parser.add_argument('-p', '--path',
    #                     default=DOWNLOADED_IMG_PATH,
    #                     help='Path where the flood training datasets have been downloaded')

    return(parser.parse_args())

