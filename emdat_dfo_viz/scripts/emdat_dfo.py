import os
import numpy as np 
import pandas as pd 

import matplotlib.pyplot as plt
import matplotlib as mpl


plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = '16'

def import_data():

    country_df = pd.read_csv('./emdat_dfo_viz/data/countries_continents_update.csv', encoding='latin-1')
    country_dict = dict(zip(country_df['Country'],country_df['Continents']))

    emdat_df = pd.read_csv("./emdat_dfo_viz/data/emdat_public_20230710.csv", encoding='latin-1')
    emdat_1985_df = emdat_df.loc[(emdat_df['Year'] >=1985) & (emdat_df['Year'] < 2023)][['Year', 'Region', 'Continent']]
    emdat_1985_df['Continent2'] = np.where(emdat_1985_df['Continent'] == 'Americas', emdat_1985_df['Region'], emdat_1985_df['Continent'])
    emdat_1985_df['Continent2'] = np.where(emdat_1985_df['Continent2'] == 'Caribbean', 'Northern America', emdat_1985_df['Continent2'])
    emdat_1985_df['Continent2'] = np.where(emdat_1985_df['Continent2'] == 'Central America', 'Northern America', emdat_1985_df['Continent2'])
    emdat_1985_df['Val'] = 1

    emdat_df = pd.DataFrame()
    emdat_df['Continents'] = ['Africa', 'Asia', 'Europe', 'Northern America', 'Oceania', 'South America']
    emdat_df = emdat_df.set_index('Continents')
    for yr in range(1985, 2023):
        temp = pd.Series(emdat_1985_df.loc[emdat_1985_df['Year']==yr].groupby(['Continent2'])['Val'].sum())
        emdat_df = pd.concat([emdat_df, temp], axis=1)
        emdat_df = emdat_df.rename(columns={'Val':yr})
        # emdat_df[yr] = emdat_1985_df.loc[emdat_1985_df['Year']==yr].groupby(['Continent2'])['Val'].sum().values
    emdat_df = emdat_df.fillna(0)
    emdat_df = emdat_df.T
    # emdat_df.columns = emdat_df.iloc[0]
    # emdat_df = emdat_df.drop(['Continents'], axis=0)
    emdat_df = emdat_df[['Asia','Africa','Northern America', 'South America','Europe','Oceania']]
    emdat_df = emdat_df.rename(columns={'Northern America': 'North America'})

    dfo_df = pd.read_csv("./emdat_dfo_viz/data/dfo_FloodArchive_20230710.csv", encoding='latin-1')

    dfo_df['Continents'] = ''
    dfo_df['Country'] = dfo_df['Country'].str.strip()
    dfo_df['Continents'] = dfo_df['Country'].map(country_dict)
    dfo_df['Year'] = dfo_df['Began'].str.split('/').str[-1]
    dfo_df = dfo_df[['Year', 'Continents']]
    dfo_df['Val'] = 1
    dfo_df.loc[len(dfo_df)] = ['2022', 'Asia', 0]
    dfo_df.loc[len(dfo_df)] = ['2022', 'Africa', 0]
    dfo_df.loc[len(dfo_df)] = ['2022', 'North America', 0]
    dfo_df.loc[len(dfo_df)] = ['2022', 'South America', 0]
    dfo_df.loc[len(dfo_df)] = ['2022', 'Europe', 0]
    dfo_df.loc[len(dfo_df)] = ['2022', 'Oceania', 0]


    df = pd.DataFrame()
    df['Continents'] = ['Africa', 'Asia', 'Europe', 'North America', 'Oceania', 'South America']
    for yr in range(1985, 2023):
        df[yr] = dfo_df.loc[dfo_df['Year']==str(yr)].groupby(['Continents'])['Val'].sum().values
    df = df.T
    df.columns = df.iloc[0]
    df = df.drop(['Continents'], axis=0)
    df = df[['Asia','Africa','North America', 'South America','Europe','Oceania']]

    return df, emdat_df


def plot_flood_freq():
    df, emdat_df = import_data()

    print(f"dfo min: {df[-4:].sum(axis=1).min()}")
    print(f"dfo max: {df[-4:].sum(axis=1).max()}")

    print(f"emdat min: {emdat_df[-4:].sum(axis=1).min()}")
    print(f"emdat min: {emdat_df[-4:].sum(axis=1).max()}")

    img_path = './emdat_dfo_viz/imgs/dfo_emdat_20230714.png'
    if os.path.exists(img_path):
        
        print(f'{img_path} exists')

        return img_path
        

    color_dict = {'Oceania':'#fde725',
                'Europe': '#7ad151', 
                'South America': '#22a884',
                'North America': '#2a788e', 
                'Africa': '#414487', 
                'Asia': '#440154'}


    fig, ax = plt.subplots(figsize=(15, 10))
    ax.set_facecolor('silver')
    ax.grid(color='white', zorder=0)

    bottom = np.zeros(38)
    for cont, count in df.items():
        p = ax.bar(df.index - 0.2, count, 0.4, label=cont, bottom=bottom, color=color_dict[cont], zorder=2)
        bottom += count
    # ax.legend(title = 'DFO', loc="upper left", fontsize=18)

    bottom = np.zeros(38)
    for cont, count in emdat_df.items():
        p = ax.bar(emdat_df.index + 0.2, count, 0.4, label=cont, alpha=0.5, bottom=bottom, color=color_dict[cont], zorder=3)
        bottom += count

    handles, labels = plt.gca().get_legend_handles_labels()
    plt.gca().add_artist(ax.legend(handles[6:12], labels[6:12], 
                                title='EMDAT', loc=(0.2,0.67), 
                                title_fontsize=18, facecolor='white',
                                framealpha =1))
    plt.gca().add_artist(ax.legend(handles[0:6], labels[0:6], 
                                title='DFO', loc=(0.01, 0.67), 
                                title_fontsize=18, facecolor='white',
                                framealpha =1))

    # define patch area2
    rect2 = mpl.patches.Rectangle(
        xy=(2017.5, -.5),  # lower left corner of box: beginning of x-axis range & y coord)
        width=4.95,  # width from x-axis range
        height=230,
        #color='grey',
        #alpha=0.4, 
        edgecolor='red',
        linewidth=3,
        facecolor='none',
        zorder=4
    )
    ax.add_patch(rect2)

    ax.set_xlabel('Year', size=22)
    ax.set_ylabel('Flood Count', size=22)

    plt.savefig(img_path, dpi=300, facecolor='w', edgecolor='w')




    return