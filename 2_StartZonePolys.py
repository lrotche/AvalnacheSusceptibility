#-------------------------------------------------------------------------------
# Name:        Avalanche start zone polygons
# Purpose:      Part 2: This is the second code in a series. It is assumed that
#               you have already run "Avalanche Susceptibility raster layer
#               creation" created by Lindsey Rotche. This code creates itterative
#               start zone polygons to be inserted into an avlanche runout model.
#               Required inputs are a study area polygon, folder structure from
#               the Part 1 code, and an output folder location.
#
# Author:      Lindsey Rotche
#
# Created:     July 12, 2022
# Copyright:   (c) lrotche 2022
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#Set up environment
import os
import arcpy
from arcpy.sa import *
arcpy.CheckOutExtension("spatial")

#Get study area poly
studyarea = raw_input("What is the path of your study area polygon?: ")
#Folder with all start susceptibility layers
totalsuscept_folder = raw_input("What is the path of the folder named \"SusceptibilityRaster\" created in \"Part 1: Avalanche Susceptibility raster layer creation\" ?: ")
#Folder to build start polys
base_folder = raw_input("What is the path of the folder where you want the start polygons built?: ")


#Folder with final start susceptibility splits
finalsplits_folder = totalsuscept_folder + "/Finals/FinalStartSplits"
#Folder with ridge polys
ridges_folder = totalsuscept_folder + "/BaseLayers"

ridgebase = "PolyRidges_"
suscept_base = "startsusceptibility_"

#Get start zone radius (meters)
start_radius = 160


#Find or create overall start poly folder
overallstarts_folder = base_folder + "/StartPolys"
if not os.path.exists(overallstarts_folder):
    os.makedirs(overallstarts_folder)
#Find or create start poly folder for specific radius
starts_folder = overallstarts_folder + "/" + str(start_radius) + "mR"
if not os.path.exists(starts_folder):
    os.makedirs(starts_folder)
#Find or create fishnet folder
fishnet_folder = starts_folder + "/Fishnets"
if not os.path.exists(fishnet_folder):
    os.makedirs(fishnet_folder)
#Find or create delete folder folder
delme_folder = starts_folder + "/DeleteMe"
if not os.path.exists(delme_folder):
    os.makedirs(delme_folder)


#Get susceptibility rasters
arcpy.env.workspace = finalsplits_folder
susceptibility = arcpy.ListRasters()
print susceptibility

susbase_len = len(suscept_base)
for suscept in susceptibility:
    #Get suffix
    suffix = suscept[susbase_len:-4]

    #Get extent of suceptibility raster
    susceptlyr = Raster(suscept)
    extent = susceptlyr.extent
    xmin = extent.XMin
    ymin = extent.YMin
    ymax = extent.YMax

    #Origin for fishnet
    origin = str(xmin) + " " + str(ymin)
    #Y-axis for fishnet
    yaxis = str(xmin) + " " + str(ymax)

    #Create fishnet
    fishnet = arcpy.CreateFishnet_management(fishnet_folder + "/Fishnet_" + suffix + ".shp", origin, yaxis, start_radius, start_radius, 0, 0,"", "LABELS", extent, "POLYGON")
    points = arcpy.MakeFeatureLayer_management(fishnet_folder + "/Fishnet_" + suffix + "_label.shp", "pointslyr_" + suffix)

    #Create susceptiblity poly
    suscept_binary = Con(susceptlyr, 1)
    suscept_poly = arcpy.RasterToPolygon_conversion(suscept_binary, delme_folder + "/SusceptPoly_" + suffix + ".shp")
    #Delete susceptibility polygons < 1000m2 (Buhler 2022)
    arcpy.AddGeometryAttributes_management(suscept_poly, "AREA", "", "SQUARE_METERS")
    susceptpoly_lyr = arcpy.MakeFeatureLayer_management(suscept_poly, "susceptpoly_lyr_" + suffix)
    arcpy.SelectLayerByAttribute_management(susceptpoly_lyr,"NEW_SELECTION", """ "POLY_AREA" < 1000 """)
    arcpy.DeleteFeatures_management(susceptpoly_lyr)


    #Select points that intersect susceptibility poly
    arcpy.SelectLayerByLocation_management(points, "INTERSECT", suscept_poly)

    #Make new layer with only selected features
    start_points = arcpy.FeatureClassToFeatureClass_conversion(points, delme_folder, "StartPoints_" + suffix + ".shp")

    #Buffer start points to make start zones
    starts_all = arcpy.Buffer_analysis(start_points, delme_folder + "/Starts_" + suffix + ".shp", str(start_radius) + " Meters")

    #Erase starts with ridges
    starts_erase = arcpy.Erase_analysis(starts_all, ridges_folder + "/" + ridgebase + suffix + ".shp", delme_folder + "/StartsErase_" + suffix + ".shp")
    #Erase not-suscept from starts
    studyarea_erase = arcpy.Erase_analysis(studyarea, suscept_poly, delme_folder + "/NotSuscept_" + suffix + ".shp")
    starts_mask = arcpy.Erase_analysis(starts_erase, studyarea_erase, delme_folder + "/StartsMask_" + suffix + ".shp")
    #Make starts multipart
    starts_final = arcpy.MultipartToSinglepart_management(starts_mask, starts_folder + "/StartsFINAL_" + suffix + ".shp")

    #Delete all start zones < 1000m2 (Buhler 2022)
    arcpy.AddGeometryAttributes_management(starts_final, "AREA", "", "SQUARE_METERS")
    starts_lyr = arcpy.MakeFeatureLayer_management(starts_final, "starts_lyr_" + suffix)
    arcpy.SelectLayerByAttribute_management(starts_lyr,"NEW_SELECTION", """ "POLY_AREA" < 1000 """)
    arcpy.DeleteFeatures_management(starts_lyr)
    #Delete all start zones not completey within study area
    studyarea_lyr = arcpy.MakeFeatureLayer_management(studyarea, "studyarea_lyr_" + suffix)
    arcpy.SelectLayerByLocation_management(starts_lyr, "COMPLETELY_WITHIN", studyarea_lyr, "", "NEW_SELECTION", "INVERT")
    arcpy.DeleteFeatures_management(starts_lyr)





