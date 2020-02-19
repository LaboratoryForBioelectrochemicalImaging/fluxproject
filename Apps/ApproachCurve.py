# GUI
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import ttk as ttk

# Numerical analysis
import numpy as np
import pandas as pd
import scipy.io # support for matlab workspaces
import scipy.optimize # nonlinear curve fitting

# Plotting
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # figure handler for embeddable plots
from matplotlib.figure import Figure

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


class PACApp:
    """Handles data from approach curve experiments.
        __init__ will initialize generate the tkinter window
        SelectFile allows for file selection
        ImportFile reads the selected file into memory
        ReshapeData does everything after the 'plot' button in pressed. This method will be broken up into smaller methods in the near future.
    """
    def __init__(self, master):
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

        # set min column sizes to prevent excessive resizing
        for i in range(0, 8):
            frameBase.columnconfigure(i, minsize=120)
            framePlot.columnconfigure(i, minsize=110)

        ###### Base frame #####
        # Intro
        labelIntro = tk.Label(frameBase, text="Import experimental data to be plotted.")
        labelIntro.grid(row=0, column=0, columnspan=6, padx=20, pady=10, sticky="WS")

        # Select file
        self.buttonFile = tk.Button(frameBase, text="Select File", command=self.SelectFile)
        self.buttonFile.grid(row=1, column=1, sticky="W" + "E", padx=10, pady=5)
        self.labelFile = tk.Label(frameBase, text="")
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

        # Label for number of points in data set (before processing)
        labelNpts = tk.Label(frameBase, text="# pts (original):")
        labelNpts.grid(row=1, column=3, padx=10, sticky="E")
        self.labelNpts2 = tk.Label(frameBase, text="")
        self.labelNpts2.grid(row=1, column=4, padx=10, sticky="W")

        # Label for number of points in data set (after processing)
        labelNpts3 = tk.Label(frameBase, text="# pts (post-processing):")
        labelNpts3.grid(row=2, column=3, padx=10, sticky="E")
        self.labelNpts4 = tk.Label(frameBase, text="")
        self.labelNpts4.grid(row=2, column=4, padx=10, sticky="W")

        # Label for zero tip-substrate distance dropdown
        labelZerod = tk.Label(frameBase, text="Method of determining d = 0")
        labelZerod.grid(row=1, column=5, sticky="W", padx=10)

        # Dropdown menu for method of determining zero tip-substrate distance
        # Create a stringvar which will contian the eventual choice
        self.zerodVar = tk.StringVar(master)
        self.zerodVar.set('First point with data')  # set the default option
        # Dictionary with options
        choices = {'First point with data', 'First derivative analysis', 'No calibration'}
        popupMulticycle = tk.OptionMenu(frameBase, self.zerodVar, *choices)
        popupMulticycle.configure(width=20)
        popupMulticycle.grid(row=2, column=5, sticky="W", padx=10)
        # link function to change dropdown
        self.zerodVar.trace('w', self.change_dropdown)

        ###### Analytics frame #####
        # Intro
        labelAnalytics = tk.Label(frameAnalytics, text="Customize the data treatment.")
        labelAnalytics.grid(row=0, column=0, padx=20, pady=10, sticky="WS")

        # Toggle for normalizing currents
        self.statusNormalize = tk.IntVar()
        self.checkNormalize = tk.Checkbutton(frameAnalytics, text="Normalize?", variable=self.statusNormalize,
                                             command=self.BoxesSelected)
        self.checkNormalize.var = self.statusNormalize
        self.checkNormalize.grid(row=1, column=0, sticky="E", padx=10)

        # Toggle for experimental normalization
        self.statusNormalizeExp = tk.IntVar()
        self.checkNormalizeExp = tk.Checkbutton(frameAnalytics, state="disabled", text="Experimental iss?",
                                                variable=self.statusNormalizeExp, command=self.BoxesSelected)
        self.checkNormalizeExp.var = self.statusNormalizeExp
        self.checkNormalizeExp.grid(row=2, column=0, sticky="E", padx=10)

        # Input for accepting electrode parameters for theoretical iss
        labelRadius = tk.Label(frameAnalytics, text="Radius (µm)")
        labelRadius.grid(row=1, column=1, padx=10, sticky="W")
        self.entryRadius = tk.Entry(frameAnalytics)
        self.entryRadius.grid(row=2, column=1, padx=10, sticky="W")

        labelRg = tk.Label(frameAnalytics, text="Rg")
        labelRg.grid(row=1, column=2, padx=10, sticky="W")
        self.entryRg = tk.Entry(frameAnalytics)
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

        # Input for accepting experimental iss
        labelIssExp = tk.Label(frameAnalytics, text="Expermental iss (nA)")
        labelIssExp.grid(row=1, column=6, padx=10, sticky="W")
        self.entryIssExp = tk.Entry(frameAnalytics, state="disabled")
        self.entryIssExp.grid(row=2, column=6, padx=10, sticky="W")

        # Labels only to be used for error reporting
        self.labelRadiusErr = tk.Label(frameAnalytics, text="")
        self.labelRadiusErr.grid(row=3, column=1, padx=10, sticky="W")
        self.labelRgErr = tk.Label(frameAnalytics, text="")
        self.labelRgErr.grid(row=3, column=2, padx=10, sticky="W")
        self.labelConcErr = tk.Label(frameAnalytics, text="")
        self.labelConcErr.grid(row=3, column=3, padx=10, sticky="W")
        self.labelDiffErr = tk.Label(frameAnalytics, text="")
        self.labelDiffErr.grid(row=3, column=4, padx=10, sticky="W")
        self.labelIssExpErr = tk.Label(frameAnalytics, text="")
        self.labelIssExpErr.grid(row=3, column=6, padx=10, sticky="W")

        # Toggle for fitting Rg
        self.statusFitRg = tk.IntVar()
        self.checkFitRg = tk.Checkbutton(frameAnalytics, text="Fit Rg?", variable=self.statusFitRg,
                                         command=self.BoxesSelected)
        self.checkFitRg.var = self.statusFitRg
        self.checkFitRg.grid(row=4, column=1, rowspan=2, sticky="E", padx=10)

        labelEstRg = tk.Label(frameAnalytics, text="Estimated Rg")
        labelEstRg.grid(row=4, column=2, padx=10, sticky="W")
        self.labelEstRg2 = tk.Label(frameAnalytics, text="")
        self.labelEstRg2.grid(row=5, column=2, padx=10, sticky="W")

        # Toggle for fitting kappa
        self.statusFitKappa = tk.IntVar()
        self.checkFitKappa = tk.Checkbutton(frameAnalytics, text="Fit kappa?", variable=self.statusFitKappa,
                                            command=self.BoxesSelected)
        self.checkFitKappa.var = self.statusFitKappa
        self.checkFitKappa.grid(row=4, column=3, rowspan=2, sticky="E", padx=10)

        labelEstKappa = tk.Label(frameAnalytics, text="Estimated kappa")
        labelEstKappa.grid(row=4, column=4, padx=10, sticky="W")
        self.labelEstKappa2 = tk.Label(frameAnalytics, text="")
        self.labelEstKappa2.grid(row=5, column=4, padx=10, sticky="W")

        labelEstK = tk.Label(frameAnalytics, text="Estimated k (cm/s)")
        labelEstK.grid(row=4, column=5, padx=10, sticky="W")
        self.labelEstK2 = tk.Label(frameAnalytics, text="")
        self.labelEstK2.grid(row=5, column=5, padx=10, sticky="W")

        ####### Formatting tab ##########
        # Intro
        labelFormatting = tk.Label(frameFormatting, text="Customize the formatting of the graph.")
        labelFormatting.grid(row=0, column=0, padx=20, pady=5, columnspan=3, sticky="W")

        # Toggle for displaying pure feedback lines
        self.statusFeedback = tk.IntVar()
        self.checkFeedback = tk.Checkbutton(frameFormatting, text="Show pure feedback cases?",
                                            variable=self.statusFeedback)
        self.checkFeedback.var = self.statusFeedback
        self.checkFeedback.grid(row=1, column=1, sticky="E", padx=10)

        # Dropdown menu for units on distance
        # Label for dropdown menu
        labelDistance = tk.Label(frameFormatting, text="Units (Distance)")
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

        labelXmin2 = tk.Label(frameFormatting, text="Xmin (norm.)")
        labelXmin2.grid(row=1, column=5, sticky="W", padx=10)
        self.labelXmin3 = tk.Label(frameFormatting, text="")
        self.labelXmin3.grid(row=2, column=5, sticky="W", padx=10)

        labelXmax2 = tk.Label(frameFormatting, text="Xmax (norm.)")
        labelXmax2.grid(row=3, column=5, sticky="W", padx=10)
        self.labelXmax3 = tk.Label(frameFormatting, text="")
        self.labelXmax3.grid(row=4, column=5, sticky="W", padx=10)

        labelYmin = tk.Label(frameFormatting, text="Ymin")
        labelYmin.grid(row=1, column=6, sticky="W", padx=10)
        self.entryYmin = tk.Entry(frameFormatting)
        self.entryYmin.grid(row=2, column=6, sticky="W", padx=10)

        labelYmax = tk.Label(frameFormatting, text="Ymax ")
        labelYmax.grid(row=3, column=6, sticky="W", padx=10)
        self.entryYmax = tk.Entry(frameFormatting)
        self.entryYmax.grid(row=4, column=6, sticky="W", padx=10)

        labelYmin2 = tk.Label(frameFormatting, text="Ymin (norm.)")
        labelYmin2.grid(row=1, column=7, sticky="W", padx=10)
        self.labelYmin3 = tk.Label(frameFormatting, text="")
        self.labelYmin3.grid(row=2, column=7, sticky="W", padx=10)

        labelYmax2 = tk.Label(frameFormatting, text="Ymax (norm.)")
        labelYmax2.grid(row=3, column=7, sticky="W", padx=10)
        self.labelYmax3 = tk.Label(frameFormatting, text="")
        self.labelYmax3.grid(row=4, column=7, sticky="W", padx=10)

        # Data cursor setup
        labelCursor = tk.Label(frameFormatting, text="Data Cursor")
        labelCursor.grid(row=1, column=8, sticky="W", padx=10)
        self.labelXCursor = tk.Label(frameFormatting, text="X : ")
        self.labelXCursor.grid(row=2, column=8, sticky="W", padx=10)
        self.labelYCursor = tk.Label(frameFormatting, text="Y : ")
        self.labelYCursor.grid(row=3, column=8, sticky="W", padx=10)

        ###### Plot control ###########
        # Button for generating plot
        self.buttonPlot = tk.Button(framePlot, text="Plot Data", state="disabled", command=self.ReshapeData)
        self.buttonPlot.grid(row=0, column=1, rowspan=2, sticky="W" + "E")
        self.labelPlot = tk.Label(framePlot, text="Import data to begin.")
        self.labelPlot.grid(row=0, column=2, rowspan=2, sticky="W", padx=10)

        # Button for saving the plot
        self.buttonSave = tk.Button(framePlot, text="Save Figure", state="disabled", command=self.save_figure)
        self.buttonSave.grid(row=0, column=3, rowspan=2, sticky="W" + "E", padx=10)

        # Label for what portion to save
        labelSave = tk.Label(framePlot, text="Region to save: ")
        labelSave.grid(row=0, column=4, rowspan=3, sticky="E", padx=10)

        # Dropdown menu for what portion of graph to save
        # Create a stringvar which will contian the eventual choice
        self.figsaveVar = tk.StringVar(master)
        self.figsaveVar.set('Normalized PAC')  # set the default option
        # Dictionary with options
        choices = {'Normalized PAC', 'Non-normalized PAC', 'Both'}
        popupSave = tk.OptionMenu(framePlot, self.figsaveVar, *choices)
        popupSave.configure(width=20)
        popupSave.grid(row=0, column=5, sticky="W", padx=10)
        # link function to change dropdown
        self.figsaveVar.trace('w', self.change_dropdown)

        # Button for exporting to text file
        self.buttonExport = tk.Button(framePlot, text="Export Data", state="disabled", command=self.export_data_action)
        self.buttonExport.grid(row=0, column=6, sticky="W" + "E", padx=10)

        # Button for resetting window
        self.buttonReset = tk.Button(framePlot, text="Reset Window", command=self.ResetWindow)
        self.buttonReset.grid(row=0, column=7, padx=20, pady=10, sticky="W" + "E")

        ######### Bottom frame: Figure ###########

        # Setup data cursor
        def DataCursor(event):
            try:
                xcursor = event.xdata
                ycursor = event.ydata
                self.labelXCursor.config(text="X : {0:.3f}".format(xcursor))
                self.labelYCursor.config(text="Y : {0:.3f}".format(ycursor))
            except:
                pass

        # Start creating the plot
        self.fig = Figure(figsize=(9, 4), dpi=120)

        ### Left plot: Imported data ###
        self.ax1 = self.fig.add_subplot(121)
        #        self.img = self.ax1.plot(self.distances,self.currents)
        # Set labels
        self.ax1.set_xlabel('Distance (µm)')
        self.ax1.set_ylabel('Current (nA)')

        ### Right plot: Processed data ###
        self.ax2 = self.fig.add_subplot(122)
        #        self.img2 = self.ax2.plot(self.distances,self.currents)
        self.ax2.set_xlabel('Normalized distance')
        self.ax2.set_ylabel('Normalized current')

        # Create canvas object which contains frame
        self.fig.subplots_adjust(wspace=0.5, top=0.95, bottom=0.15)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frameBottom)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="S")
        self.canvas.mpl_connect('button_press_event', DataCursor)
        self.canvas.draw()

        self.last_dir = ""
        # values that will hold the status of the checkboxes at the time the data was last plotted
        self.statNorm = 0
        self.statFK = 0
        self.statFB = 0
        self.statNormXP = 0
        self.statFRg = 0

    def change_dropdown(*args):
        pass

    def SelectFile(self):
        try:
            self.filepath = askopenfilename(initialdir=self.last_dir + "/", title="Choose a file.")

            filename_start = self.filepath.rindex('/') + 1
            self.filename = self.filepath[filename_start:]
            self.last_dir = self.filepath[:filename_start - 1]

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
            elif self.filename[-3:] == 'zsc' or self.filename[-3:] == 'ZSC':
                self.textVar.set('SECMx')
            else:
                pass
            self.labelImport.config(text="Ready.")
        except:
            self.ResetWindow()

    def ImportFile(self):
        ## Check if manufacturer needed
        if self.filename[-3:] == 'txt' and self.textVar.get() == 'None':
            self.labelImport.config(text="Specify a manufacturer.")

        ### ASC / HEKA import ###
        elif self.filename[-3:] == 'asc':
            self.import_heka_asc(self.filepath)
        ### MAT / HEKA import ###
        elif self.filename[-3:] == 'mat':
            self.import_heka_mat(self.filepath)
        ### ZSC / SECMx import ###
        elif self.filename[-3:] == 'zsc' or self.filename[-3:] == 'ZSC':
            self.import_2d_secmx(self.filepath)
        ### TXT / Biologic import ###
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'Biologic':
            self.import_biologic(self.filepath)
        ### TXT / CH Instruments import ###
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'CH Instruments':
            self.import_ch_instruments(self.filepath)
        ### DAT / Sensolytics import ###
        elif self.filename[-3:] == 'dat':
            self.import_sensolytics(self.filepath)
        ### CSV / PAR import ###
        elif self.filename[-3:] == 'csv':
            self.import_par(self.filepath)

        else:
            self.labelImport.config(text="File type not supported.")

    """
    Looking to extend the import file functionality to support a different file type?
    The ReshapeData function assumes the following is present after the ImportFile function has run:
        > self.distances = 1D numpy array containing distances (in µm)
        >>> These are assumed to be positive values in order of increasing d.
        > self.currents = 1D numpy array containing currents (in nA) 
    """

    def import_heka_asc(self, filepath):
        # Import data file
        self.data = []
        try:
            with open(filepath, 'r') as fh:
                for curline in fh:
                    try:
                        curline = curline.split()  # split line into segments
                        float(curline[0])  # check if line contains strings or numbers
                        self.data.append(curline)  # if number, add to dataframe
                    except:
                        pass  # if string, skip to next line
                fh.close()

        except:
            self.labelImport.config(text="Could not import file.")

        ncols = len(self.data[0])

        self.labelImport.config(text="File imported.")
        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")

        # Convert raw data to matrix
        try:
            if ncols == 5:
                df = pd.DataFrame(self.data,
                                  columns=["PtIndex", "Distance (m)", "Current (A)", "Distance (m)", "Current (A)"],
                                  dtype=float)
            elif ncols == 3:
                df = pd.DataFrame(self.data, columns=["PtIndex", "Distance (m)", "Current (A)"], dtype=float)

            df = df.values
            try:
                df[:, 1] = df[:, 1] * 1E6  # m --> um
                df[:, 2] = df[:, 2] * 1E9  # A --> nA
                df[:, 4] = df[:, 4] * 1E9  # A --> nA
            except:
                pass

            # Determine number of pts
            nptsorig = len(df)

            # Create distance and current variables
            self.distances0 = df[:, 1]
            self.currents0 = df[:, 2]

            self.labelNpts2.config(text=nptsorig)
        except:
            print("Error importing data.")

    def import_heka_mat(self, filepath):
        self.zerodVar.set('First point with data')

        try:
            matdata = scipy.io.loadmat(filepath)

            # Delete non-data containing variables
            del matdata['__header__']
            del matdata['__globals__']
            del matdata['__version__']

            for entry in matdata:
                trace = matdata[entry]
                self.distances0 = trace[:, 0]
                self.currents0 = trace[:, 1]

            self.distances0 = self.distances0 * 1E6  # m --> um
            self.currents0 = self.currents0 * 1E9  # A --> nA

            nptsorig = len(self.distances0)
            self.labelNpts2.config(text=nptsorig)

            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")

        except:
            self.labelImport.config(text="Error importing file.")

    def import_2d_secmx(self, filepath):
        """Imports data at the filepath address. Formats data to that required by the ReshapeData() method.
        This method is designed to read 2D approach curve files of ASCII SECMx encoding (.zsc)
        PLEASE NOTE THAT THIS METHOD CANNOT READ BINARY ENCODED FILES.
        SECMx is an SECM control software by Gunther Wittstock. https://uol.de/pc2/forschung/secm-tools/secmx"""
        data = []
        use13 = False  # This variable determines which columns to read, the 2nd and 4th if True (for when an ADC column is in the datafile, or the 2nd and 3rd for when there is no ADC current column.
        try:
            with open(filepath, 'r') as fh:
                position_conversion_factor = 1.0 # multiplicative conversion factor to convert units to µm
                current_conversion_factor = 1.0 # multiplicative conversion factor to convert units to nA
                for curline in fh:

                    # Ignore lines that do not contain data when reading data into global memory
                    if not (curline.startswith('|') or curline.startswith('[') or curline.startswith('p') or curline.startswith('\n') or len(curline) == 0):  # Read the line into memory if it is valid.
                        curline = curline.split()  # split-up the line into an array of the floating point data
                        if use13:
                            data.append([float(curline[1])*position_conversion_factor, float(curline[3])*current_conversion_factor])
                        else:
                            data.append([float(curline[1])*position_conversion_factor, float(curline[2])*current_conversion_factor])
                    else:
                        # access the data table header to determine if an ADC column exists. If so, there will be 4 columns and use13 shall be true. otherwise, col1 and col2 should be used.
                        if curline.startswith('p'):
                            use13 = len(curline.split('\t')) == 4
                        # check to see is the line contains information about the units
                        if curline.rfind('Unit=') >= 0:
                            unit = curline[curline.rfind('Unit=') + 5:]
                            if unit.startswith('µm'):
                                position_conversion_factor = 1.0
                            elif unit.startswith('nm'):
                                position_conversion_factor = 0.001
                            elif unit.startswith('mm'):
                                position_conversion_factor = 1E3
                            elif unit.startswith('nA'):
                                current_conversion_factor = 1.0
                            elif unit.startswith('µA'):
                                current_conversion_factor = 1E3
                            elif unit.startswith('mA'):
                                current_conversion_factor = 1E6
                            elif unit.startswith('pA'):
                                current_conversion_factor = 0.001
                            elif unit.startswith('A'):
                                current_conversion_factor = 1E9
                            elif unit.startswith('cm'):
                                position_conversion_factor = 1E4
                            else:
                                print('panic: ' + unit.strip())
                fh.close()


        except:
            self.labelImport.config(text="Could not import file.")

        self.labelImport.config(text="File imported.")
        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")

        # Convert raw data to matrix
        try:
            df = pd.DataFrame(data, dtype=float)  # turn the data into a dataframe for sorting purposes
            df = df.sort_values(0)  # ensure the distances are in ascending order
            df = df.values  # cast the dataframe to a numpy array
            nptsorig = len(df)  # determine the number of points

            # Create distance and current variables
            self.distances0 = df[:, 0]  # copy the distances over
            self.currents0 = df[:, 1]  # copy the currents over

            self.labelNpts2.config(text=nptsorig)
        except Exception as e:
            print("Error importing data: \n")

    def import_biologic(self, filepath):
        self.zerodVar.set('No calibration')

        # Import file
        self.data = []
        try:
            with open(filepath, 'r') as fh:
                for curline in fh:
                    try:
                        curline = curline.split()
                        float(curline[0])
                        self.data.append(curline)
                    except:
                        pass
                fh.close()
        except:
            self.labelImport.config(text="Could not import file.")

        # Process file into consistent format for ReshapeData
        df = pd.DataFrame(self.data, columns=["Time (s)", "Current (A)"], dtype=float)
        df = df.values

        df[:, 1] = df[:, 1] * 1E9  # A --> nA

        # Update labels
        self.labelImport.config(text="File imported.")
        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")

        # Convert raw data to matrix
        try:
            df = pd.DataFrame(self.data, columns=["Distance (µm)", "Current (A)"], dtype='float')
            df = df.values
            df[:, 1] = df[:, 1] * 1E9  # A --> nA

            # Determine number of pts
            nptsorig = len(df)

            # Create distance and current variables
            self.distances0 = df[:, 0]
            self.distances0 = self.distances0 - np.amin(self.distances0)
            self.currents0 = df[:, 1]

            self.labelNpts2.config(text=nptsorig)
        except:
            print("Error importing data.")

    def import_ch_instruments(self, filepath):
        try:
            self.data = []
            datastart = 0  # toggle for determining if reading point cloud
            index = 0

            # First read to extract data
            with open(filepath, 'r') as fh:
                for curline in fh:
                    try:
                        curline = curline.split(',')
                        if curline == ['Distance/um', ' Current/A\n']:
                            datastart = 1
                        if datastart == 1:
                            float(curline[0])  # check if line contains strings or numbers
                            self.data.append(curline)  # if number, add to dataframe
                    except:
                        pass  # if string, skip to next line
                fh.close()

            # Second read to extract constant potential
            with open(filepath, 'r') as fh2:
                for curline2 in fh2:
                    index = index + 1
                    if index == 9:  # The scan rate info can be found in this line
                        conpot = curline2.split('=')
                        conpot = float(conpot[1].strip('\n'))
                    else:
                        pass

            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")

            # Convert raw data to matrix
            try:
                df = pd.DataFrame(self.data, columns=["Distance (µm)", "Current (A)"], dtype='float')
                df = df.values
                df[:, 1] = df[:, 1] * 1E9  # A --> nA

                # Determine number of pts
                nptsorig = len(df)

                # Create distance and current variables
                self.distances0 = df[:, 0]
                self.distances0 = np.amax(self.distances0) - self.distances0
                self.currents0 = df[:, 1]
                self.currents0 = self.currents0 * (-1)  # polarographic --> IUPAC convention

                self.labelNpts2.config(text=nptsorig)

            except:
                self.labelImport.config(text="Error importing file.")
        except:
            self.labelImport.config(text="Error importing file.")

    def import_sensolytics(self, filepath):
        try:
            self.data = []
            header = []
            index = 0

            with open(filepath, 'r') as fh:
                for curline in fh:
                    index = index + 1
                    if index <= 15:
                        try:
                            curline = curline.split(':')
                            header.append(curline)
                        except:
                            pass
                    if index > 15:
                        try:
                            curline = curline.split(',')
                            float(curline[0])
                            self.data.append(curline)
                        except:
                            pass
                fh.close()

            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")

            df = pd.DataFrame(self.data, columns=['Distance (um)', 'Index', 'Current (nA)', 'NA'], dtype=float)
            del df['NA']
            df = df.values

            nptsorig = len(df)

            self.distances0 = df[:, 0]
            self.currents0 = df[:, 2]

            self.labelNpts2.config(text=nptsorig)

        except:
            self.labelImport.config(text="Error importing file.")

    def import_par(self, filepath):
        try:
            with open(self.filepath) as fh:
                data = pd.read_csv(fh, header=3)
                fh.close()

            data = data.values
            self.distances0 = data[:, 1] * 1E3  # mm --> um
            self.distances0 = np.amax(self.distances0) - self.distances0
            self.currents0 = data[:, 2] * 1E3  # uA --> nA

            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")

            nptsorig = len(self.distances0)
            self.labelNpts2.config(text=nptsorig)

        except:
            self.labelImport.config(text="Error importing file.")

    def ReshapeData(self):
        self.distances = self.distances0.copy()
        self.currents = self.currents0.copy()

        ## Calculate zero tip substrate distance
        # Strip off any NaN points, make first point containing a current value the new zero
        critrow = np.amin(np.where(np.isnan(self.currents) == False))
        self.distances = self.distances[critrow:]
        self.currents = self.currents[critrow:]

        if self.zerodVar.get() != 'No calibration':
            self.distances = self.distances - np.amin(self.distances)  # correct to min
        else:
            pass

        if self.zerodVar.get() == 'First point with data':
            # Report how many points are left
            self.labelNpts4.config(text=len(self.distances))
        elif self.zerodVar.get() == "First derivative analysis":
            # Perform a derivative analysis, take location of peak to be zero
            currentsderiv = abs(np.gradient(self.currents))
            maxderiv = np.where(currentsderiv == np.amax(currentsderiv))
            maxderiv = int(maxderiv[0])

            # Strip off any points before the deriv peak (assume electrode bent)
            self.distances = self.distances[maxderiv:]
            self.currents = self.currents[maxderiv:]

            # Report how many points are left
            self.labelNpts4.config(text=len(self.distances))

        # Normalize distances
        try:
            if self.checkNormalize.var.get() == 1:
                self.distancesnorm = self.distances / (float(self.entryRadius.get()))
                self.labelRadiusErr.config(text="")
                self.labelRgErr.config(text="")
                self.labelConcErr.config(text="")
                self.labelDiffErr.config(text="")
            else:
                pass
        except:
            self.labelRadiusErr.config(text="Enter a value.")
            self.labelRgErr.config(text="Enter a value.")

        # Convert distances if necessary
        if self.distanceVar.get() == "µm":
            pass
        elif self.distanceVar.get() == "mm":
            self.distances = self.distances / 1E3
        elif self.distanceVar.get() == "nm":
            self.distances = self.distances * 1E3

        # Calculate theoretical steady state value
        try:
            if self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 0:
                beta = 1 + (0.23 / ((((float(self.entryRg.get())) ** 3) - 0.81) ** 0.36))
                self.issTheo = 4 * 1E9 * 96485 * beta * (float(self.entryDiff.get())) * (
                            (float(self.entryRadius.get())) / 1E6) * (float(self.entryConc.get()))
                self.labelTheoIssValue.config(text="{0:.3f}".format(self.issTheo))
            else:
                pass
        except:
            print("Error calculating theoretical steady state current.")

            # Normalize currents
        if self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 0:
            try:
                self.currentsnorm = self.currents / self.issTheo
                self.labelRadiusErr.config(text="")
                self.labelRgErr.config(text="")
                self.labelConcErr.config(text="")
                self.labelDiffErr.config(text="")
            except:
                self.labelRadiusErr.config(text="Enter a value.")
                self.labelRgErr.config(text="Enter a value.")
                self.labelConcErr.config(text="Enter a value.")
                self.labelDiffErr.config(text="Enter a value.")
        elif self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 1:
            try:
                self.currentsnorm = self.currents / (float(self.entryIssExp.get()))
            except:
                self.labelRadiusErr.config(text="Enter a value.")
        else:
            pass

        # Update current units if needed
        if self.currentVar.get() == "nA":
            pass
        elif self.currentVar.get() == "µA":
            self.currents = self.currents / 1E3
        elif self.currentVar.get() == "pA":
            self.currents = self.currents * 1E3

        # Update figure with PAC pre-treatment
        try:
            self.ax1.clear()
            self.img = self.ax1.plot(self.distances, self.currents)
            self.ax1.set_xlabel('Distance ({})'.format(self.distanceVar.get()))
            self.ax1.set_ylabel('Current ({})'.format(self.currentVar.get()))

            try:
                self.ax1.set_xlim([float(self.entryXmin.get()), float(self.entryXmax.get())])
            except:
                pass
            try:
                self.ax1.set_ylim([float(self.entryYmin.get()), float(self.entryYmax.get())])
            except:
                pass

        except:
            print("Data imported, call 1 to update canvas PAC failed.")

        # Fit Rg if requested
        if self.checkFitRg.var.get() == 1:
            critrow = np.amin(np.where(self.distancesnorm >= 0.1))
            self.distancesnorm = self.distancesnorm[critrow:]
            self.currentsnorm = self.currentsnorm[critrow:]

            try:
                # bounds prevent Rg<1 (insulating glass having smaller radius than the electrode it is meant to be
                # surrounding)
                self.estRg = scipy.optimize.curve_fit(self.negfbfit, self.distancesnorm,
                                                      self.currentsnorm, bounds=(1, np.inf))
                self.estRg = float(self.estRg[0])
                self.labelEstRg2.config(text="{0:.3f}".format(self.estRg))
            except:
                self.labelEstRg2.config(text="Err")

        # Fit kappa if requested
        if self.checkFitKappa.var.get() == 1:
            critrow = np.amin(np.where(self.distancesnorm >= 0.1))
            self.distancesnorm = self.distancesnorm[critrow:]
            self.currentsnorm = self.currentsnorm[critrow:]

            try:
                self.estKappa = scipy.optimize.curve_fit(self.kappafit, self.distancesnorm, self.currentsnorm, bounds=(0, np.inf))  # bounds prevent negative kappa
                self.estKappa = float(self.estKappa[0])
                self.labelEstKappa2.config(text="{0:.3E}".format(self.estKappa))
            except:
                self.labelEstKappa2.config(text="Err")

            try:
                self.estK = (1E8 * self.estKappa * float(self.entryDiff.get())) / (float(self.entryRadius.get()))
                self.labelEstK2.config(text="{0:.3E}".format(self.estK))
            except:
                self.labelDiffErr.config(text="Enter a value.")
                self.labelEstK2.config(text="Err.")

        # Calculate pure feedback normalized currents for comparison
        if self.checkNormalize.var.get() == 1:
            try:
                # Note: The value of Rg used in these equations depends on the state of the 'fit Rg?' checkbox
                self.theonegfb = self.negfb()
                self.theoposfb = self.posfb()
            except:
                print("Error calculating pure feedback currents.")
        else:
            pass

        # Calculate theoretical kappa curve for comparison
        if self.checkFitKappa.var.get() == 1:
            try:
                self.theokappatheo = self.kappa()
            except:
                print("Error calculating theoretical mixed kinetics curve.")

        # Update figure with PAC post-treatment
        try:
            if self.checkNormalize.var.get() == 1:
                self.ax2.clear()

                # Check if the feedback cases should be plotted as well
                if self.checkFeedback.var.get() == 1:
                    self.ax2.plot(self.distancesnorm, self.currentsnorm, label='Experimental')
                    self.ax2.plot(self.distancesnorm, self.theonegfb, color='red', label='Negative feedback')
                    self.ax2.plot(self.distancesnorm, self.theoposfb, color='green', label='Positive feedback')
                    self.ax2.legend()
                    self.ax2.set_xlabel('Normalized distance')
                    self.ax2.set_ylabel('Normalized current')
                    self.ax2.set_ylim([0, 3])
                else:
                    self.ax2.plot(self.distancesnorm, self.currentsnorm)
                    self.ax2.set_xlabel('Normalized distance')
                    self.ax2.set_ylabel('Normalized current')

                # Check if the fit line should be plotted as well
                if self.checkFitKappa.var.get() == 1:
                    self.ax2.plot(self.distancesnorm, self.theokappatheo, label='Fit curve')
                    self.ax2.legend()
                    self.ax2.set_xlabel('Normalized distance')
                    self.ax2.set_ylabel('Normalized current')
                    self.ax2.set_ylim([0, 3])

                # Set X/Y limits on normalized axes, update labels
                try:
                    xmin_norm = float(self.entryXmin.get()) / float(self.entryRadius.get())
                    xmax_norm = float(self.entryXmax.get()) / float(self.entryRadius.get())
                    self.ax2.set_xlim([xmin_norm, xmax_norm])
                    self.labelXmin3.config(text="{0:.2f}".format(xmin_norm))
                    self.labelXmax3.config(text="{0:.2f}".format(xmax_norm))
                except:
                    pass
                try:
                    ymin_norm = float(self.entryYmin.get()) / float(self.entryRadius.get())
                    ymax_norm = float(self.entryYmin.get()) / float(self.entryRadius.get())
                    self.labelYmin3.config(text="{0:.2f}".format(ymin_norm))
                    self.labelYmax3.config(text="{0:.2f}".format(ymax_norm))
                    self.ax2.set_ylim([ymin_norm, ymax_norm])
                except:
                    pass
            else:
                pass
        except:
            print("Data imported, call 2 to update canvas PAC failed.")

        self.canvas.draw()
        self.buttonSave.config(state="normal")
        self.buttonExport.config(state="normal")
        # save checkbox states
        self.statNorm = self.statusNormalize.get()
        self.statNormXP = self.statusNormalizeExp.get()
        self.statFK = self.statusFitKappa.get()
        self.statFB = self.statusFeedback.get()
        self.statFRg = self.statusFitRg.get()

    def negfbfit(self, distancesnorm, Rg):
        Lvalues = self.distancesnorm

        # Build up the analytical approximation
        currentsins_pt1 = ((2.08 / (Rg ** 0.358)) * (Lvalues - (0.145 / Rg))) + 1.585
        currentsins_pt2 = (2.08 / (Rg ** 0.358) * (Lvalues + (0.0023 * Rg))) + 1.57
        currentsins_pt3 = (np.log(Rg) / Lvalues) + (2 / (np.pi * Rg) * (np.log(1 + (np.pi * Rg) / (2 * Lvalues))))
        currentsins = currentsins_pt1 / (currentsins_pt2 + currentsins_pt3)

        return currentsins

    def kappafit(self, distancesnorm, kappa):
        Lvalues = self.distancesnorm
        Rg = float(self.entryRg.get())

        # negfb
        currentsins_pt1 = ((2.08 / (Rg ** 0.358)) * (Lvalues - (0.145 / Rg))) + 1.585
        currentsins_pt2 = (2.08 / (Rg ** 0.358) * (Lvalues + (0.0023 * Rg))) + 1.57
        currentsins_pt3 = (np.log(Rg) / Lvalues) + (2 / (np.pi * Rg) * (np.log(1 + (np.pi * Rg) / (2 * Lvalues))))
        currentsins = currentsins_pt1 / (currentsins_pt2 + currentsins_pt3)

        # positive fb
        alpha = np.log(2) + np.log(2) * (1 - (2 / np.pi) * np.arccos(1 / Rg)) - np.log(2) * (1 - ((2 / np.pi) * np.arccos(1 / Rg)) ** 2)
        beta = 1 + 0.639 * (1 - (2 / np.pi) * np.arccos(1 / Rg)) - 0.186 * (1 - ((2 / np.pi) * np.arccos(1 / Rg)) ** 2)
        currentsmixed_pt0 = alpha + (1 / beta) * (np.pi / (4 * np.arctan(Lvalues + (1 / kappa)))) + (1 - alpha - (0.5 / beta)) * (2 / np.pi) * np.arctan(Lvalues + (1 / kappa))

        # Merge neg/posfb expressions into analytical approx.
        currentsmixed_pt1 = currentsins - 1
        currentsmixed_pt2 = 1 + (2.47 * Lvalues * kappa) * (Rg ** 0.31)
        currentsmixed_pt3 = 1 + (Lvalues ** ((0.006 * Rg + 0.113))) * (kappa ** ((-0.0236 * Rg + 0.91)))

        currentsmixed = currentsmixed_pt0 + ((currentsmixed_pt1) / (currentsmixed_pt2 * currentsmixed_pt3))

        return currentsmixed

    def negfb(self):
        if self.checkFitRg.var.get() == 1:
            Rg = self.estRg
        else:
            Rg = float(self.entryRg.get())

        Lvalues = self.distancesnorm

        # Build up the analytical approximation
        currentsins_pt1 = ((2.08 / (Rg ** 0.358)) * (Lvalues - (0.145 / Rg))) + 1.585
        currentsins_pt2 = (2.08 / (Rg ** 0.358) * (Lvalues + (0.0023 * Rg))) + 1.57
        currentsins_pt3 = (np.log(Rg) / Lvalues) + (2 / (np.pi * Rg) * (np.log(1 + (np.pi * Rg) / (2 * Lvalues))))
        currentsins = currentsins_pt1 / (currentsins_pt2 + currentsins_pt3)

        return currentsins

    def kappa(self):
        Lvalues = self.distancesnorm
        Rg = float(self.entryRg.get())
        kappa = self.estKappa

        # negfb
        currentsins_pt1 = ((2.08 / (Rg ** 0.358)) * (Lvalues - (0.145 / Rg))) + 1.585
        currentsins_pt2 = (2.08 / (Rg ** 0.358) * (Lvalues + (0.0023 * Rg))) + 1.57
        currentsins_pt3 = (np.log(Rg) / Lvalues) + (2 / (np.pi * Rg) * (np.log(1 + (np.pi * Rg) / (2 * Lvalues))))
        currentsins = currentsins_pt1 / (currentsins_pt2 + currentsins_pt3)

        # positive fb
        alpha = np.log(2) + np.log(2) * (1 - (2 / np.pi) * np.arccos(1 / Rg)) - np.log(2) * (1 - ((2 / np.pi) * np.arccos(1 / Rg)) ** 2)
        beta = 1 + 0.639 * (1 - (2 / np.pi) * np.arccos(1 / Rg)) - 0.186 * (1 - ((2 / np.pi) * np.arccos(1 / Rg)) ** 2)
        currentsmixed_pt0 = alpha + (1 / beta) * (np.pi / (4 * np.arctan(Lvalues + (1 / kappa)))) + (1 - alpha - (0.5 / beta)) * (2 / np.pi) * np.arctan(Lvalues + (1 / kappa))

        # Merge neg/posfb expressions into analytical approx.
        currentsmixed_pt1 = currentsins - 1
        currentsmixed_pt2 = 1 + (2.47 * Lvalues * kappa) * (Rg ** 0.31)
        currentsmixed_pt3 = 1 + (Lvalues ** ((0.006 * Rg + 0.113))) * (kappa ** ((-0.0236 * Rg + 0.91)))

        currentsmixed = currentsmixed_pt0 + ((currentsmixed_pt1) / (currentsmixed_pt2 * currentsmixed_pt3))

        return currentsmixed

    def posfb(self):
        if self.checkFitRg.var.get() == 1:
            Rg = self.estRg
        else:
            Rg = float(self.entryRg.get())

        Lvalues = self.distancesnorm

        # Build up the analytical approximation
        alpha = np.log(2) + np.log(2) * (1 - (2 / np.pi) * np.arccos(1 / Rg)) - np.log(2) * (1 - ((2 / np.pi) * np.arccos(1 / Rg)) ** 2)
        beta = 1 + 0.639 * (1 - (2 / np.pi) * np.arccos(1 / Rg)) - 0.186 * (1 - ((2 / np.pi) * np.arccos(1 / Rg)) ** 2)
        currentscond = alpha + (1 / beta) * (np.pi / (4 * np.arctan(Lvalues))) + (1 - alpha - (0.5 / beta)) * (2 / np.pi) * np.arctan(Lvalues)

        return currentscond

    def BoxesSelected(self):
        # Enable/disable entry fields for calculating theoretical iss
        if self.checkNormalize.var.get() == 1:
            self.entryConc.config(state="normal")
            self.entryDiff.config(state="normal")
            self.checkNormalizeExp.config(state="normal")
        else:
            pass

        if self.checkNormalizeExp.var.get() == 1:
            self.entryIssExp.config(state="normal")
        else:
            pass

        if self.checkFitRg.var.get() == 1:
            self.entryRg.config(state="disabled")
            self.entryConc.config(state="disabled")
            self.entryDiff.config(state="disabled")
            self.entryIssExp.config(state="normal")

        else:
            self.entryRg.config(state="normal")
            self.entryConc.config(state="normal")
            self.entryDiff.config(state="normal")

    def save_figure(self):
        """Saves the figure that is currently being displayed by the app"""
        try:
            filepath = asksaveasfilename(initialdir=self.last_dir + "/", title="Select file",
                                         filetypes=(("png", "*.png"), ("all files", "*.*")))
            filename_start = filepath.rindex('/')
            self.last_dir = filepath[:filename_start]

            # Save full image
            if self.figsaveVar.get() == "Both":
                self.fig.savefig(fname=filepath, dpi=400)
                self.labelPlot.config(text="Figure saved.")

            # Save left image only
            elif self.figsaveVar.get() == "Non-normalized PAC":
                # Determine dimensions of first subplot
                extent = self.ax1.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())

                # Save the figure, expand the extent by 50% in x and 20% in y to include axis labels and colorbar
                self.fig.savefig(fname=filepath, dpi=400)
                self.labelPlot.config(text="Figure saved.")

            # Save right image only
            else:
                # Determine dimensions of second subplot
                extent = self.ax2.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())

                # Save the figure, expand the extent by 50% in x and 20% in y to include axis labels and colorbar
                self.fig.savefig(fname=filepath, dpi=400)
                self.labelPlot.config(text="Figure saved.")

        except:
            self.labelPlot.config(text="Error saving figure to file.")

    def export_data_action(self):
        """Exports the data in an ASCII file that can be read by most 3rd-party plotting software.
        The data is formatted as follows (i.a. = if applicable):
        #Headings
        #
        #Distance, current, normalized distance i.a., normalized current i.a., theoretical curve i.a., positive feedback curve i.a., negative feedback curve i.a.
        d,I,Nd,NI,TF,+FB,-FB
        ...
        """
        export = ""
        try:
            # Prompt user to select a file name, open a text file with that name
            export = asksaveasfilename(initialdir=self.last_dir + "/",
                                       filetypes=[("Text file", "*.txt")],
                                       title="Choose a file.")
            filename_start = export.rindex('/')
            self.last_dir = export[:filename_start]
            if not export[-4] == '.':
                export = export + ".txt"
        except:
            pass
        if not export == "":
            try:
                with open(export, "w+") as fh:
                    # Header lines: print details about the file and data treatment
                    fh.write("#FLUX: APPROACH CURVE\n")
                    fh.write("#Original file: {} \n".format(self.filename))
                    fh.write("#Units of current: {} \n".format(self.currentVar.get()))
                    fh.write("#Units of distance: {} \n".format(self.distanceVar.get()))

                    # Report theoretical and experimental steady state currents
                    if self.statNorm == 1:
                        if self.statNormXP == 1:
                            expiss = float(self.entryIssExp.get())
                            fh.write("#Experimental steady state current (nA): {0:.3f} \n".format(expiss))
                        else:
                            theoiss = self.issTheo
                            fh.write("#Theoretical steady state current (nA): {0:.3f} \n".format(theoiss))

                            expiss = 'Not calculated'
                            fh.write("#Experimental steady state current (nA): {} \n".format(expiss))
                    else:
                        theoiss = 'Not calculated'
                        fh.write("#Theoretical steady state current (nA): {} \n".format(theoiss))

                    # Report Rg
                    if self.statFRg == 1:
                        fh.write("#Rg (fit): {0:.1f} \n".format(self.estRg))
                    else:
                        try:
                            inputRg = float(self.entryRg.get())
                            fh.write("#Rg (input): {0:.3f} \n".format(inputRg))
                        except:
                            fh.write("#Rg: Not available \n")

                    # Report kappa
                    if self.statFK == 1:
                        fh.write("#kappa (fit): {0:.3E} \n".format(self.estKappa))
                        try:
                            fh.write("#k (cm/s): {0:.3E} \n".format(self.estK))
                        except:
                            pass
                    else:
                        fh.write("#kappa (fit): Not calculated \n")
                        fh.write("#k (cm/s): Not calculated \n")

                        # Insert blank line between header and data
                    fh.write("# \n")
                    fh.write("#Distance, Current")
                    if self.statNorm == 1:
                        fh.write(", Normalized distance, Normalized current")
                    if self.statFK == 1:
                        fh.write(", Theoretical fit")
                    if self.statFB == 1:
                        fh.write(", Positive feedback, Negative feedback")

                    for d in range(len(self.distances)):
                        fh.write("\n{0:1.4E},{1:1.4E}".format(self.distances[d], self.currents[d]))
                        if self.statNorm == 1:
                            fh.write(",{0:1.4E},{1:1.4E}".format(self.distancesnorm[d], self.currentsnorm[d]))
                        if self.statFK == 1:
                            fh.write(",{0:1.4E}".format(self.theokappatheo[d]))
                        if self.statFB == 1:
                            fh.write(",{0:1.4E},{1:1.4E}".format(self.theoposfb[d], self.theonegfb[d]))

                    # Print 1D array of distance
                    # fh.write("Tip-substrate distance: \n")
                    # np.savetxt(fh, self.distances, delimiter=',', fmt='%1.4e')
                    # fh.write(" \n")

                    # Print 1D array of current
                    # fh.write("Current: \n")
                    # np.savetxt(fh, self.currents, delimiter=',', fmt='%1.4e')
                    # fh.write(" \n")

                    # Print normalized quantities, if applicable
                    # if self.statusNormalize.get() == 1:

                        # Normalized distance
                        # fh.write("Normalized tip-substrate distance: \n")
                        # np.savetxt(fh, self.distancesnorm, delimiter=',', fmt='%1.4e')
                        # fh.write(" \n")

                        # Normalized current
                        # fh.write("Normalized current: \n")
                        # np.savetxt(fh, self.currentsnorm, delimiter=',', fmt='%1.4e')
                        # fh.write(" \n")

                        # else:
                        # fh.write(" \n")

                    # Print mixed feedback line for est kappa, if applicable
                    # if self.statusFitKappa.get() == 1:
                        # fh.write("Theoretical line for estimated kappa: \n")
                        # np.savetxt(fh, self.theokappatheo, delimiter=',', fmt='%1.4e')
                        # fh.write(" \n")
                        # else:
                        # fh.write(" \n")

                    # Print pure feedback lines, if applicable
                    # if self.statusFeedback.get() == 1:

                        # Positive feedback
                        # fh.write("Theoretical positive feedback: \n")
                        # np.savetxt(fh, self.theoposfb, delimiter=',', fmt='%1.4e')
                        # fh.write(" \n")

                        # Negative feedback
                        # fh.write("Theoretical negative feedback: \n")
                        # np.savetxt(fh, self.theonegfb, delimiter=',', fmt='%1.4e')
                        # fh.write(" \n")
                        # else:
                        # fh.write(" \n")

                    fh.close()
                    self.labelPlot.config(text="Data exported.")
            except:
                self.labelPlot.config(text="Error whilst exporting data")

    def ResetWindow(self):
        print("Reset requested.")

        # Reset graph
        self.ax1.clear()
        self.ax1.set_xlabel('Distance (µm)')
        self.ax1.set_ylabel('Current (nA)')
        self.ax2.clear()
        self.ax2.set_xlabel('Normalized distance')
        self.ax2.set_ylabel('Normalized current')
        self.canvas.draw()

        # Checkboxes
        self.checkNormalize.var.set(0)
        self.checkNormalizeExp.var.set(0)
        self.checkFeedback.var.set(0)
        self.checkFitRg.var.set(0)
        self.checkFitKappa.var.set(0)

        # Buttons
        self.buttonImport.config(state="disabled")
        self.buttonPlot.config(state="disabled")
        self.buttonSave.config(state="disabled")
        self.buttonExport.config(state="disabled")

        # Labels
        self.labelFile.config(text="")
        self.labelImport.config(text="Select file to continue.")
        self.labelNpts2.config(text="")
        self.labelNpts4.config(text="")
        self.labelPlot.config(text="Import data to begin.")
        self.labelTheoIssValue.config(text="")
        self.labelRadiusErr.config(text="")
        self.labelRgErr.config(text="")
        self.labelConcErr.config(text="")
        self.labelDiffErr.config(text="")
        self.labelEstRg2.config(text="")
        self.labelEstK2.config(text="")
        self.labelEstKappa2.config(text="")
        self.labelXmin3.config(text="")
        self.labelXmax3.config(text="")
        self.labelYmin3.config(text="")
        self.labelYmax3.config(text="")
        self.labelXCursor.config(text="X : ")
        self.labelYCursor.config(text="Y : ")

        # Entries
        self.entryIssExp.delete(0, "end")
        self.entryIssExp.config(state="disabled")
        self.entryRadius.delete(0, "end")
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
