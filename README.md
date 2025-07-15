# FloodViz

## Scripts for visualizing flood events

---

### Set up

Generate the python environment using the `flood_viz.yml` file.

Activate the environment:

`conda activate flood_viz`

---

### Figure generation

To get a histogram of flood events from the DFO and EMDAT datasets (1985-2022), run:

`python floodviz.py -s flood_freq`

<figure>
    <img src="./imgs/dfo_emdat_20230714.png" width="800px">
    <figcaption> <b>Figure 1.</b> Global flood counts grouped by continent from two datasets from 1985-2022.
</figure>

---

To get a plot of a specific flood event, run:

---

To produce a series of flood plots, run:

`python floodviz.py -s raster_class -in Q:/.shortcut-targets-by-id/1iXFDnM6JEC6f0gm4-HjYgreTPUJc6Rat/selected_flood_results_vini_backup`

Optional parameters:

```
usage: floodviz.py [-h] [-s SCRIPT] [-in INPUT_DIR] [-szn SEASONAL] [-g GDRIVE] [-fc FALSE_COLOR] [-tc TRUE_COLOR]
                   [-n NUMBER]

Plots and saves images of classified flood events.

options:
  -h, --help            show this help message and exit
  -s SCRIPT, --script SCRIPT
                        Input the name of the flood visualizations you want. (raster_class OR flood_freq)
  -in INPUT_DIR, --input_dir INPUT_DIR
                        Input base path that has flood classified rasters of interest.
  -szn SEASONAL, --seasonal SEASONAL
                        Set to True for seasonal classification images. Set to False for annual classification images.
                        DEFAULT = TRUE
  -g GDRIVE, --gdrive GDRIVE
                        Root Drive to your Desktop Google Drive
                        DEFAULT = 'Q:/My Drive'
  -fc FALSE_COLOR, --false_color FALSE_COLOR
                        Display False Color image (True/False)
                        DEFAULT = TRUE
  -tc TRUE_COLOR, --true_color TRUE_COLOR
                        Display True Color image (True/False)
                        DEFAULT = TRUE
  -n NUMBER, --number NUMBER
                        Number of images to loop through from input dir.
                        DEFAULT = 3
```

<figure>
    <img src="./imgs/HLS_HLS.S30.T20MPD.2021140T142729.v2.0_CLASS_FC-TC.png" width="1500px">
    <figcaption> <b>Figure 2.</b> Classified flood map with permanent, seasonal, and flood water labeled and the True and False Color images.
</figure>