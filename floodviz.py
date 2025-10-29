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

import matplotlib.image as img 
import matplotlib.pyplot as plt

from cli import parse_viz_script
from raster_class_viz.scripts.viz_floods import raster_class_plot
from emdat_dfo_viz.scripts.emdat_dfo import plot_flood_freq



def main():

    args = parse_viz_script()

    script = args.script
    input_dir = args.input_dir        # directory with classified imagery
    seasonal = args.seasonal          # True/False
    gdrive = args.gdrive              # Google Drive base path (e.g., 'Q:/My Drive')
    false_color = args.false_color    # True/False
    true_color = args.true_color      # True/False
    n = args.number                   # Number of images to loop through in the FOR loop
    h = args.hexbin                   # True/False to add a hexbin plot to the classification figure.

    print(f'script: {script}\ntype: {type(script)}')

    if script == 'raster_class':
        print(f'  input_dir: {input_dir}\ttype: {type(input_dir)}')
        print(f'   seasonal: {seasonal}\ttype: {type(seasonal)}')
        print(f'     gdrive: {gdrive}\ttype: {type(gdrive)}')
        print(f'false_color: {false_color}\ttype: {type(false_color)}')
        print(f' true_color: {true_color}\ttype: {type(true_color)}')
        print(f'          n: {n}\t\ttype: {type(n)}')
        print(f'     hexbin: {h}\ttype: {type(h)}')


        # except:
        raster_class_plot(input_dir, seasonal, gdrive, false_color, true_color, n, h)
    
    elif script == 'flood_freq':
        # try:
        img_path = plot_flood_freq()
        
        # reading png image file 
        im = img.imread(img_path) 
        
        # show image 
        plt.imshow(im)
        plt.axis('off')
        plt.show()
        # except:
    
    return    


if __name__ == '__main__':
    main()