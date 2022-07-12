#-------------------------------------------------------------------------------
# Name:        Avalanche Susceptibility raster layer creation
# Purpose:      This code creates avlanche start zone susceptibility, connected
#               slope susceptibility, and terrain trap layers for a new method
#               in avlanche susceptibility mapping.  There are required inputs
#               of home folder path, location of DEMs, and the basename of your
#               DEMs
#
# Author:      Lindsey Rotche
#
# Created:     July 12, 2022
# Copyright:   (c) lrotche 2022
# Licence:     <your licence>
#-------------------------------------------------------------------------------
##########  Set up environment ##########
import arcpy
import math
import os
from arcpy.sa import *
arcpy.CheckOutExtension("spatial")

#path where you want new folders made for layers
path = raw_input("Input the path for where all new folders should be built: ")
#Path for folder with DEMs
splitspath = raw_input("Input the path for the location of your DEMs: ")
#Base name of your DEMs
splitbase = raw_input("If you have multiple DEMs, make sure they have the same basename and then a number.\nExample: avDEM_1, avDEM_2, avDEM_3 where \"avDEM_\" is the basename\nWhat is the basename?\nIf you have a single DEM, input the file name without the extension: ")

#Find or create folder for base data
basepath = path + "/SusceptibilityRaster/BaseLayers/"
if not os.path.exists(basepath):
    os.makedirs(basepath)
#Find or create folder for reclassified layers
recpath = path + "/SusceptibilityRaster/ReclassifiedLayers/"
if not os.path.exists(recpath):
    os.makedirs(recpath)
#Find or create folder for intermediate data to be deleted
delpath = path + "/SusceptibilityRaster/DeleteMe/"
if not os.path.exists(delpath):
    os.makedirs(delpath)
#Find or create folder for final susceptibility rasters
finalpath = path + "/SusceptibilityRaster/Finals/"
if not os.path.exists(finalpath):
    os.makedirs(finalpath)
#Find or create folder for final start susceptibility rasters
finalstart_splits = finalpath + "/FinalStartSplits/"
if not os.path.exists(finalstart_splits):
    os.makedirs(finalstart_splits)
#Find or create folder for final connected susceptibility rasters
finalconnect_splits = finalpath + "/FinalConnectSplits/"
if not os.path.exists(finalconnect_splits):
    os.makedirs(finalconnect_splits)
#Find or create folder for terrain trap data
ttrappath = path + "/TerrainTraps/"
if not os.path.exists(ttrappath):
    os.makedirs(ttrappath)
#Find or create folder for terrain trap splits
ttrappath_splits = ttrappath + "/Splits/"
if not os.path.exists(ttrappath_splits):
    os.makedirs(ttrappath_splits)


####  Function to create and reclassify slope, aspect, and vector ruggedness layers ##########
def basedata(dem, x):
    #---- Make topographic layers ----

    # Create slope #
    print "Creating slope"
    outSlope = Slope(dem)
    slope = outSlope.save(basepath + "slope_" + str(x) + ".tif")

    # Create aspect #
    print "Creating aspect"
    outAspect = Aspect(dem)
    aspect = outAspect.save(basepath + "aspect_" + str(x) + ".tif")

    # Create VRM #
    # Convert Slope and Aspect rasters to radians
    print "Converting to radians"
    slopeRad = Float(outSlope * 3.14/180.0)
    aspectRad = Float(outAspect * 3.14/180.0)
    # Calculate x, y, and z rasters
    print "Calculating x, y, and z rasters"
    xyRaster = Sin(slopeRad)
    zRaster = Cos(slopeRad)
    aspectCon = Con(outAspect, 0.0, aspectRad, "VALUE = -1") #If value is -1 on original aspect make value 0, otherwise make it radian value
    xRaster = Sin(aspectCon) * xyRaster
    yRaster = Cos(aspectCon) * xyRaster
    # Calculate sums of x, y, and z rasters for selected neighborhood size
    print "Calculating sums of x, y, and z rasters in selected neighborhood"
    xSumRaster = FocalStatistics(xRaster, NbrRectangle(5, 5, "CELL"), "SUM", "NODATA")
    ySumRaster = FocalStatistics(yRaster, NbrRectangle(5, 5, "CELL"), "SUM", "NODATA")
    zSumRaster = FocalStatistics(zRaster, NbrRectangle(5, 5, "CELL"), "SUM", "NODATA")
    # Calculate VRM
    print "Creating VRM"
    vrm = 1 - (SquareRoot(Square(xSumRaster) + Square(ySumRaster) + Square(zSumRaster)) / 25)
    vrm.save(basepath + "vrm_" + str(x) + ".tif")

    #---- Reclassify ----

    print "Time to reclassify..."
    #Reclassify slope
    print "Reclassifying slope"
    #For start susceptibility raster
    slope_reclass = Reclassify(outSlope, "VALUE", RemapRange([[0, 28, "NODATA"], [28, 30, 4], [30, 35, 7], [35, 45, 9], [45, 90, 7]]), "NODATA")
    slope_reclass.save(recpath + "SlopeReclass_" + str(x) + ".tif")
    #For connected slopes
    conected_reclass = Reclassify(outSlope, "VALUE", RemapRange([[12, 25, 4], [25, 28, 9]]), "NODATA")
    conected_reclass.save(recpath + "ConnectedReclass_" + str(x) + ".tif")
    #For terrain traps
    ttrapfall_reclass = Reclassify(outSlope, "VALUE", RemapRange([[50, 90, 1]]), "NODATA")
    ttrapfall_reclass.save(ttrappath_splits + "SteepFalls_" + str(x) + ".tif")

    #Reclassify aspect
    # N=0-22.5 # NE=22.5-67.5 # E=67.5-112.5 # SE=112.5-157.5 # S=157.5-202.5 # SW=202.5-247.5 # W=247.5-292.5 # NW=292.5-337.5 # N=337.5-360
    print "Reclassifying aspect"
    aspect_reclass = Reclassify(outAspect, "VALUE", RemapRange([[0, 22.5, 9], [22.5, 67.5, 6], [67.5, 112.5, 1], [112.5, 157.5, 4], [157.5, 202.5, 6], [202.5, 247.5, 2], [247.5, 292.5, 1], [292.5, 337.5, 4], [337.5, 360, 9]]), "NODATA")
    aspect_reclass.save(recpath + "AspectReclass_" + str(x) + ".tif")

    #Reclassify VRM
    print "Reclassifying VRM"
    vrm_reclass = Reclassify(vrm, "VALUE", RemapRange([[0, 0.001, 9], [0.001, 0.0034, 7], [0.0034,0.0057,5], [0.0057, 0.02, 1], [0.02, 1, 0]]))
    vrm_reclass.save(recpath + "vrmReclass_" + str(x) + ".tif")

####  Funciton to create ridge layer and reclassify disntace to ridges  ####
#Beause the process follows a different outline
def ridgefunc(dem, x):
    #Create TPI
    print "Creating TPI"
    demObject = Raster(dem)

    #Get focal mean of deam with 00 cell circle neighborhood
    FocalMean_200 = arcpy.sa.FocalStatistics(dem, NbrCircle(200, "CELL"), "MEAN")
    #Get TPI by subtracting focal mean from original dem
    TPI = demObject - FocalMean_200
    TPI.save(basepath + "TPI_" + str(x) + ".tif")

    #Get standard deviation of TPI
    std_result = arcpy.management.GetRasterProperties(TPI, "STD")
    mean_result = arcpy.management.GetRasterProperties(TPI, "MEAN")
    std = std_result.getOutput(0)
    mean = mean_result.getOutput(0)

    #Create new layer with only ridges
    ridges_raster = Reclassify(TPI, "VALUE", RemapRange([[std, 1000.0, 1]]), "NODATA")
    ridges_raster.save(basepath + "Ridges_" + str(x) + ".tif")

    #Create new layer with only gullies/valleys
    ttrapgul_rast = Reclassify(TPI, "VALUE", RemapRange([[-1000.0,float(mean)-float(std), 1]]), "NODATA")
    ttrapgul_rast.save(ttrappath_splits + "Gullies_" + str(x) + ".tif")

    #Reclassify distance to ridges
    print "Reclassifying distance to ridges"

    #Convert ridge raster to vector
    ridges = arcpy.RasterToPolygon_conversion(ridges_raster, basepath + "PolyRidges_" + str(x) + ".shp")

    #Create 80m from ridges and 100m from ridges buffers
    ridges_80m = arcpy.Buffer_analysis(ridges, delpath + "Ridges_80m_" + str(x) + ".shp", "80 Meters", "OUTSIDE_ONLY", "", "ALL")
    ridges_100m_full = arcpy.Buffer_analysis(ridges, delpath + "Ridges_100m_Full_" + str(x) + ".shp", "100 Meters", "OUTSIDE_ONLY", "", "ALL")
    ridges_100m = arcpy.Erase_analysis(ridges_100m_full, ridges_80m, delpath + "Ridges_100m_Erased_" + str(x) + ".shp")

    #Add weight fields to buffers and ridges
    arcpy.AddField_management(ridges, "Weight", "SHORT")
    arcpy.AddField_management(ridges_80m, "Weight", "SHORT")
    arcpy.AddField_management(ridges_100m, "Weight", "SHORT")

    #Fill in appropriate weights
    with arcpy.da.UpdateCursor(ridges, ["Weight"]) as cursor:
        for row in cursor:
            row[0] = 3
            cursor.updateRow(row)
        del cursor

    with arcpy.da.UpdateCursor(ridges_80m, ["Weight"]) as cursor:
        for row in cursor:
            row[0] = 9
            cursor.updateRow(row)
        del cursor

    with arcpy.da.UpdateCursor(ridges_100m, ["Weight"]) as cursor:
        for row in cursor:
            row[0] = 5
            cursor.updateRow(row)
        del cursor

    #Merge buffs and ridges to one shapefile
    DistRidge_vector = arcpy.Merge_management([ridges, ridges_80m, ridges_100m], delpath + "DistToRidges_" + str(x) + ".shp", "Weight")

    #Convert to raster
    distridge = arcpy.PolygonToRaster_conversion(DistRidge_vector, "Weight", delpath + "part_DistToRidges_" + str(x) + ".tif", "MAXIMUM_AREA", "", 1)
    ridge_reclass = Con(IsNull(distridge), 0, distridge)
    ridge_reclass.save(recpath + "DistToRidges_" + str(x) + ".tif")

####  Run base layer functions in for loop for all DEMs  ####
arcpy.env.workspace = splitspath
arcpy.env.overwriteOutput = True

#Get DEMs
demList = arcpy.ListRasters()

x = -1
for dem in demList:
    x = x + 1
    basedata(dem, x)
    ridgefunc(dem, x)

##### Function to weight and add all layers together  #####
def suceptfunc(slope, vrm, aspect, ridges, connect, start_output, connect_output):
    slope_reclass = Raster(slope)
    vrm_reclass = Raster(vrm)
    aspect_reclass = Raster(aspect)
    ridges_reclass = Raster(ridges)
    connect_reclass = Raster(connect)

    slope_weight = 1.0
    vrm_weight = 0.5
    aspect_weight = 0.5
    ridge_weight = 0.5
    connect_weight = 1.0

    startfinal = ((slope_weight)*(slope_reclass)) + ((vrm_weight)*(vrm_reclass)) + ((aspect_weight)*(aspect_reclass)) + ((ridge_weight)*(ridges_reclass))
    startfinal.save(start_output)

    connectfinal = ((connect_weight)*(connect_reclass)) + ((vrm_weight)*(vrm_reclass)) + ((aspect_weight)*(aspect_reclass)) + ((ridge_weight)*(ridges_reclass))
    connectfinal.save(connect_output)

####  Run the start susceptiblity function in a for loop  ####
demlist = arcpy.ListRasters(splitbase+"*")

#List of reclass layers by type
arcpy.env.workspace = recpath
aspect_list = arcpy.ListRasters("AspectReclass*")
ridge_list = arcpy.ListRasters("DistToRidges*")
slope_list = arcpy.ListRasters("SlopeReclass*")
vrm_list = arcpy.ListRasters("vrmReclass*")
connect_list = arcpy.ListRasters("ConnectedReclass*")

#Make list of all layers with each type divided into sublists
main_list = [aspect_list] + [ridge_list] + [slope_list] + [vrm_list] + [connect_list]

#Make list of index values
demcount = len(demlist)
indexlist = list(range(demcount))

#Organize into groups by number
for index in indexlist:
    templist = []
    for element in main_list:
        templist.append(element[index])
    aspect = templist[0]
    ridges = templist[1]
    slope = templist[2]
    vrm = templist[3]
    connect = templist[4]

    suffix = aspect[14:-4]
    print "for " + suffix + ": aspect is " + aspect + ", ridges is " + ridges + ", slope is " + slope + ", vrm is " + vrm

    #Create name for outputs
    start_output = finalstart_splits + "/startsusceptibility_" + suffix + ".tif"
    connect_output = finalconnect_splits + "/connectsusceptibility_" + suffix + ".tif"

    #Run suceptfunc function for each number
    suceptfunc(slope, vrm, aspect, ridges, connect, start_output, connect_output)
    print "susceptibility calculated for " + suffix

####  Combine split finals into one large one  ####
#Combine start suscetibility rasters
arcpy.env.workspace = finalstart_splits
arcpy.env.overwriteOutput = True

finalstart_splits = arcpy.ListRasters("startsusceptibility*")
arcpy.MosaicToNewRaster_management(finalstart_splits, finalpath, "FULL_startsuceptibility.tif", "", "32_BIT_FLOAT", "", "1")

#Combine connect susceptibility rasters
arcpy.env.workspace = finalconnect_splits
arcpy.env.overwriteOutput = True

finalconnect_splits = arcpy.ListRasters("connectsusceptibility*")
arcpy.MosaicToNewRaster_management(finalconnect_splits, finalpath, "FULL_connectsuceptibility.tif", "", "32_BIT_FLOAT", "", "1")

#Combine gullies
arcpy.env.workspace = ttrappath_splits
arcpy.env.overwriteOutput = True

finalgully_splits = arcpy.ListRasters("Gullies*")
arcpy.MosaicToNewRaster_management(finalgully_splits, ttrappath, "FULL_Gullies.tif", "", "8_BIT_UNSIGNED", "", "1")

#Combine steep falls
finalfalls_splits = arcpy.ListRasters("SteepFalls*")
arcpy.MosaicToNewRaster_management(finalfalls_splits, ttrappath, "FULL_SteepFalls.tif", "", "8_BIT_UNSIGNED", "", "1")

print "Done!"