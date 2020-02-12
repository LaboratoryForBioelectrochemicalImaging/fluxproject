# GUI
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import ttk as ttk

# Numerical analysis
import numpy as np
import pandas as pd
from scipy.interpolate import griddata # Interpolation algorithm
from skimage import feature # Canny algorithm
import scipy.io # support for matlab workspaces
import scipy.optimize # nonlinear curve fitting
import numpy.matlib # contains repmat function

# Plotting
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # figure handler for embeddable plots
from matplotlib.figure import Figure
from matplotlib import cm # colormaps for surface plots
from mpl_toolkits.axes_grid1 import make_axes_locatable # subplot resizer

# -*- coding: utf-8 -*-
"""  
Flux: Source Code Vers. 1.0.2
Copyright (c) 2019 Lisa Stephens
With minor changes by Nathaniel Leslie (2020)

 This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

This script contains the source code for Flux, a GUI developed to simplify the
process of treating scanning electrochemical microscopy data sets. 

A separate class has been defined for each experiment type (image, CV, CA, 
approach curve) which consists of the set of functions required to process it. 
These classes have the following basic structure:
1. __init__ : Sets up the window, initializes a blank figure
2. SelectFile : Opens a file dialogue window to select a dataset
3. ImportFile : Based on the filetype/manufacturer, imports the dataset and 
   reshapes it into a consistent form for further analysis.
4. ReshapeData : Processes the data set based on the options selected by 
   the user. Updates the figure with the current processing settings.
5. BoxesSelected : Enables/disables functions in the GUI based on current 
   settings
6. SaveFig : Save figure to .png file
7. SaveTxt : Save processed data to .txt file
8. ResetWindow : Clear dataset, figure, and labels

Flux has been tested with the following package versions: numpy v1.16.2, 
pandas v0.24.1, scipy v1.2.1, scikit-image v0.14.2, matplotlib v3.0.3; some 
stability issues have been observed with other versions (particularly between 
numpy/scikit-image).


"""


class ImageApp:
    """Handles data from scanning electrochemical microscopy.
        __init__ will initialize generate the tkinter window
        SelectFile allows for file selection
        ImportFile reads the selected file into memory
        ReshapeData does everything after the 'plot' button in pressed. This method will be broken up into smaller methods in the near future.
    """
    # Setup main window
    def __init__(self, master):
        # initial values to be overwritten

        xpos = np.array([0, 1])
        ypos = np.array([0, 1])
        currents = np.array([[0, 1], [0, 1]])

        xpos_interp = np.array([0, 1])
        ypos_interp = np.array([0, 1])
        currents_edges = np.array([[0, 1], [0, 1]])

        # Create containers
        tabs = ttk.Notebook(master)
        frameBase = tk.Frame(tabs)
        frameAnalytics = tk.Frame(tabs)
        frameFormatting = tk.Frame(tabs)
        tabs.add(frameBase, text="  Base  ")
        tabs.add(frameAnalytics, text="  Analytics  ")
        tabs.add(frameFormatting, text="  Formatting  ")
        tabs.pack(expand=1, fill="both", side="top")

        framePlot = tk.Frame(master)
        framePlot.pack(side="top", pady=5)

        self.frameBottom = tk.Frame(master)
        self.frameBottom.pack(side="bottom")

        ###### Top frame: info about file ########

        # set min column sizes to prevent excessive resizing
        for i in range(0, 8):
            frameBase.columnconfigure(i, minsize=150)
            framePlot.columnconfigure(i, minsize=140)
            frameFormatting.columnconfigure(i, minsize=140)

        # Intro
        labelIntro = tk.Label(frameBase, text="Import experimental data to be plotted.")
        labelIntro.grid(row=0, column=0, padx=20, pady=5, columnspan=3, sticky="WS")

        # Select file
        self.buttonFile = tk.Button(frameBase, text="Select File", command=self.SelectFile)
        self.buttonFile.grid(row=1, column=1, sticky="W" + "E", padx=10)
        self.labelFile = tk.Label(frameBase, pady=10)
        self.labelFile.grid(row=1, column=2, sticky="W")

        # Import file
        self.buttonImport = tk.Button(frameBase, text="Import File", state="disabled", command=self.ImportFile)
        self.buttonImport.grid(row=2, column=1, sticky="W" + "E", padx=10)
        self.labelImport = tk.Label(frameBase, text="Select file to continue.")
        self.labelImport.grid(row=2, column=2, sticky="W")

        # Dropdown menu for manufacturer (needed for files of different format, same extension)
        labelText = tk.Label(frameBase, text="Manufacturer: ")
        labelText.grid(row=3, column=1, sticky="E", padx=10)
        # Create a stringvar which will contian the eventual choice
        self.textVar = tk.StringVar(master)
        self.textVar.set('None')  # set the default option
        # Dictionary with options
        textChoices = {'Biologic', 'CH Instruments', 'HEKA', 'Sensolytics', 'PAR'}
        popupText = tk.OptionMenu(frameBase, self.textVar, *textChoices)
        popupText.configure(width=15)
        popupText.grid(row=3, column=2, sticky="W")
        #        # link function to change dropdown
        self.textVar.trace('w', self.change_dropdown)

        # Specify sampling density of raw SECM image
        self.labelXdim = tk.Label(frameBase, text="Number of x points: ")
        self.labelXdim.grid(row=1, column=3, sticky="W", padx=10)
        self.labelXdim2 = tk.Label(frameBase, text="")
        self.labelXdim2.grid(row=1, column=4, sticky="W")

        self.labelYdim = tk.Label(frameBase, text="Number of y points: ")
        self.labelYdim.grid(row=1, column=5, sticky="W", padx=10)
        self.labelYdim2 = tk.Label(frameBase, text="")
        self.labelYdim2.grid(row=1, column=6, sticky="W")

        # Specify sampling density of interpolated SECM image
        self.labelXinterp = tk.Label(frameBase, text="Interpolated x: ")
        self.labelXinterp.grid(row=2, column=3, sticky="W", padx=10)
        self.labelXinterp2 = tk.Label(frameBase, text="")
        self.labelXinterp2.grid(row=2, column=4, sticky="W")

        self.labelYinterp = tk.Label(frameBase, text="Interpolated y: ")
        self.labelYinterp.grid(row=2, column=5, sticky="W", padx=10)
        self.labelYinterp2 = tk.Label(frameBase, text="")
        self.labelYinterp2.grid(row=2, column=6, sticky="W")

        # Toggle for edge detection
        self.statusEdges = tk.IntVar()
        self.checkEdges = tk.Checkbutton(framePlot, text="Detect edges?", variable=self.statusEdges,
                                         command=self.BoxesSelected)
        self.checkEdges.var = self.statusEdges
        self.checkEdges.grid(row=0, column=0, sticky="E", padx=10, pady=5)

        # Button for generating plot
        self.buttonPlot = tk.Button(framePlot, text="Plot Data", state="disabled", command=self.ReshapeData)
        self.buttonPlot.grid(row=0, column=1, rowspan=2, sticky="W" + "E")
        self.labelPlot = tk.Label(framePlot, text="Import data to begin.")
        self.labelPlot.grid(row=0, column=2, rowspan=2, sticky="W", padx=10)

        # Button for saving the plot
        self.buttonSave = tk.Button(framePlot, text="Save Figure", state="disabled", command=self.SaveFig)
        self.buttonSave.grid(row=0, column=3, rowspan=2, sticky="W" + "E", padx=10)

        # Button for exporting to text file
        self.buttonExport = tk.Button(framePlot, text="Export Data", state="disabled", command=self.SaveTxt)
        self.buttonExport.grid(row=0, column=4, sticky="W" + "E", padx=10)

        # Button for resetting window
        self.buttonReset = tk.Button(framePlot, text="Reset Window", command=self.ResetWindow)
        self.buttonReset.grid(row=0, column=5, padx=20, sticky="W" + "E")

        # Intro
        labelIntro = tk.Label(frameAnalytics, text="Customize the data treatment.")
        labelIntro.grid(row=0, column=0, padx=20, pady=5, columnspan=3, sticky="WS")

        # Toggle for normalizing currents
        self.statusNormalize = tk.IntVar()
        self.checkNormalize = tk.Checkbutton(frameAnalytics, text="Normalize currents?", variable=self.statusNormalize,
                                             command=self.BoxesSelected)
        self.checkNormalize.var = self.statusNormalize
        self.checkNormalize.grid(row=1, column=0, sticky="E", padx=10)

        # Toggle for theoretical/experimental normalization
        self.statusNormalizeExp = tk.IntVar()
        self.checkNormalizeExp = tk.Checkbutton(frameAnalytics, state="disabled", text="Using experimental iss?",
                                                variable=self.statusNormalizeExp, command=self.BoxesSelected)
        self.checkNormalizeExp.var = self.statusNormalizeExp
        self.checkNormalizeExp.grid(row=2, column=0, sticky="E", padx=10)

        # Dropdown menu for slope correction choices
        # Label for X-slope correction
        labelXslope = tk.Label(frameAnalytics, text="X-slope correction")
        labelXslope.grid(row=3, column=1, sticky="W", padx=10)
        # Create a stringvar which will contian the eventual choice
        self.slopeXVar = tk.StringVar(master)
        self.slopeXVar.set('None')  # set the default option
        # Dictionary with options
        slopeXChoices = {'None', 'Y = 0', 'Y = Max'}
        popupSlopeX = tk.OptionMenu(frameAnalytics, self.slopeXVar, *slopeXChoices)
        popupSlopeX.configure(width=10)
        popupSlopeX.grid(row=4, column=1, sticky="W", padx=10)
        #        # link function to change dropdown
        self.slopeXVar.trace('w', self.change_dropdown)

        # Dropdown menu for slope correction choices
        # Label for Y-slope correction
        labelYslope = tk.Label(frameAnalytics, text="Y-slope correction")
        labelYslope.grid(row=3, column=2, sticky="W", padx=10)
        # Create a stringvar which will contian the eventual choice
        self.slopeYVar = tk.StringVar(master)
        self.slopeYVar.set('None')  # set the default option
        # Dictionary with options
        slopeYChoices = {'None', 'X = 0', 'X = Max'}
        popupSlopeY = tk.OptionMenu(frameAnalytics, self.slopeYVar, *slopeYChoices)
        popupSlopeY.configure(width=10)
        popupSlopeY.grid(row=4, column=2, sticky="W", padx=10)
        #        # link function to change dropdown
        self.slopeYVar.trace('w', self.change_dropdown)

        # Input for accepting experimental iss
        labelIssExp = tk.Label(frameAnalytics, text="Expermental iss (nA)")
        labelIssExp.grid(row=1, column=6, padx=10, sticky="W")
        self.entryIssExp = tk.Entry(frameAnalytics, state="disabled")
        self.entryIssExp.grid(row=2, column=6, padx=10, sticky="W")

        # Input for accepting electrode parameters for theoretical iss
        labelRadius = tk.Label(frameAnalytics, text="Radius (µm)")
        labelRadius.grid(row=1, column=1, padx=10, sticky="W")
        self.entryRadius = tk.Entry(frameAnalytics, state="disabled")
        self.entryRadius.grid(row=2, column=1, padx=10, sticky="W")

        labelRg = tk.Label(frameAnalytics, text="Rg")
        labelRg.grid(row=1, column=2, padx=10, sticky="W")
        self.entryRg = tk.Entry(frameAnalytics, state="disabled")
        self.entryRg.grid(row=2, column=2, padx=10, sticky="W")

        labelConc = tk.Label(frameAnalytics, text="Conc. (mM)")
        labelConc.grid(row=1, column=3, padx=10, sticky="W")
        self.entryConc = tk.Entry(frameAnalytics, state="disabled")
        self.entryConc.grid(row=2, column=3, padx=10, sticky="W")

        labelDiff = tk.Label(frameAnalytics, text="Diff. coeff. (m^2/s)")
        labelDiff.grid(row=1, column=4, padx=10, sticky="W")
        self.entryDiff = tk.Entry(frameAnalytics, state="disabled")
        self.entryDiff.grid(row=2, column=4, padx=10, sticky="W")

        labelTheoIss = tk.Label(frameAnalytics, text="Theoretical iss (nA)")
        labelTheoIss.grid(row=1, column=5, padx=10, sticky="W")
        self.labelTheoIssValue = tk.Label(frameAnalytics, text="")
        self.labelTheoIssValue.grid(row=2, column=5, padx=10, sticky="W")

        ######## Formatting menu ########
        # Intro
        labelFormatting = tk.Label(frameFormatting, text="Customize the formatting of the graph.")
        labelFormatting.grid(row=0, column=0, padx=20, pady=5, columnspan=3, sticky="W")

        # Dropdown menu for colormap choices
        # Label for X-slope correction
        labelColormap = tk.Label(frameFormatting, text="Colourmap")
        labelColormap.grid(row=1, column=1, sticky="W", padx=10)
        # Create a stringvar which will contian the eventual choice
        self.colormapVar = tk.StringVar(master)
        self.colormapVar.set('RdYlBu')  # set the default option
        # Dictionary with options
        colormapChoices = {'RdYlBu', 'coolwarm', 'jet', 'grayscale'}
        popupColormap = tk.OptionMenu(frameFormatting, self.colormapVar, *colormapChoices)
        popupColormap.configure(width=10)
        popupColormap.grid(row=2, column=1, sticky="W", padx=10)
        #        # link function to change dropdown
        self.colormapVar.trace('w', self.change_dropdown)

        # Dropdown menu for units on distance
        # Label for dropdown menu
        labelDistance = tk.Label(frameFormatting, text="Units (Distances)")
        labelDistance.grid(row=1, column=2, sticky="W", padx=10)
        # Create a stringvar which will contian the eventual choice
        self.distanceVar = tk.StringVar(master)
        self.distanceVar.set('µm')  # set the default option
        # Dictionary with options
        distanceChoices = {'mm', 'µm', 'nm'}
        popupDistances = tk.OptionMenu(frameFormatting, self.distanceVar, *distanceChoices)
        popupDistances.configure(width=10)
        popupDistances.grid(row=2, column=2, sticky="W", padx=10)
        #        # link function to change dropdown
        self.distanceVar.trace('w', self.change_dropdown)

        # Dropdown menu for units on current
        # Label for dropdown menu
        labelCurrent = tk.Label(frameFormatting, text="Units (Current)")
        labelCurrent.grid(row=1, column=3, sticky="W", padx=10)
        # Create a stringvar which will contian the eventual choice
        self.currentVar = tk.StringVar(master)
        self.currentVar.set('nA')  # set the default option
        # Dictionary with options
        currentChoices = {'µA', 'nA', 'pA'}
        popupCurrent = tk.OptionMenu(frameFormatting, self.currentVar, *currentChoices)
        popupCurrent.configure(width=10)
        popupCurrent.grid(row=2, column=3, sticky="W", padx=10)
        #        # link function to change dropdown
        self.currentVar.trace('w', self.change_dropdown)

        # Entry fields for controlling axis limits on plot
        labelXmin = tk.Label(frameFormatting, text="Xmin")
        labelXmin.grid(row=1, column=4, sticky="W", padx=10)
        self.entryXmin = tk.Entry(frameFormatting)
        self.entryXmin.grid(row=2, column=4, sticky="W", padx=10)

        labelXmax = tk.Label(frameFormatting, text="Xmax")
        labelXmax.grid(row=3, column=4, sticky="W", padx=10)
        self.entryXmax = tk.Entry(frameFormatting)
        self.entryXmax.grid(row=4, column=4, sticky="W", padx=10)

        labelYmin = tk.Label(frameFormatting, text="Ymin")
        labelYmin.grid(row=1, column=5, sticky="W", padx=10)
        self.entryYmin = tk.Entry(frameFormatting)
        self.entryYmin.grid(row=2, column=5, sticky="W", padx=10)

        labelYmax = tk.Label(frameFormatting, text="Ymax")
        labelYmax.grid(row=3, column=5, sticky="W", padx=10)
        self.entryYmax = tk.Entry(frameFormatting)
        self.entryYmax.grid(row=4, column=5, sticky="W", padx=10)

        labelZmin = tk.Label(frameFormatting, text="Zmin")
        labelZmin.grid(row=1, column=6, sticky="W", padx=10)
        self.entryZmin = tk.Entry(frameFormatting)
        self.entryZmin.grid(row=2, column=6, sticky="W", padx=10)

        labelZmax = tk.Label(frameFormatting, text="Zmax")
        labelZmax.grid(row=3, column=6, sticky="W", padx=10)
        self.entryZmax = tk.Entry(frameFormatting)
        self.entryZmax.grid(row=4, column=6, sticky="W", padx=10)

        # Data cursor setup
        labelCursor = tk.Label(frameFormatting, text="Data Cursor")
        labelCursor.grid(row=1, column=7, sticky="W", padx=10)
        self.labelXCursor = tk.Label(frameFormatting, text="X : ")
        self.labelXCursor.grid(row=2, column=7, sticky="W", padx=10)
        self.labelYCursor = tk.Label(frameFormatting, text="Y : ")
        self.labelYCursor.grid(row=3, column=7, sticky="W", padx=10)

        ######### Bottom frame: Figure ###########
        # Start creating the plot
        self.fig = Figure(figsize=(9, 4), dpi=120)

        ### Left plot: Raw SECM image ###
        self.ax1 = self.fig.add_subplot(121)
        self.ax1.set_aspect(1)
        self.img = self.ax1.pcolormesh(xpos, ypos, currents, cmap=cm.get_cmap('RdYlBu_r'))
        # Generate axes to resize the colorbar properly
        divider = make_axes_locatable(self.ax1)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        # Add the color bar
        self.cb = self.fig.colorbar(self.img, cax=cax)
        self.cb.set_label('Current (nA)')
        # Set labels
        self.ax1.set_xlabel('X (µm)')
        self.ax1.set_ylabel('Y (µm)')

        ### Right plot: Detected edges ###
        self.ax2 = self.fig.add_subplot(122)
        self.ax2.set_aspect(1)
        self.edge = self.ax2.pcolormesh(xpos_interp, ypos_interp, currents_edges, cmap=cm.get_cmap('binary'))
        self.ax2.set_xlabel('X (µm)')

        def DataCursor(event):
            try:
                xcursor = event.xdata
                ycursor = event.ydata
                self.labelXCursor.config(text="X : {0:.3f}".format(xcursor))
                self.labelYCursor.config(text="Y : {0:.3f}".format(ycursor))
            except:
                pass

        # Create canvas object which contains frame
        self.fig.subplots_adjust(left=0.07, right=1.0, top=0.95, bottom=0.15)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frameBottom)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="S")
        self.canvas.mpl_connect('button_press_event', DataCursor)
        self.canvas.draw()

    def change_dropdown(*args):
        pass

    def SelectFile(self):
        self.filepath = askopenfilename(initialdir="/",
                                        title="Choose a file.")
        folder = []

        # check for folder symbols in filepath
        for c in self.filepath:
            folder.append(c == '/')
        folder = [i for i, j in enumerate(folder) if j == True]
        # trim off folder path to retrieve just filename
        self.filename = self.filepath[max(folder) + 1:]

        self.labelFile.config(text=self.filename)
        self.buttonImport.config(state="normal")

        # Set manufacturer
        if self.filename[-3:] == 'asc':
            self.textVar.set('HEKA')
        elif self.filename[-3:] == 'mat':
            self.textVar.set('HEKA')
        elif self.filename[-3:] == 'dat':
            self.textVar.set('Sensolytics')
        elif self.filename[-3:] == 'csv':
            self.textVar.set('PAR')
        elif self.filename[-3:] == 'img':
            self.textVar.set('SECMx')
        else:
            pass
        self.labelImport.config(text="Ready.")

    def ImportFile(self):
        ## Check if manufacturer needed
        if self.filename[-3:] == 'txt' and self.textVar.get() == 'None':
            self.labelImport.config(text="Specify a manufacturer.")

        ### ASC import ####
        elif self.filename[-3:] == 'asc':
            self.import_heka_asc(self.filepath)
        ### SECMx import ####
        elif self.filename[-3:] == 'img':
            self.import_3d_secmx(self.filepath)
            self.labelImport.config(text="File imported.")
        ### MAT import ####
        elif self.filename[-3:] == 'mat':
            self.import_heka_mat(self.filepath)
        ### TXT/Biologic import ####
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'Biologic':
            self.import_biologic(self.filepath)
        ### TXT/CH instruments import ####
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'CH Instruments':
            self.import_ch_instruments(self.filepath)
        ### DAT / Sensolytics import ###
        elif self.filename[-3:] == 'dat':
            self.import_sensolytics(self.filepath)
        ### CSV / PAR import
        elif self.filename[-3:] == 'csv':
            self.import_par(self.filepath)

        # Message to display if one of the above imports does not apply
        else:
            self.labelImport.config(text="File type not supported.")

        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")
        self.checkEdges.config(state="normal")

    def import_heka_asc(self, filepath):
        data = []
        try:
            with open(filepath, 'r') as fh:
                for curline in fh:
                    try:
                        curline = curline.split()  # split line into segments
                        float(curline[0])  # check if line contains strings or numbers
                        data.append(curline)  # if number, add to dataframe
                    except:
                        pass  # if string, skip to next line
            self.labelImport.config(text="File imported.")
        except:
            self.labelImport.config(text="Could not import file.")

        # Convert raw data to matrix
        try:
            self.df = pd.DataFrame(data, columns=["PtIndex", "xpos", "Current"], dtype='float')
            self.df = self.df.values

            self.df[:, 1] = self.df[:, 1] * 1E6  # m --> um
            self.df[:, 2] = self.df[:, 2] * 1E9  # A --> nA

            self.nptsy = self.df[self.df[:, 1] == 0]
            self.nptsy = len(self.nptsy)
            self.nptsx = int(len(self.df) / self.nptsy)

            self.labelXdim2.config(text=self.nptsx)
            self.labelYdim2.config(text=self.nptsy)

            # Set up grids for plotting
            self.xpos0 = np.unique(self.df[:, 1])
            self.ypos0 = np.linspace(np.amin(self.xpos0), np.amax(self.xpos0), self.nptsy)
            self.currents0 = self.df[:, 2]
            self.currents0 = self.currents0.reshape(self.nptsy, self.nptsx)

            del self.df

        except:
            print("Integer values for the number of points required.")

    def import_3d_secmx(self, filepath):
        """Imports data at the filepath address. Formats data to that required by the ReshapeData() method.
        This method is designed to read 3D SECM image files of ASCII SECMx encoding (.img)
        PLEASE NOTE THAT THIS METHOD CANNOT READ BINARY ENCODED FILES.
        SECMx is an SECM control software by Gunther Wittstock. https://uol.de/pc2/forschung/secm-tools/secmx"""
        data = []
        try:
            with open(filepath, 'r') as fh:
                for curline in fh:
                    # Ignore lines that do not contain data when reading data into global memory
                    if not (curline.startswith('|') or curline.startswith('[') or curline.startswith(
                            'p') or curline.startswith('F') or curline.startswith('R') or curline.startswith(
                            '\n') or len(curline) == 0):  # Read the line into memory if it is valid.
                        curline = curline.split()  # split-up the line into an array of the floating point data
                        data.append([curline[1], curline[3], curline[-1]])  # add [x/um, y/um, i/nA]
                fh.close()


        except:
            self.labelImport.config(text="Could not import file.")

        self.labelImport.config(text="File imported.")
        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")

        # Convert raw data to matrix
        try:
            df = pd.DataFrame(data, dtype=float)  # turn the data into a dataframe for sorting purposes
            df = df.sort_values(by=[1, 0])  # ensure the distances are in ascending order

            df = df.values  # cast the dataframe to a numpy array

            self.xpos0 = np.unique(df[:, 0])  # find the unique x values
            self.ypos0 = np.unique(df[:, 1])  # find the unique y values
            self.nptsx = len(self.xpos0)  # number of unique x points
            self.nptsy = len(self.ypos0)  # number of unique y points

            currents = df[:, 2]
            self.currents0 = np.reshape(currents, (self.nptsx, self.nptsy))  # format the 2D current map.
            # update the window
            self.labelXdim2.config(text=self.nptsx)
            self.labelYdim2.config(text=self.nptsy)

        except Exception as e:
            print("Error importing data: \n")
            print(e)

    def import_heka_mat(self, filepath):
        try:
            matdata = scipy.io.loadmat(filepath)
            # Delete non-data containing variables
            del matdata['__header__']
            del matdata['__globals__']
            del matdata['__version__']

            self.nptsy = len(matdata)
            data = []
            # Read once to determine dimensions
            for entry in matdata:
                trace = matdata[entry]
                self.xpos0 = trace[:, 0]
                self.nptsx = len(self.xpos0)

            # Read a second time to construct the appropriate table
            data = np.empty((self.nptsy, self.nptsx), dtype=float)
            count = 0
            for entry in matdata:
                trace = matdata[entry]
                data[count, :] = trace[:, 1]
                count = count + 1

            self.xpos0 = self.xpos0 * 1E6
            self.ypos0 = np.linspace(np.amin(self.xpos0), np.amax(self.xpos0), self.nptsy)
            self.currents0 = data * 1E9

            self.labelImport.config(text="File imported.")

        except:
            self.labelImport.config(text="Could not import file.")

        self.labelXdim2.config(text=self.nptsx)
        self.labelYdim2.config(text=self.nptsy)

    def import_biologic(self, filepath):
        try:
            data = []
            datastart = 0  # toggle for determining if reading point cloud

            with open(filepath, 'r') as fh:
                for curline in fh:
                    try:
                        curline = curline.split()
                        if curline == ['X', 'Y', 'Z']:
                            datastart = 1
                        if datastart == 1:
                            float(curline[0])  # check if line contains strings or numbers
                            data.append(curline)  # if number, add to dataframe
                    except:
                        pass  # if string, skip to next line

            self.df = pd.DataFrame(data, dtype='float')
            self.df = self.df.values

            self.df[:, 2] = self.df[:, 2] * 1E9  # A --> nA
            self.nptsx = self.df[self.df[:, 0] == 0]
            self.nptsx = len(self.nptsx)
            self.nptsy = int(len(self.df) / self.nptsx)

            self.xpos0 = np.unique(self.df[:, 0])
            self.xpos0 = self.xpos0 - np.amin(self.xpos0)
            self.ypos0 = np.unique(self.df[:, 1])
            self.ypos0 = self.ypos0 - np.amin(self.ypos0)
            self.currents0 = self.df[:, 2]
            self.currents0 = self.currents0.reshape(self.nptsy, self.nptsx)

            self.labelImport.config(text="File imported.")
            self.labelXdim2.config(text=self.nptsx)
            self.labelYdim2.config(text=self.nptsy)


        except:
            self.labelImport.config(text="Could not import file.")

    def import_ch_instruments(self, filepath):
        try:
            data = []
            datastart = 0  # toggle for determining if reading point cloud

            with open(filepath, 'r') as fh:
                for curline in fh:
                    try:
                        curline = curline.split(',')
                        if curline == ['X/um', ' Y/um', ' Current/A\n']:
                            datastart = 1
                        if datastart == 1:
                            float(curline[0])  # check if line contains strings or numbers
                            data.append(curline)  # if number, add to dataframe
                    except:
                        pass  # if string, skip to next line

            self.df = pd.DataFrame(data, dtype='float')
            self.df = self.df.values

            self.df[:, 2] = self.df[:, 2] * 1E9  # A --> nA
            self.nptsx = self.df[self.df[:, 0] == 0]
            self.nptsx = len(self.nptsx)
            self.nptsy = int(len(self.df) / self.nptsx)

            self.xpos0 = np.unique(self.df[:, 0])
            self.xpos0 = self.xpos0 - np.amin(self.xpos0)
            self.ypos0 = np.unique(self.df[:, 1])
            self.ypos0 = self.ypos0 - np.amin(self.ypos0)
            self.currents0 = self.df[:, 2]
            self.currents0 = self.currents0.reshape(self.nptsy, self.nptsx)
            self.currents0 = self.currents0 * (-1)  # polarographic --> IUPAC convention

            self.labelImport.config(text="File imported.")
            self.labelXdim2.config(text=self.nptsx)
            self.labelYdim2.config(text=self.nptsy)

        except:
            self.labelImport.config(text="Could not import file.")

    def import_sensolytics(self, filepath):
        data = []
        header = []
        index = 0

        try:
            with open(filepath, 'r') as fh:
                for curline in fh:
                    index = index + 1
                    if index <= 23:
                        try:
                            curline = curline.split(':')
                            header.append(curline)
                        except:
                            pass
                    if index > 23:
                        try:
                            curline = curline.split(',')
                            float(curline[0])
                            data.append(curline)
                        except:
                            pass
                fh.close()

            self.df = pd.DataFrame(data, columns=['X', 'Xrel', 'Y', 'Yrel', 'Z', 'Zrel', 'Ch1', 'Ch2'], dtype=float)
            del self.df['Ch2']
            self.df = self.df.values

            self.nptsx = int(header[5][1].strip(' \n')) + 1
            self.nptsy = int(header[6][1].strip(' \n')) + 1

            self.xpos0 = np.unique(self.df[:, 1])
            self.ypos0 = np.unique(self.df[:, 3])
            self.currents0 = self.df[:, 6]
            self.currents0 = self.currents0.reshape(self.nptsy, self.nptsx)

            self.labelImport.config(text="File imported.")
            self.labelXdim2.config(text=self.nptsx)
            self.labelYdim2.config(text=self.nptsy)

        except:
            self.labelImport.config(text="Could not import file.")

    def import_par(self, filepath):
        try:
            data = []
            header = []
            index = 0
            with open(filepath) as fh:
                # Read the first time, pull header (x-dimensions)
                for curline in fh:
                    try:
                        index += 1
                        if index == 7:
                            header.append(curline.split(','))
                        else:
                            pass
                    except:
                        pass
                fh.close()

                # Read the second time, pull last column (y-dimensions)
                # Note: there is no header to this column, which confuses the third import
            with open(filepath) as fh:
                data = pd.read_csv(fh, header=6, dtype=float)
                self.ypos0 = data.iloc[:, -1]
                fh.close()

            with open(self.filepath) as fh:
                # Read the second time, import data to table
                data = pd.read_csv(fh, header=6, index_col=False)
                fh.close()

        except:
            self.labelImport.config(text="Could not import file.")

        # Process data into consistent form needed for ReshapeData
        try:
            # conversion of all quantities to numpy arrays
            self.xpos0 = np.transpose(np.array(header, dtype=float))
            self.xpos0 = np.unique(self.xpos0)
            self.xpos0 = self.xpos0 * 1E3  # mm --> um
            self.ypos0 = self.ypos0.values
            self.ypos0 = self.ypos0 * 1E3  # mm --> um
            self.currents0 = data.values
            self.currents0 = self.currents0 * 1E3  # uA --> nA

            self.nptsx = len(self.xpos0)
            self.nptsy = len(self.ypos0)

            self.labelImport.config(text="File imported.")
            self.labelXdim2.config(text=self.nptsx)
            self.labelYdim2.config(text=self.nptsy)

        except:
            self.labelImport.config(text="Error processing file.")

    """
    Looking to extend the import file functionality to support a different file type?
    The ReshapeData function assumes the following is present after the ImportFile function has run:
        > self.xpos0, self.ypos0 = 2 separate 1D numpy arrays containing unique x and y values respectively in µm
        > self.nptsx, self.nptsy = 2 separate integers containing the number of x and y points respectively
        > self.currents0 = 2D numpy array containing current values in nA.
        > self.nptsx, self.nptsy = Number of points in x and y directions

    """

    def ReshapeData(self):
        # Reset all data to original import to prevent repeating math operations
        self.xpos = self.xpos0.copy()
        self.ypos = self.ypos0.copy()
        self.currents = self.currents0.copy()

        # Unit conversions; create xposG/yposG variables only to be used for graphs
        # (if converting self.xpos variable directly, errors in edge detection)
        if self.distanceVar.get() == "nm":
            self.xposG = self.xpos.copy() * 1E3  # um --> nm
            self.yposG = self.ypos.copy() * 1E3
        elif self.distanceVar.get() == "mm":
            self.xposG = self.xpos.copy() / 1E3  # um --> mm
            self.yposG = self.ypos.copy() / 1E3  # um --> mm
        else:
            self.xposG = self.xpos.copy()
            self.yposG = self.ypos.copy()

        ### Slope correction
        # X-Slope correction
        if self.slopeXVar.get() == 'None':
            pass
        elif self.slopeXVar.get() == 'Y = 0':
            xslope0 = np.polyfit(self.xpos, self.currents[0, :], 1)
            for i in range(0, (self.currents.shape[1])):
                self.currents[:, i] = self.currents0[:, i] - xslope0[0] * (self.xpos[i] - self.xpos[0])
        elif self.slopeXVar.get() == 'Y = Max':
            xslopemax = np.polyfit(self.xpos, self.currents0[-1, :], 1)
            for i in range(0, (self.currents0.shape[1])):
                self.currents[:, i] = self.currents0[:, i] - xslopemax[0] * (self.xpos[i] - self.xpos[0])
        # Y-Slope correction
        if self.slopeYVar.get() == 'None':
            pass
        elif self.slopeYVar.get() == 'X = 0':
            yslope0 = np.polyfit(self.ypos, self.currents[:, 0], 1)
            for i in range(0, (self.currents.shape[0])):
                self.currents[i, :] = self.currents0[i, :] - yslope0[0] * (self.ypos[i] - self.ypos[0])
        elif self.slopeYVar.get() == 'X = Max':
            yslopemax = np.polyfit(self.ypos, self.currents[:, -1], 1)
            for i in range(0, (self.currents.shape[0])):
                self.currents[i, :] = self.currents0[i, :] - yslopemax[0] * (self.ypos[i] - self.ypos[0])

        ## Normalization; if deselected, iss = 1 (no change)
        # No normalization
        if self.checkNormalize.var.get() == 0:
            self.iss = 1
        # Experimental normalization
        elif self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 1:
            self.iss = float(self.entryIssExp.get())
        # Theoretical normalization
        elif self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 0:
            beta = 1 + (0.23 / ((((float(self.entryRg.get())) ** 3) - 0.81) ** 0.36))
            self.iss = 4 * 1E9 * 96485 * beta * (float(self.entryDiff.get())) * (
                        (float(self.entryRadius.get())) / 1E6) * (float(self.entryConc.get()))
            self.labelTheoIssValue.config(text="{0:.3f}".format(self.iss))
        else:
            pass

        self.currents = np.divide(self.currents, self.iss)

        # Convert current between nA/uA/pA if not normalized
        if self.checkNormalize.var.get() == 0:
            if self.currentVar.get() == "nA":
                pass
            elif self.currentVar.get() == "µA":
                self.currents = self.currents / 1E3
            elif self.currentVar.get() == "pA":
                self.currents = self.currents * 1E3
        else:
            pass

        self.currents = self.currents.reshape(self.nptsy, self.nptsx)

        # Update interpolated dimension labels
        if self.checkEdges.var.get() == 1:
            self.labelXinterp2.config(text="Processing...")
            self.labelYinterp2.config(text="Processing...")
            self.labelPlot.config(text="Processing...")

        # Set up grids for plotting
        self.ypos_int = (np.amax(self.xpos) - np.amin(self.xpos)) / (self.nptsy - 1)
        self.ypos = np.arange(np.amin(self.xpos), (np.amax(self.xpos) + self.ypos_int), self.ypos_int)
        self.xpos_grid, self.ypos_grid = np.meshgrid(self.xpos, self.ypos)

        # Update figure with SECM image
        try:
            self.ax1.clear()
            self.ax1.set_aspect(1)
            self.cb.remove()

            # Colormap selection
            if self.colormapVar.get() == 'RdYlBu':
                self.img = self.ax1.pcolormesh(self.xposG, self.yposG, self.currents, cmap=cm.get_cmap('RdYlBu_r'))
            elif self.colormapVar.get() == 'jet':
                self.img = self.ax1.pcolormesh(self.xposG, self.yposG, self.currents, cmap=cm.get_cmap('jet'))
            elif self.colormapVar.get() == 'coolwarm':
                self.img = self.ax1.pcolormesh(self.xposG, self.yposG, self.currents, cmap=cm.get_cmap('coolwarm'))
            elif self.colormapVar.get() == 'grayscale':
                self.img = self.ax1.pcolormesh(self.xposG, self.yposG, self.currents, cmap=cm.get_cmap('Greys'))
            else:
                pass

                # X-Y axis limits; try/except loops, except loop will take place if entry field empty or invalid
            try:
                self.ax1.set_xlim([float(self.entryXmin.get()), float(self.entryXmax.get())])
            except:
                pass
            try:
                self.ax1.set_ylim([float(self.entryYmin.get()), float(self.entryYmax.get())])
            except:
                pass
            try:
                self.img.set_clim([float(self.entryZmin.get()), float(self.entryZmax.get())])
            except:
                pass

            # Setup colormap, make same size as y-axis
            divider = make_axes_locatable(self.ax1)
            cax = divider.append_axes("right", size="5%", pad=0.1)
            self.cb = self.fig.colorbar(self.img, cax=cax)

            # Create axis labels with appropriate units
            if self.checkNormalize.var.get() == 1:
                self.cb.set_label('Normalized Current')
            else:
                self.cb.set_label('Current ({})'.format(self.currentVar.get()))

            self.ax1.set_xlabel('X ({})'.format(self.distanceVar.get()))
            self.ax1.set_ylabel('Y ({})'.format(self.distanceVar.get()))
            self.canvas.draw()

            self.buttonSave.config(state="normal")

        except:
            print("Data imported, call to update canvas failed.")

        # Detect edges
        if self.checkEdges.var.get() == 1:

            # The Following interpolation does not play nice with negative x,y positions very much.
            self.xposa = self.xpos - np.amin(self.xpos)  # Adjust the x-positions so that there are no negative values
            self.yposa = self.ypos - np.amin(self.ypos)  # Adjust the y-positions so that there are no negative values

            # Create df to be compatible with edge detection algorithm
            ypos_int = np.amax(self.xposa) / ((self.nptsy) - 1)
            self.df = np.reshape(self.currents, (self.nptsx * self.nptsy))
            self.dfycol = np.linspace(0, ((self.nptsx * self.nptsy) - 1), (self.nptsx * self.nptsy))

            # duct tape hack so that point where the floor function below get assigned to the correct row
            modcol = np.remainder(self.dfycol, self.nptsx)
            for i in range(0, len(modcol)):
                if modcol[i] == 0:
                    self.dfycol[i] = self.dfycol[i] + 1
            self.dfycol = ypos_int * (np.floor(np.divide(self.dfycol, self.nptsx)))

            self.df = np.vstack((numpy.matlib.repmat(self.xposa, 1, self.nptsy), self.df))
            self.df = np.vstack((self.dfycol, self.df))
            self.df = self.df.T

            try:
                # Set up evenly spaced interpolation grids for edge detection
                try:
                    # Check if already evenly spaced; if yes, do nothing; if no, create grid @ 1 pt/um level
                    if self.nptsx > self.nptsy:
                        xpos_interp = np.linspace(np.amin(self.xposa), np.amax(self.xposa), np.amax(self.xposa) + 1)
                        ypos_interp = xpos_interp
                    elif self.nptsx < self.nptsy:
                        xpos_interp = np.linspace(np.amin(self.yposa), np.amax(self.yposa), np.amax(self.yposa) + 1)
                        ypos_interp = xpos_interp
                    else:
                        xpos_interp = self.xposa
                        ypos_interp = xpos_interp
                    xpos_unigrid, ypos_unigrid = np.meshgrid(xpos_interp, ypos_interp)

                    # Interpolate to prepare for edge detection
                    currents_interp = griddata((self.df[:, 1], self.df[:, 0]), self.df[:, 2],
                                               (xpos_unigrid, ypos_unigrid), method='cubic')
                except:
                    print("Error interpolating data to uniform grid.")

                currents_norm = (currents_interp - np.amin(currents_interp)) / (
                            np.amax(currents_interp) - np.amin(currents_interp))
                self.currents_edges = feature.canny(currents_norm)

                # Unit conversions
                if self.distanceVar.get() == "mm":
                    xpos_interp = xpos_interp.copy() / 1E3
                    ypos_interp = ypos_interp.copy() / 1E3
                elif self.distanceVar.get() == "nm":
                    xpos_interp = xpos_interp.copy() * 1E3
                    ypos_interp = ypos_interp.copy() * 1E3
                else:
                    pass

            except:
                print("Error detecting edges.")
        else:
            pass

        # Update figure with detected edges
        try:
            if self.checkEdges.var.get() == 1:
                self.labelXinterp2.config(text=len(xpos_interp))
                self.labelYinterp2.config(text=len(ypos_interp))
                self.labelPlot.config(text="")

                self.ax2.clear()

                self.edge = self.ax2.pcolormesh(xpos_interp, ypos_interp, self.currents_edges,
                                                cmap=cm.get_cmap('binary'))
                self.ax2.set_xlabel('X ({})'.format(self.distanceVar.get()))

                # X-Y axis limits; try/except loops, except loop will take place if entry field empty or invalid
                try:
                    self.ax2.set_xlim([float(self.entryXmin.get()), float(self.entryXmax.get())])
                except:
                    pass
                try:
                    self.ax2.set_ylim([float(self.entryYmin.get()), float(self.entryYmax.get())])
                except:
                    pass

                self.canvas.draw()

            else:
                self.labelXinterp2.config(text="N/A")
                self.labelYinterp2.config(text="N/A")
        except:
            print("Call to update canvas (detected edges) failed.")

        self.buttonExport.config(state="normal")

    def BoxesSelected(self):
        # Enable/disable 'to experimental iss?' checkbox
        if self.checkNormalize.var.get() == 1:
            self.checkNormalizeExp.config(state="normal")
        else:
            self.checkNormalizeExp.config(state="disabled")

        # Enable/disable entry fields for calculating theoretical iss
        if self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 0:
            self.entryRadius.config(state="normal")
            self.entryRg.config(state="normal")
            self.entryConc.config(state="normal")
            self.entryDiff.config(state="normal")
        else:
            self.entryRadius.config(state="disabled")
            self.entryRg.config(state="disabled")
            self.entryConc.config(state="disabled")
            self.entryDiff.config(state="disabled")

        # Enable/disable entry fields for inputting experimental iss
        if self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 1:
            self.entryIssExp.config(state="normal")
        else:
            self.entryIssExp.config(state="disabled")

    def SaveFig(self):
        try:
            print("Save requested.")

            # If edges detected, save full image
            if self.checkEdges.var.get() == 1:
                self.fig.savefig(fname=asksaveasfilename(
                    initialdir="/", title="Select file",
                    filetypes=(("png", "*.png"), ("all files", "*.*"))), dpi=400)
                self.labelPlot.config(text="Figure saved.")
            # If no edges detected, only save SECM image
            else:
                # Determine dimensions of first subplot
                extent = self.ax1.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())

                # Save the figure, expand the extent by 50% in x and 20% in y to include axis labels and colorbar
                self.fig.savefig(fname=asksaveasfilename(
                    initialdir="/", title="Select file",
                    filetypes=(("png", "*.png"), ("all files", "*.*"))),
                    bbox_inches=extent.expanded(1.6, 1.3), dpi=400)
                self.labelPlot.config(text="Figure saved.")

        except:
            self.labelPlot.config(text="Error saving figure to file.")

    def SaveTxt(self):

        # Prompt user to select a file name, open a text file with that name
        export = asksaveasfilename(initialdir="/",
                                   filetypes=[("TXT File", "*.txt")],
                                   title="Choose a file.")
        fh = open(export + ".txt", "w+")

        # Header lines: print details about the file and data treatment
        fh.write("Original file: {} \n".format(self.filename))
        fh.write("Units of current: {} \n".format(self.currentVar.get()))
        fh.write("Units of distance: {} \n".format(self.distanceVar.get()))

        if self.statusNormalize.get() == 1:
            if self.statusNormalizeExp.get() == 1:
                normalstatus = 'Experimental iss'
                iss = self.entryIssExp.get()
            else:
                normalstatus = 'Theoretical iss'
                iss = self.iss

        else:
            normalstatus = 'No'
            iss = 'N/A'
        fh.write("Currents normalized: {} \n".format(normalstatus))
        fh.write("Steady state current used (nA): {} \n".format(iss))

        if self.slopeXVar.get() == 'None':
            xslope = 'No'
        else:
            xslope = 'Yes'

        if self.slopeYVar.get() == 'None':
            yslope = 'No'
        else:
            yslope = 'Yes'

        fh.write("X-slope corrected: {} \n".format(xslope))
        fh.write("Y-slope corrected: {} \n".format(yslope))
        fh.write(" \n")

        # Print 1D array of x points
        fh.write("X pts: {} \n".format(self.nptsx))
        np.savetxt(fh, self.xposG, delimiter=',', fmt='%1.4e')
        fh.write(" \n")

        # Print 1D array of y points
        fh.write("Y pts: {} \n".format(self.nptsy))
        np.savetxt(fh, self.yposG, delimiter=',', fmt='%1.4e')
        fh.write(" \n")

        # Print 2D array of currents
        fh.write("Matrix of currents:  {} \n".format(self.nptsx * self.nptsy))
        np.savetxt(fh, self.currents, delimiter=',', fmt='%1.4e')
        fh.write(" \n")

        # Print 2D array of detected edges
        if self.statusEdges.get() == 1:
            fh.write("Detected edges: \n")
            np.savetxt(fh, self.currents_edges, delimiter=',', fmt='%i')
        else:
            pass

        # Upate label to indicate successful save
        self.labelPlot.config(text="Data exported.")

        fh.close()

    def ResetWindow(self):
        print("Reset requested.")
        # Get rid of old data:
        try:
            del self.df
            del self.xpos0
            del self.ypos0
            del self.currents0
        except:
            pass

        # Recreate dummy data
        xpos = np.array([0, 1])
        ypos = np.array([0, 1])
        currents = np.array([[0, 1], [0, 1]])

        xpos_interp = np.array([0, 1])
        ypos_interp = np.array([0, 1])
        currents_edges = np.array([[0, 1], [0, 1]])

        # Reset graph
        self.ax1.clear()
        self.ax1.set_aspect(1)
        self.cb.remove()
        #        self.fig.subplots_adjust(left=0.07,right=1.0)
        self.img = self.ax1.pcolormesh(xpos, ypos, currents, cmap=cm.get_cmap('RdYlBu_r'))
        divider = make_axes_locatable(self.ax1)
        cax = divider.append_axes("right", size="5%", pad=0.1)
        self.cb = self.fig.colorbar(self.img, cax=cax)
        self.cb.set_label('Current (nA)')
        self.ax1.set_xlabel('X (µm)')
        self.ax1.set_ylabel('Y (µm)')
        self.canvas.draw()
        self.ax2.clear()
        self.fig.subplots_adjust(left=0.07, right=1.0)
        self.edge = self.ax2.pcolormesh(xpos_interp, ypos_interp, currents_edges, cmap=cm.get_cmap('binary'))
        self.ax2.set_xlabel('X (µm)')
        self.canvas.draw()

        # Reset labels and buttons to default states

        # Buttons
        self.buttonImport.config(state="disabled")
        self.buttonPlot.config(state="disabled")
        self.buttonSave.config(state="disabled")
        self.textVar.set('None')
        self.buttonExport.config(state="normal")

        # Labels
        self.labelFile.config(text="")
        self.labelImport.config(text="Select file to continue.")
        self.labelXdim2.config(text="")
        self.labelYdim2.config(text="")
        self.labelXinterp2.config(text="")
        self.labelYinterp2.config(text="")
        self.labelPlot.config(text="Import data to begin.")
        self.labelTheoIssValue.config(text="")
        self.labelXCursor.config(text="X : ")
        self.labelYCursor.config(text="Y : ")

        # Checkboxes
        self.checkNormalizeExp.config(state="disabled")
        self.checkNormalize.var.set(0)
        self.checkNormalizeExp.var.set(0)
        self.checkEdges.var.set(0)

        # Entries
        self.entryIssExp.delete(0, "end")
        self.entryIssExp.config(state="disabled")
        self.entryRadius.delete(0, "end")
        self.entryRadius.config(state="disabled")
        self.entryRg.delete(0, "end")
        self.entryRg.config(state="disabled")
        self.entryConc.delete(0, "end")
        self.entryConc.config(state="disabled")
        self.entryDiff.delete(0, "end")
        self.entryDiff.config(state="disabled")
        self.entryXmin.delete(0, "end")
        self.entryXmax.delete(0, "end")
        self.entryYmin.delete(0, "end")
        self.entryYmax.delete(0, "end")
        self.entryZmin.delete(0, "end")
        self.entryZmax.delete(0, "end")
