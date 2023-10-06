# Run with the below:
# python floodviz.py -s raster_class
# python floodviz.py -s flood_freq

# if not using the default folders, pls see cli.py for how to specify
# your folders; for example:


import os
# import json
# import pandas as pd
# import numpy as np
from pathlib import Path

from cli import parse_viz_script
from raster_class_viz.scripts.viz_floods import raster_class_plot



def main():

    args = parse_viz_script()

    script = args.script

    print(f'script: {script}\ntype: {type(script)}')

    if script == 'raster_class':
        if args.input_dir is None:
            input_dir = Path(input('Enter the directory that contains the flood classified rasters:'))
        else:
            input_dir = args.input_dir
        print(f'script: {input_dir}\ntype: {type(input_dir)}')

        # except:
        raster_class_plot(input_dir)


if __name__ == '__main__':
    main()