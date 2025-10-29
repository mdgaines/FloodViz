import argparse
from pathlib import Path
from distutils.util import strtobool


# def parse_viz_floods():
#     '''
#         Parse the expected command-line arguments for viz_floods.py
#     '''
#     parser = argparse.ArgumentParser(description='Plots and saves images of classified flood events.')

#     # parser.add_help()

#     parser.add_argument('-in', '--input_dir', type=Path,
#                         # default='all',
#                         help='Input base path that has flood classified rasters of interest.')
    
#     parser.add_argument('-szn', '--seasonal', type=bool,
#                         default=True,
#                         help='Set to True for seasonal classification images.\nSet to False for annual classification images.')

#     parser.add_argument('-g', '--gdrive', type=Path,
#                         default='Q:/My Drive',
#                         help='Root Drive to your Desktop Google Drive')
    
#     parser.add_argument('-fc', '--false_color', type=bool,
#                         default=True,
#                         help='Display False Color image (True/False)')
    
#     parser.add_argument('-tc', '--true_color', type=bool,
#                         default=True,
#                         help='Display True Color image (True/False)')
    
#     parser.add_argument('-n', '--number', type=int,
#                         default=3,
#                         help='Number of images to loop through from input dir.')
    

#     return(parser.parse_args())



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
    

    parser.add_argument('-szn', '--seasonal', type=lambda x: bool(strtobool(x)),
                        default=True,
                        help='Set to True for seasonal classification images.\nSet to False for annual classification images.')

    parser.add_argument('-g', '--gdrive', type=Path,
                        default='Q:/My Drive',
                        help='Root Drive to your Desktop Google Drive.')
    
    parser.add_argument('-fc', '--false_color', type=lambda x: bool(strtobool(x)),
                        default=True,
                        help='Display False Color image (True/False).')
    
    parser.add_argument('-tc', '--true_color', type=lambda x: bool(strtobool(x)),
                        default=True,
                        help='Display True Color image (True/False).')
    
    parser.add_argument('-n', '--number', type=int,
                        default=3,
                        help='Number of images to loop through from input dir.')
    
    parser.add_argument('-hex', '--hexbin', type=lambda x: bool(strtobool(x)),
                        default=False,
                        help='Add hexbin plot to classification figure (True/False).')
    

    return(parser.parse_args())

