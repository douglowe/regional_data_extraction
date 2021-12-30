
import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
import salem
import matplotlib.pyplot as plt
import cartopy
from shapely.geometry import Point




def load_shapefiles(GMBs,path,shape_file):
    dtest = gpd.read_file(path+shape_file)
    GMB_area = dtest[dtest.loc[:,'NAME'].isin(GMBs)]
    GMB_area = GMB_area.to_crs("EPSG:4326")
    return(GMB_area)


def obtain_lat_lon_indexes(ds,lat_lower,lat_higher,long_lower,long_higher):

    lat_index_list = []
    lon_index_list = []

    for index_lat in range(ds.south_north.shape[0]):
        lats = ds.isel(south_north=index_lat).XLAT.values[0]
        if lats.max() > lat_lower and lats.min() < lat_higher: 
            lat_index_list = lat_index_list + [index_lat]

    for index_lon in range(ds.west_east.shape[0]):
        lons = ds.isel(west_east=index_lon).XLONG.values[0]
        if lons.max() > long_lower and lons.min() < long_higher: 
            lon_index_list = lon_index_list + [index_lon]


    return(lat_index_list, lon_index_list)


def build_mask_array(GMB_area,ds,lat_lower,lat_higher,long_lower,long_higher):

    lat_index_list, lon_index_list = obtain_lat_lon_indexes(ds,lat_lower,lat_higher,long_lower,long_higher)
    mask = np.empty([ds.south_north.shape[0], ds.west_east.shape[0]])
    mask[:] = np.nan


    for index_lat in lat_index_list:
        lats = ds.isel(south_north=index_lat).XLAT.values[0]
        
        for index_lon in lon_index_list:
            lat = ds.isel(south_north=index_lat).isel(west_east=index_lon).XLAT.values[0]
            lon = ds.isel(south_north=index_lat).isel(west_east=index_lon).XLONG.values[0]


            point_df = pd.DataFrame({'longitude': [lon], 'latitude': [lat]})
            point_geometry = gpd.points_from_xy(point_df.longitude, point_df.latitude, crs="EPSG:4326")
            point_gdf = gpd.GeoDataFrame(point_df, geometry=point_geometry)

            point_within_shapefile = [point_gdf.within(GMB_area['geometry'][ind])[0] for ind in GMB_area['geometry'].index]
        
            if any(point_within_shapefile):
                mask[index_lat][index_lon] = True
    return(mask)


def plot_data(demo,time,wrf_in,xlims,ylims,zlims,zlevels,data_label,figure_string):

    for sl in np.arange(0,len(time)):
        fig = plt.figure()
        ax = plt.axes(projection=cartopy.crs.Orthographic(0, 50))
        ax.coastlines();
        ax.set_xlim(xlims[0],xlims[1])
        ax.set_ylim(ylims[0],ylims[1])
        ax1 = demo[sl,:,:].plot.contourf(ax=ax, transform=wrf_in.salem.cartopy(),vmin=zlims[0],vmax=zlims[1],levels=zlevels);
        ax.set_title(np.datetime_as_string(time[sl].values,unit='h'))
        ax1.colorbar.set_label(data_label)
        ax.add_geometries(GMB_area.boundary,cartopy.crs.Geodetic(),facecolor='none',edgecolor='k')
        fig.savefig(f'{figure_string}_{np.datetime_as_string(demo["time"][sl].values,unit="h")}.png',dpi=300)
        plt.close(fig)


def save_stat_data(demo,file_name):
    columns = ['Date','Minimum','Mean','Median','Maximum','Std']

    model_stats = pd.DataFrame(columns=columns)
    model_stats.loc[:,'Date'] = demo['time']
    model_stats.loc[:,'Minimum'] = demo.min(axis=(1,2))
    model_stats.loc[:,'Mean'] = demo.mean(axis=(1,2))
    model_stats.loc[:,'Median'] = demo.median(axis=(1,2))
    model_stats.loc[:,'Maximum'] = demo.max(axis=(1,2))
    model_stats.loc[:,'Std'] = demo.std(axis=(1,2))

    model_stats.to_csv(file_name,index=False)



if __name__ == '__main__':
    #import argparse
    
    # read arguments from the command line
    #parser = argparse.ArgumentParser(description="*** Tool for extracting Pollution data for GM region ***")
    
    
    
    
    # hardwiring values
    gm_path = '../ShapeFiles/OS_Boundary_Line_2021-10/Data/GB/'
    gm_shape_file = 'district_borough_unitary_region.shp'

    emep_file = 'Base_day_SeptOct2020.nc'
    wrf_file = 'wrfout_d01_2020-12-31_00:00:00'


    GMBs = ['Bolton District (B)', 'Bury District (B)', 'Manchester District (B)', \
            'Oldham District (B)', 'Rochdale District (B)', 'Salford District (B)', \
            'Stockport District (B)', 'Tameside District (B)', 'Trafford District (B)', \
            'Wigan District (B)']

    # lat/longitude limits for region of the domain to search within when creating the 
    # data mask. If you change your region of interest then change these values to match. 
    lat_lower = 53
    lat_higher = 54
    long_lower = -3
    long_higher = -1
    
    # plot limits for the data maps. This is in OSGB units (I think). If you change your
    # region of interest then change these values to match.
    xlims=(-1.9e5,-1.2e5)
    ylims=(3.6e5,4.2e5)
    
    # Colorbar limits, and number of gradient edges, to use for plotting data.
    zlims=(0,25)
    zlevels=11
    
    # colorbar label, and variable name for extraction/plotting.
    data_label='NO2 (ppb)'
    data_name='SURF_ppb_NO2'
    
    figure_string='testfig2'
    file_name='example_data2.csv'

    # logical controls for plotting data or exporting the stats data
    plot_data_flag = False
    stat_data_flag = True


    #### working code
    # load GMB shapefils
    GMB_area = load_shapefiles(GMBs,gm_path,gm_shape_file)
    # load WRF/EMEP data
    wrf_in = salem.open_wrf_dataset(wrf_file)
    emep_in = xr.open_dataset(emep_file, decode_coords="all")
    ds = xr.open_dataset(wrf_file)

    # create data mask
    mask = build_mask_array(GMB_area,ds,lat_lower,lat_higher,long_lower,long_higher)
    
    # apply data mask
    demo = emep_in[data_name].where(cond=mask==True, other=np.nan)
    # pull out model time
    time = emep_in['time']

    # generate pollution maps
    if plot_data_flag:
        plot_data(demo,time,wrf_in,xlims,ylims,zlims,zlevels,data_label,figure_string)  
    
    # save stats data
    if stat_data_flag:
        save_stat_data(demo,file_name)  












