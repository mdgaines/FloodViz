import os
import pandas as pd
import numpy as np
from pathlib import Path

from glob import glob

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import rioxarray as rxr
import earthpy.plot as ep


def plot_flood_permanent_seasonal(fl_path:Path):

    class_labels = ['No Data', 'Non-water', 'Flood Water']

    fld_src_arr = rxr.open_rasterio(fl_path, masked=True).squeeze()

    # Plot data using nicer colors
    colors = ['black', 'lightgray', 'darkblue']
    class_bins = [-0.5, 0.5, 1.5, 2.5]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(class_bins, 
                        len(colors))

    # Plot newly classified and masked raster
    f, ax = plt.subplots(figsize=(10, 5))
    im = fld_src_arr.plot.imshow(cmap=cmap,
                            norm=norm,
                            add_colorbar=False)
    
    # Add legend using earthpy
    ep.draw_legend(im,
                titles=class_labels)
    
    ax.set(title="Classified Floodwater")
    ax.set_axis_off()
    plt.show()
    # plt.savefig('./')

    return


def plot_flood_permanent(fl_path:Path):

    return


def main():

    flood_fl_lst = glob('G:/.shortcut-targets-by-id/1-Owv0cvb_maGj6CjU3lJDrnx_wofctRz/flood_examples_mollie/*/*.tif')

    for fl in flood_fl_lst:
        plot_flood_permanent_seasonal(Path(fl))

        plot_flood_permanent(Path(fl))


if __name__ == '__main__':
    main()