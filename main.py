''' 
TOPP - THE OPTIMAL PATH PROGRAM

This code accepts DEM as an input and finds the optimal path in a raster imagery
Last tested on October 2nd, 2022 at 10:20 pm

Developed by Hakan OGUZ
'''

import tkinter.messagebox
from tkinter import *
from tkinter import filedialog
import os
import itertools
from osgeo import gdal, osr, ogr
import numpy as np
from skimage.graph import route_through_array
from math import sqrt, ceil
import webbrowser

def about():
    global my_img
    about = Toplevel()
    about.geometry("250x300")

    about.resizable(False, False)
    about.title("About Me")
    my_img = PhotoImage(file="logo\hakan.png")
    my_label_img = Label(about, image=my_img).pack(pady=20)
    my_label_txt = Label(about, text="TOPP").pack()
    my_label_txt = Label(about, text="The Optimal Path Program").pack()
    my_label_txt = Label(about, text="Created by Hakan OGUZ").pack(pady=20)
    my_label_txt = Label(about, text="Version 1.0.0").pack()
    my_label_txt = Label(about, text="October 2, 2022").pack()

def help_page():
    webbrowser.open_new("https://hakanoguz.github.io/tools.html")

def convert_to_polyline():
    def pixelOffset2coord(rasterfn, xOffset, yOffset):
        raster = gdal.Open(rasterfn)
        geotransform = raster.GetGeoTransform()
        originX = geotransform[0]
        originY = geotransform[3]
        pixelWidth = geotransform[1]
        pixelHeight = geotransform[5]
        coordX = originX + pixelWidth * xOffset
        coordY = originY + pixelHeight * yOffset
        return coordX, coordY

    def raster2array(rasterfn):
        raster = gdal.Open(rasterfn)
        band = raster.GetRasterBand(1)
        array = band.ReadAsArray()
        return array

    def array2shp(array, outSHPfn, rasterfn, pixelValue):

        # max distance between points
        raster = gdal.Open(rasterfn)
        geotransform = raster.GetGeoTransform()
        pixelWidth = geotransform[1]
        maxDistance = ceil(sqrt(2 * pixelWidth * pixelWidth))
        #print(maxDistance)

        # array2dict
        count = 0
        roadList = np.where(array == pixelValue)
        multipoint = ogr.Geometry(ogr.wkbMultiLineString)
        pointDict = {}
        for indexY in roadList[0]:
            indexX = roadList[1][count]
            Xcoord, Ycoord = pixelOffset2coord(rasterfn, indexX, indexY)
            pointDict[count] = (Xcoord, Ycoord)
            count += 1

        # dict2wkbMultiLineString
        multiline = ogr.Geometry(ogr.wkbMultiLineString)
        for i in itertools.combinations(pointDict.values(), 2):
            point1 = ogr.Geometry(ogr.wkbPoint)
            point1.AddPoint(i[0][0], i[0][1])
            point2 = ogr.Geometry(ogr.wkbPoint)
            point2.AddPoint(i[1][0], i[1][1])

            distance = point1.Distance(point2)

            if distance < maxDistance:
                line = ogr.Geometry(ogr.wkbLineString)
                line.AddPoint(i[0][0], i[0][1])
                line.AddPoint(i[1][0], i[1][1])
                multiline.AddGeometry(line)

        # wkbMultiLineString2shp
        shpDriver = ogr.GetDriverByName("ESRI Shapefile")
        if os.path.exists(outSHPfn):
            shpDriver.DeleteDataSource(outSHPfn)
        outDataSource = shpDriver.CreateDataSource(outSHPfn)
        outLayer = outDataSource.CreateLayer(outSHPfn, geom_type=ogr.wkbMultiLineString)
        featureDefn = outLayer.GetLayerDefn()
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetGeometry(multiline)
        outLayer.CreateFeature(outFeature)

    def main(rasterfn, outSHPfn, pixelValue):
        array = raster2array(rasterfn)
        array2shp(array, outSHPfn, rasterfn, pixelValue)

    if __name__ == "__main__":
        rasterfn = 'Path.tif'
        outSHPfn = 'Path.shp'
        pixelValue = 1
        main(rasterfn, outSHPfn, pixelValue)

    tkinter.messagebox.showinfo("Message", "Path converted to Shapefile successfully!")
    #print("Path converted to ESRI Shapefile!")
'''
532841	4199828 # starting x and y
614542  4258343 # destinatiın x and y
'''

def calculate_slope():
    #window.filepath = "C:/Users/johnd/PycharmProjects/pythonProjects8/dem.tif"
    try:
        dem = gdal.Open(window.filepath)
    except Exception:
        print("Please select a DEM file as an input!")
    slp = gdal.DEMProcessing("Slope.tif", dem, "slope", computeEdges=True)
    tkinter.messagebox.showinfo("Message", "Slope.tif created successfully!")
    return slp


def find_path():
    def raster2array(rasterfn):
        raster = gdal.Open(rasterfn)
        band = raster.GetRasterBand(1)
        array = band.ReadAsArray()
        return array

    def coord2pixeloffset(rasterfn, x, y):
        raster = gdal.Open(rasterfn)
        geotransform = raster.GetGeoTransform()
        originx = geotransform[0]
        originy = geotransform[3]
        pixelwidth = geotransform[1]
        pixelheight = geotransform[5]
        xoffset = int((x - originx) / pixelwidth)
        yoffset = int((y - originy) / pixelheight)
        return xoffset, yoffset

    def createpath(costsurfacefn, costsurfacearray, startcoord, stopcoord):
        # coordinates to array index
        startcoordx = startcoord[0]
        startcoordy = startcoord[1]
        startindexx, startindexy = coord2pixeloffset(costsurfacefn, startcoordx, startcoordy)

        stopcoordx = stopcoord[0]
        stopcoordy = stopcoord[1]
        stopindexx, stopindexy = coord2pixeloffset(costsurfacefn, stopcoordx, stopcoordy)

        # create path
        indices, weight = route_through_array(costsurfacearray, (startindexy, startindexx), (stopindexy, stopindexx),
                                              geometric=True, fully_connected=True)
        indices = np.array(indices).T
        path = np.zeros_like(costsurfacearray)
        path[indices[0], indices[1]] = 1
        return path

    def array2raster(newrasterfn, rasterfn, array):
        raster = gdal.Open(rasterfn)
        geotransform = raster.GetGeoTransform()
        originx = geotransform[0]
        originy = geotransform[3]
        pixelwidth = geotransform[1]
        pixelheight = geotransform[5]
        cols = array.shape[1]
        rows = array.shape[0]

        driver = gdal.GetDriverByName('GTiff')
        outraster = driver.Create(newrasterfn, cols, rows, 1, gdal.GDT_Byte)
        outraster.SetGeoTransform((originx, pixelwidth, 0, originy, 0, pixelheight))
        outband = outraster.GetRasterBand(1)
        outband.WriteArray(array)
        outrasterSRS = osr.SpatialReference()
        outrasterSRS.ImportFromWkt(raster.GetProjectionRef())
        outraster.SetProjection(outrasterSRS.ExportToWkt())
        outband.FlushCache()

    def main(costsurfacefn, outputpathfn, startcoord, stopcoord):
        costsurfacearray = raster2array(costsurfacefn)  # creates array from cost surface raster

        patharray = createpath(costsurfacefn, costsurfacearray, startcoord, stopcoord)  # creates path array

        array2raster(outputpathfn, costsurfacefn, patharray)  # converts path array to raster

    if __name__ == "__main__":
        CostSurfacefn = 'Slope.tif'
        try:
            startX = int(startX_entry.get())
            startY = int(startY_entry.get())
            stopX = int(stopX_entry.get())
            stopY = int(stopY_entry.get())
        except Exception as ex:
            tkinter.messagebox.showerror(title="Error", message="Please enter X,Y coordinates!")
        else:
            startcoord = (startX, startY)
            stopcoord = (stopX, stopY)
        outputPathfn = 'Path.tif'
        main(CostSurfacefn, outputPathfn, startcoord, stopcoord)
        tkinter.messagebox.showinfo("Message", "Path.tif created successfully!")


def browse_image():
    #global my_image

    window.filepath = filedialog.askopenfilename(initialdir=os.getcwd(),
                                                 title="Select Image File",
                                                 filetypes=(("TIFF files", "*.tif"),
                                                            ("PNG files", "*.png"),
                                                            ("JPG files", "*.jpg"),
                                                            ("All files", "*.*")))
    tkinter.messagebox.showinfo("Message", "DEM was loaded successfully!")
#     my_image = ImageTk.PhotoImage(Image.open(window.filepath))
#     Label(image=my_image).pack()


window = Tk()

my_label = Label(bd=1,relief="solid",font="Times",bg='#3C424A',fg="white")

window.geometry("420x300")

window.resizable(False, False)

window.title("TOPP-The Optimal Path Program")
icon = PhotoImage(file="logo\logo.png")
window.iconphoto(True, icon)
window.configure(bg='#3C424A')
buttonBrowse = Button(window, text="Load DEM", width=12, command=browse_image)
buttonBrowse.place(x=10, y=250)

buttonCalcSlope = Button(window, text="Create Slope", width=12, command=calculate_slope)
buttonCalcSlope.place(x=110, y=250)

button_help_page = Button(window, text="Help Page", width=12, bg='#3C424A',fg="white", command=help_page)
button_help_page.place(x=310, y=10)


# buttonCalcSlope.place(relx=0.80, rely=0.96, anchor=S)
buttonFindPath = Button(window, text="Find Path", width=12, command=find_path)
buttonFindPath.place(x=210, y=250)

btnConvertShp = Button(window, text="Path to Shp", width=12, command=convert_to_polyline)
btnConvertShp.place(x=310, y=250)

startX_entry = Entry(window, width=15)
startY_entry = Entry(window, width=15)
stopX_entry = Entry(window, width=15)
stopY_entry = Entry(window, width=15)
startX_entry.place(x=200, y=80)
startY_entry.place(x=310, y=80)
stopX_entry.place(x=200, y=130)
stopY_entry.place(x=310, y=130)

text_label_start = Label(window, text="Enter starting point coordinates:", bg='#3C424A',fg="white")
text_label_start.pack()
text_label_start.place(x=20, y=79)

text_label_startX = Label(window, text="X", bg='#3C424A',fg="white")
text_label_startX.pack()
text_label_startX.place(x=240, y=57)

text_label_startY = Label(window, text="Y", bg='#3C424A',fg="white")
text_label_startY.pack()
text_label_startY.place(x=340, y=57)

text_label_stop = Label(window, text="Enter ending point coordinates:", bg='#3C424A',fg="white")
text_label_stop.pack()
text_label_stop.place(x=20, y=129)

text_label_stopX = Label(window, text="X", bg='#3C424A',fg="white")
text_label_stopX.pack()
text_label_stopX.place(x=240, y=107)

text_label_stopY = Label(window, text="Y", bg='#3C424A',fg="white")
text_label_stopY.pack()
text_label_stopY.place(x=340, y=107)

button_about = Button(window, text="About", width=12, bg='#3C424A', fg="white", command=about)
button_about.place(x=10, y=10)
window.mainloop()