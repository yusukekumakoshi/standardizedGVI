# This script is used to calculate sGVI (standardized GVI) from point-based GVI data.
# Copyright(C) Yusuke Kumakoshi, Urban Sciences Lab 2020

import os
import geopandas as gpd
import pandas as pd
import numpy as np
from geovoronoi import voronoi_regions_from_coords, points_to_coords
from geovoronoi.plotting import subplot_for_map, plot_voronoi_polys_with_points_in_area
from shapely.ops import cascaded_union
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')
from shapely.geometry import Point

def addExternalPoints(boundary,idx,gdf_clip):
    """
    Add external points to gdf_clip (points with GVI).
    When less than 3 points are in the boundary, Voronoi tessellation does not work.
    --> Force it to work by adding external points.
    """
    x_min, y_min, x_max, y_max = boundary.geometry[idx].bounds
    h = y_max - y_min # height
    w = x_max - x_min # width

    #dummy points
    gdf_clip_ext = gdf_clip.copy()
    dummy_pts = [Point(x_min,y_max+4*h),Point(x_max,y_min-4*h),Point(x_max+4*w,y_min),Point(x_min-4*w,y_max)]
    for pts_idx, gdf_idx in enumerate(range(len(gdf_clip_ext),len(gdf_clip_ext)+4,1)):
        gdf_clip_ext.loc[gdf_idx,'geometry'] = dummy_pts[pts_idx]
    
    gdf_clip_ext.reset_index(drop=True,inplace=True)
    
    return gdf_clip_ext

# gvi_point_gdf,boundary_gdf,link_gdf
def calc_sGVI(gvi_point_gdf,boundary_gdf,link_gdf):
    """
    Calculate sGVI from (1) point gdf of GVI, (2) boundary gdf and (3) road (link) gdf.
    (3) should be the same file as that used to calculate GVI for consistency.
    Returns boundary_gdf with new attributes.
    """
    boundary_gdf['n_pt'] = 0
    boundary_gdf['avgGVI'] = 0
    boundary_gdf['medGVI'] = 0
    boundary_gdf['sGVI'] = 0

    for idx in tqdm(boundary_gdf.index):
        boundary = boundary_gdf.iloc[idx:idx+1] # .iloc[idx] returns GeoSeries, not accepted by gpd.clip

        gdf_proj = gvi_point_gdf.to_crs(boundary_gdf.crs)

        try:
            gdf_clip = gpd.clip(gdf_proj,boundary) # TODO: check if overlays or not
            gdf_clip.dropna(how='all',inplace=True)
            gdf_clip.reset_index(drop=True,inplace=True)

            boundary_gdf.loc[idx,'n_pt'] = len(gdf_clip) # original number of points

            gdf_clip_ext = addExternalPoints(boundary,idx,gdf_clip)

            # Voronoi
            boundary_shape = cascaded_union(boundary.geometry)
            coords = points_to_coords(gdf_clip_ext.geometry)

            poly_shapes, pts, poly_to_pt_assignments = voronoi_regions_from_coords(coords, boundary_shape,farpoints_max_extend_factor=20) # 10: error

            gdf_clip['length_sum'] = 0

            for i in range(len(poly_shapes)):
                poly = poly_shapes[i]
                pt_idx = poly_to_pt_assignments[i][0] #nested list

                poly_gdf = gpd.GeoDataFrame(crs=gdf_clip.crs,geometry=[poly])
                try:
                    # Clip may fail if poly_gdf does not overlay link_gdf
                    cut_link = gpd.clip(link_gdf,poly_gdf)
                    cut_link.dropna(how='all',inplace=True)

                    if len(cut_link)<1:
                        continue

                    # add up total length
                    total_l = 0
                    for j in cut_link.index:
                        total_l += cut_link.loc[j,'geometry'].length

                    # associate with GVI (work on gdf_clip)
                    gdf_clip.loc[pt_idx,'length_sum'] = total_l
                except:
                    continue

            total = gdf_clip['length_sum'].sum()
            gdf_clip['length_ratio'] = [gdf_clip.loc[i,'length_sum']/total for i in gdf_clip.index]

            sgvi = np.dot(np.matrix(gdf_clip['greenView']),np.matrix(gdf_clip['length_ratio']).T)
            # print("sGVI of polygon ",idx,": ",sgvi[0,0])

            boundary_gdf.loc[idx,'avgGVI'] = gdf_clip['greenView'].mean()
            boundary_gdf.loc[idx,'medGVI'] = gdf_clip['greenView'].median()
            boundary_gdf.loc[idx,'sGVI'] = sgvi[0,0]
        except:
            print("No point is contained in the boundary polygon ", idx)
    return boundary_gdf


def checkValidGeometry(pt_gdf):
    for idx in pt_gdf.index:
        pt = pt_gdf.loc[idx,'geometry']
        if pt.geom_type == 'MultiPoint':
            pt_gdf.loc[idx,'geometry'] = pt[0]
        else:
            continue
    return pt_gdf

## ----------------- Main function ------------------------
if __name__ == "__main__":

    crs_common = 'epsg:4326'
    os.chdir("../debag") #set this as the current directory
    root = os.getcwd()

    # gvi_point_gdf = gpd.read_file("Nishi_GreenViewRes_32654.shp") # Shapefile of GVI point data
    # boundary_gdf = gpd.read_file("Nishi_test_32654.shp") # Shapefile of boundary polygon data
    # link_gdf = gpd.read_file("Nishi_road_32654.shp") # Shapefile of road linestring data
    gvi_point_gdf = gpd.read_file("minami_mutsukawa2_GVI.shp") # Shapefile of GVI point data
    boundary_gdf = gpd.read_file("minami_mutsukawa2_boudary.shp") # Shapefile of boundary polygon data
    link_gdf = gpd.read_file("minami_mutsukawa2_road.shp") # Shapefile of road linestring data

    # validity check
    gvi_point_gdf = checkValidGeometry(gvi_point_gdf)

    # Use the same CRS
    gvi_point_gdf = gvi_point_gdf.to_crs(crs_common)
    boundary_gdf = boundary_gdf.to_crs(crs_common)
    link_gdf = link_gdf.to_crs(crs_common)

    print("Input data ready.")

    sGVI_gdf = calc_sGVI(gvi_point_gdf,boundary_gdf,link_gdf)

    print("Calculation finished. Writing the output file.")

    sGVI_gdf.to_file("mm_sGVI.shp")
    print("Done!")
