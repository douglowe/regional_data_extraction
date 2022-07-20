
import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
import xesmf as xe
import salem
import matplotlib.pyplot as plt
import cartopy
from shapely.geometry import Point



def create_regrid_template(dataset,lat_lower,lat_higher,long_lower,long_higher,grid_increment):

    global_grid = xr.Dataset(
        {'lat': (['lat'], np.arange(lat_lower,lat_higher,grid_increment)),
        'lon': (['lon'], np.arange(long_lower,long_higher,grid_increment))}
        )
        
    regridder = xe.Regridder(dataset,global_grid,'bilinear')
    return(regridder)


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
    import argparse
    
    # read arguments from the command line
    parser = argparse.ArgumentParser(description="*** Tool for extracting Pollution data for GM region ***")
    
    # general arguments
    parser.add_argument("--emep_file",type=str,help="Path to EMEP datafile (required)")
    parser.add_argument("--wrf_file",type=str,help="Path to WRF datafile (required)")
    parser.add_argument("--data_name",type=str,help="EMEP data variable to process (required)")
    parser.add_argument("--figure_string",type=str,help="Prefix for figure file name: <prefix>_<date>.png (required if plotting data)")
    parser.add_argument("--data_label",type=str,help="Label for data plots, e.g.: 'NO2' (required if plotting data)")
    parser.add_argument("--data_unit",type=str,help="Unit for data plots, e.g.: 'ppb' (optional, but recommended, for plotting data)")
    parser.add_argument("--stats_file_name",type=str,help="Stats output file name, csv (required if outputting stats data)")
    parser.add_argument("--export_file_name",type=str,help="Export output file name, netcdf (required if exporting data)")
    
    # logical controls for plotting data or exporting the stats data
    parser.add_argument("--plot_data",dest="plot_data_flag",action='store_true',help="Plot data heat map")
    parser.add_argument("--no_plot_data",dest="plot_data_flag",action='store_false',help="Don't plot data heat map (default)")
    parser.add_argument("--stat_data",dest="stat_data_flag",action='store_true',help="Generate stat data (default)")
    parser.add_argument("--no_stat_data",dest="stat_data_flag",action='store_false',help="Generate stat data")
    parser.add_argument("--regrid_data",dest="regrid_data_flag",action='store_true',help="Regrid data to regular Lat/Lon grid")
    parser.add_argument("--no_regrid_data",dest="regrid_data_flag",action='store_false',help="Don't regrid data (default)")
    parser.add_argument("--export_data",dest="export_data_flag",action='store_true',help="Export data to netcdf file")
    parser.add_argument("--no_export_data",dest="export_data_flag",action='store_false',help="Don't export data to netcdf file")
    parser.set_defaults(plot_data_flag=False)
    parser.set_defaults(stat_data_flag=True)
    parser.set_defaults(regrid_data_flag=False)
    parser.set_defaults(export_data_flag=False)

    # Colorbar limits, and number of gradient edges, to use for plotting data.
    parser.add_argument("--data_min", type=float, dest="zmin", help="Lower bound for data colour range (default = 0)")
    parser.add_argument("--data_max", type=float, dest="zmax", help="Upper bound for data colour range (default = 20)")
    parser.add_argument("--data_levels", type=int, dest="zlevels", help="Number of bin boundaries for data colour range (default = 21)")
    parser.set_defaults(zmin=0)
    parser.set_defaults(zmax=20)
    parser.set_defaults(zlevels=21)
    #zlims=(zmin,zmax)
    
    args = parser.parse_args()
    
    
    ## applying general arguments, with check to ensure required arguments are given
    stop_program = False
    error_string = ''

    plot_data_flag = args.plot_data_flag
    stat_data_flag = args.stat_data_flag
    regrid_data_flag = args.regrid_data_flag
    export_data_flag = args.export_data_flag
    zlims = (args.zmin,args.zmax)
    zlevels = args.zlevels
    if plot_data_flag:
        print('Model data will be plotted')
    if stat_data_flag:
        print('Model data statistics will be output')

    #emep_file = '../../EMEP_Man/Base_hourInst_JanFeb2021.nc'
    if args.emep_file:
        emep_file = args.emep_file
    else:
        error_string += 'ERROR: Need to provide an EMEP file (--emep_file)\n'
        stop_program = True
    
    #wrf_file = '../../WRF_Man/2021/wrfout_d02_2021-01-07_00:00:00'
    if args.wrf_file:
        wrf_file = args.wrf_file
    else:
        error_string += 'ERROR: Need to provide a WRF file (--wrf_file)\n'
        stop_program = True
        
    #data_name='SURF_ppb_NO2'
    if args.data_name:
        data_name = args.data_name
    else:
        error_string += 'ERROR: Need to provide a data variable (--data_name)\n'
        stop_program = True

    #figure_string='no2_plots'
    if plot_data_flag:
        if args.figure_string:
            figure_string = args.figure_string
        else:
            error_string += 'ERROR: Need to provide a figure prefix (--figure_string)\n'
            stop_program = True     
    else:
        figure_string = 'no figure'

    #data_label='NO2 (ppb)'
    if plot_data_flag:
        if args.data_label:
            if args.data_unit:
                data_label = f'{args.data_label} ({args.data_unit})'
            else:
                data_label = args.data_label
        else:
            error_string += 'ERROR: Need to provide a data label (--data_label)\n'
            stop_program = True        
    else:
        data_label = 'no figure'

    #file_name='no2_stat_data.csv'
    if stat_data_flag:
        if args.stats_file_name:
            stats_file_name = args.stats_file_name
        else:
            error_string += 'ERROR: Need to provide a stat data filename (--stats_file_name)\n'
            stop_program = True    
    else:
        stats_file_name = 'no stats'

    #file_name='no2_stat_data.csv'
    if export_data_flag:
        if args.export_file_name:
            export_file_name = args.export_file_name
        else:
            error_string += 'ERROR: Need to provide a stat data filename (--export_file_name)\n'
            stop_program = True    
    else:
        export_file_name = 'no export'


    if stop_program:
        raise ValueError('Not all required arguments have been provided, see error messages below:\n'+error_string)
    
    
    
    #### hardwiring values
    gm_path = '../../Geographic_Data/OS_Boundary_Line_2021-10/Data/GB/'
    gm_shape_file = 'district_borough_unitary_region.shp'


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
    

    grid_increment = 0.01


    #### working code
    # load GMB shapefils
    GMB_area = load_shapefiles(GMBs,gm_path,gm_shape_file)
    # load WRF/EMEP data
    wrf_in = salem.open_wrf_dataset(wrf_file)
    emep_in = xr.open_dataset(emep_file, decode_coords="all")
    ds = xr.open_dataset(wrf_file)

    # regrid the data, if required
    if regrid_data_flag:
        regridder = create_regrid_template(emep_in,lat_lower,lat_higher,long_lower,long_higher,grid_increment)
        demo = regridder(emep_in[data_name])
        demo.name = data_name
        
        if export_data_flag:
            demo.to_netcdf(export_file_name)

    else:
        # create data mask
        mask = build_mask_array(GMB_area,ds,lat_lower,lat_higher,long_lower,long_higher)
    
        # apply data mask
        demo = emep_in[data_name].where(cond=mask==True, other=np.nan)
    
        # pull out model time
        time = emep_in['time']

        # save stats data
        if stat_data_flag:
            save_stat_data(demo,stats_file_name)  

        # generate pollution maps
        if plot_data_flag:
            plot_data(demo,time,wrf_in,xlims,ylims,zlims,zlevels,data_label,figure_string)  
    












