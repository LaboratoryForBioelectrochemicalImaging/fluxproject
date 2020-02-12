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


class CVApp:
    """Handles data from cyclic voltammetry experiments.
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
            frameBase.columnconfigure(i, minsize=150)
            framePlot.columnconfigure(i, minsize=140)
            frameFormatting.columnconfigure(i, minsize=140)

        ###### Base frame #####
        # Intro
        labelIntro = tk.Label(frameBase, text="Import experimental data to be plotted.")
        labelIntro.grid(row=0, column=0, columnspan=6, padx=20, pady=10, sticky="WS")

        # Select file
        self.buttonFile = tk.Button(frameBase, text="Select File", command=self.SelectFile)
        self.buttonFile.grid(row=1, column=1, sticky="W" + "E", padx=10)
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
        textChoices = {'Biologic', 'CH Instruments', 'HEKA', 'Sensolytics'}
        popupText = tk.OptionMenu(frameBase, self.textVar, *textChoices)
        popupText.configure(width=15)
        popupText.grid(row=3, column=2, sticky="W")
        #        # link function to change dropdown
        self.textVar.trace('w', self.change_dropdown)

        # Label for number of cycles
        labelCycles = tk.Label(frameBase, text="# cycles:")
        labelCycles.grid(row=1, column=3, padx=10, sticky="E")
        self.labelCycles2 = tk.Label(frameBase, text="")
        self.labelCycles2.grid(row=1, column=4, padx=10, sticky="W")

        # Label for number of point in each cycle
        labelNpts = tk.Label(frameBase, text="Pts/cycle:")
        labelNpts.grid(row=2, column=3, padx=10, sticky="E")
        self.labelNpts2 = tk.Label(frameBase, text="")
        self.labelNpts2.grid(row=2, column=4, padx=10, sticky="W")

        # Label for scan rate
        labelNu = tk.Label(frameBase, text="Scan rate (mV/s):")
        labelNu.grid(row=3, column=3, padx=10, pady=5, sticky="E")
        self.labelNu2 = tk.Label(frameBase, text="")
        self.labelNu2.grid(row=3, column=4, padx=10, sticky="W")

        # Dropdown menu for multicycle support
        # Create a stringvar which will contian the eventual choice
        self.multicycleVar = tk.StringVar(master)
        self.multicycleVar.set('Plot first cycle')  # set the default option
        # Dictionary with options
        choices = {'Plot first cycle', 'Plot second cycle to end', 'Plot all cycles', 'Plot specific cycle'}
        popupMulticycle = tk.OptionMenu(frameBase, self.multicycleVar, *choices)
        popupMulticycle.configure(width=20)
        popupMulticycle.grid(row=1, column=5, sticky="W", padx=10)
        #        # link function to change dropdown
        self.multicycleVar.trace('w', self.change_dropdown)

        # Entry field for getting specific cycle number to plot
        labelSpCycle = tk.Label(frameBase, text="Specific cycle: ")
        labelSpCycle.grid(row=2, column=5, sticky="W", padx=10)
        self.entrySpCycle = tk.Entry(frameBase, state='disabled')
        self.entrySpCycle.grid(row=3, column=5, sticky="W", padx=10)

        # Input for accepting reference electrode
        labelRefElec = tk.Label(frameBase, text="Reference electrode")
        labelRefElec.grid(row=1, column=6, padx=50, sticky="W")
        self.entryRefElec = tk.Entry(frameBase)
        self.entryRefElec.grid(row=2, column=6, padx=50, sticky="W")

        # Label for returning error if only one cycle
        self.labelError = tk.Label(frameBase, text="")
        self.labelError.grid(row=0, column=5, sticky="W", padx=10)

        ###### Analytics frame #####
        # Intro
        labelAnalytics = tk.Label(frameAnalytics, text="Customize the data treatment.")
        labelAnalytics.grid(row=0, column=0, padx=20, pady=10, sticky="WS")

        # Toggle for calculating theoretical steady state current
        self.statusNormalize = tk.IntVar()
        self.checkNormalize = tk.Checkbutton(frameAnalytics, text="Plot theoretical iss?",
                                             variable=self.statusNormalize, command=self.BoxesSelected)
        self.checkNormalize.var = self.statusNormalize
        self.checkNormalize.grid(row=1, column=0, sticky="E", padx=10)

        # Toggle for calculating experimental steady state current
        self.statusNormalizeExp = tk.IntVar()
        self.checkNormalizeExp = tk.Checkbutton(frameAnalytics, text="Calculate experimental iss?",
                                                variable=self.statusNormalizeExp)
        self.checkNormalizeExp.var = self.statusNormalizeExp
        self.checkNormalizeExp.grid(row=2, column=0, sticky="E", padx=10)

        # Toggle for calculating standard potential
        self.statusStdPot = tk.IntVar()
        self.checkStdPot = tk.Checkbutton(frameAnalytics, text="Calculate formal potential?",
                                          variable=self.statusStdPot, command=self.BoxesSelected)
        self.checkStdPot.var = self.statusStdPot
        self.checkStdPot.grid(row=3, column=0, rowspan=2, sticky="E", padx=10, pady=10)

        # Label for reporting calculated standard potential
        labelStdPot = tk.Label(frameAnalytics, text="Formal potential (V vs. ref)")
        labelStdPot.grid(row=3, column=1, padx=10)
        self.StdPot2 = tk.Label(frameAnalytics, text="")
        self.StdPot2.grid(row=4, column=1, padx=10, sticky="W")

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

        # Label for reporting calculated experimental steady state current
        labelExpIss = tk.Label(frameAnalytics, text="Experimental iss (nA)")
        labelExpIss.grid(row=1, column=6, padx=10)
        self.ExpIss2 = tk.Label(frameAnalytics, text="")
        self.ExpIss2.grid(row=2, column=6, padx=10, sticky="W")

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
        self.buttonReset.grid(row=0, column=5, padx=20, pady=10, sticky="W" + "E")

        ######## Formatting menu ########
        # Intro
        labelFormatting = tk.Label(frameFormatting, text="Customize the formatting of the graph.")
        labelFormatting.grid(row=0, column=0, padx=20, pady=5, columnspan=3, sticky="W")

        # Dropdown menu for units on distance
        # Label for dropdown menu
        labelPotential = tk.Label(frameFormatting, text="Units (Potential)")
        labelPotential.grid(row=1, column=1, sticky="W", padx=10)
        # Create a stringvar which will contian the eventual choice
        self.potentialVar = tk.StringVar(master)
        self.potentialVar.set('V')  # set the default option
        # Dictionary with options
        potentialChoices = {'V', 'mV'}
        popupPotential = tk.OptionMenu(frameFormatting, self.potentialVar, *potentialChoices)
        popupPotential.configure(width=10)
        popupPotential.grid(row=2, column=1, sticky="W", padx=10)
        #        # link function to change dropdown
        self.potentialVar.trace('w', self.change_dropdown)

        # Dropdown menu for units on current
        # Label for dropdown menu
        labelCurrent = tk.Label(frameFormatting, text="Units (Current)")
        labelCurrent.grid(row=1, column=2, sticky="W", padx=10)
        # Create a stringvar which will contian the eventual choice
        self.currentVar = tk.StringVar(master)
        self.currentVar.set('nA')  # set the default option
        # Dictionary with options
        currentChoices = {'µA', 'nA', 'pA'}
        popupCurrent = tk.OptionMenu(frameFormatting, self.currentVar, *currentChoices)
        popupCurrent.configure(width=10)
        popupCurrent.grid(row=2, column=2, sticky="W", padx=10)
        #        # link function to change dropdown
        self.currentVar.trace('w', self.change_dropdown)

        # Entry fields for controlling axis limits on plot
        labelXmin = tk.Label(frameFormatting, text="Xmin")
        labelXmin.grid(row=1, column=3, sticky="W", padx=10)
        self.entryXmin = tk.Entry(frameFormatting)
        self.entryXmin.grid(row=2, column=3, sticky="W", padx=10)

        labelXmax = tk.Label(frameFormatting, text="Xmax")
        labelXmax.grid(row=3, column=3, sticky="W", padx=10)
        self.entryXmax = tk.Entry(frameFormatting)
        self.entryXmax.grid(row=4, column=3, sticky="W", padx=10)

        labelYmin = tk.Label(frameFormatting, text="Ymin")
        labelYmin.grid(row=1, column=4, sticky="W", padx=10)
        self.entryYmin = tk.Entry(frameFormatting)
        self.entryYmin.grid(row=2, column=4, sticky="W", padx=10)

        labelYmax = tk.Label(frameFormatting, text="Ymax")
        labelYmax.grid(row=3, column=4, sticky="W", padx=10)
        self.entryYmax = tk.Entry(frameFormatting)
        self.entryYmax.grid(row=4, column=4, sticky="W", padx=10)

        # Data cursor setup
        labelCursor = tk.Label(frameFormatting, text="Data Cursor")
        labelCursor.grid(row=1, column=5, sticky="W", padx=10)
        self.labelXCursor = tk.Label(frameFormatting, text="X : ")
        self.labelXCursor.grid(row=2, column=5, sticky="W", padx=10)
        self.labelYCursor = tk.Label(frameFormatting, text="Y : ")
        self.labelYCursor.grid(row=3, column=5, sticky="W", padx=10)

        ######### Bottom frame: Figure ###########

        # Set up data cursor function
        def DataCursor(event):
            try:
                xcursor = event.xdata
                ycursor = event.ydata
                self.labelXCursor.config(text="X : {0:.3f}".format(xcursor))
                self.labelYCursor.config(text="Y : {0:.3f}".format(ycursor))
            except:
                pass

        # Start creating the plot
        self.fig = Figure(figsize=(5, 4), dpi=120)

        # Plot CV using dummy values
        self.ax1 = self.fig.add_subplot(111)
        #        self.img = self.ax1.plot(self.potential,self.currents)
        self.ax1.set_xlabel('Potential vs. Ag/AgCl ({})'.format(self.potentialVar.get()))
        self.ax1.set_ylabel('Current (nA)')

        self.fig.subplots_adjust(top=0.95, bottom=0.15, left=0.2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frameBottom)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="S")
        self.canvas.mpl_connect('button_press_event', DataCursor)
        self.canvas.draw()

    def change_dropdown(self, *args):
        if self.multicycleVar.get() == 'Plot specific cycle':
            self.entrySpCycle.config(state="normal")
        else:
            self.entrySpCycle.config(state="disabled")

    def SelectFile(self):
        self.filepath = askopenfilename(initialdir="/", title="Choose a file.")
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
        else:
            pass

    def ImportFile(self):
        ## Check if manufacturer needed
        if self.filename[-3:] == 'txt' and self.textVar.get() == 'None':
            self.labelImport.config(text="Specify a manufacturer.")

        ### ASC / Heka import ###
        elif self.filename[-3:] == 'asc':
            self.import_heka_asc(self.filepath)
        ### MAT / HEKA import ####
        elif self.filename[-3:] == 'mat':
            self.import_heka_mat(self.filepath)
        ### TXT / Biologic import ###
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'Biologic':
            self.import_biologic(self.filepath)
        ### TXT/CH instruments import ####
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'CH Instruments':
            self.import_ch_instruments(self.filepath)
        ### DAT / Sensolytics import ###
        elif self.filename[-3:] == 'dat':
            self.import_sensolytics(self.filepath)
        else:
            self.labelImport.config(text="File type not supported.")

    """
    Looking to extend the import file functionality to support a different file type?
    The ReshapeData function assumes the following is present after the ImportFile function has run:
        > self.potential = 1D numpy array containing potential values in volts for one sweep
        > self.currents_reshape = 2D numpy array containing current values in amps; each row is one cycle
        > self.ncycles = Integer corresponding to the number of cycles

    """

    def import_heka_asc(self, filepath):
        # Import data file
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
                fh.close()

        except:
            self.labelImport.config(text="Error importing file.")

        # Convert raw data to matrix
        try:
            df = pd.DataFrame(data, columns=["PtIndex", "Time (s)", "Current (A)", "Time (s)", "Potential (V)"], dtype='float')
            df = df.values

            df[:, 2] = df[:, 2] * 1E9  # A --> nA

            # Determine number of cycles
            self.ncycles = df[df[:, 1] == 0]
            self.ncycles = len(self.ncycles)
            nptscycle = int(len(df) / self.ncycles)

            self.potential0 = df[0:nptscycle, 4]
            self.currents0 = df[:, 2]
            self.currents_reshape0 = self.currents0.reshape(self.ncycles, nptscycle)

            # Calculate scan rate in mV/s
            critpt = int(np.floor(nptscycle / 4))
            print(critpt)
            scanrate = 1000 * ((df[critpt, 4] - df[0, 4]) / (df[critpt, 1] - df[0, 1]))
            self.labelNu2.config(text="{0:.0f}".format(scanrate))

            self.labelCycles2.config(text=self.ncycles)
            self.labelNpts2.config(text=nptscycle)

            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")

        except:
            self.labelImport.config(text="Could not import file.")

    def import_heka_mat(self, filepath):
        try:
            matdata = scipy.io.loadmat(filepath)
            # Delete non-data containing variables
            del matdata['__header__']
            del matdata['__globals__']
            del matdata['__version__']

            # Each cycle creates two traces: one for current, one for potential
            self.ncycles = int(np.divide(len(matdata), 2))

            data = []
            # Read once to determine dimensions
            for entry in matdata:
                trace = matdata[entry]
                self.potential0 = trace[:, 1]
                self.nptscycle = len(self.potential0)

            # Read a second time to construct the appropriate table
            data = np.empty((self.ncycles, self.nptscycle), dtype=float)
            count = 0
            for entry in matdata:
                try:
                    # Trace A_B_C_1 = Current
                    if np.remainder(count, 2) == 0:
                        trace2 = matdata[entry]
                        data[count, :] = trace2[:, 1]
                    # Trace A_B_C_2 = Potential
                    else:
                        pass
                except:
                    pass
                count = count + 1
            self.currents_reshape0 = data * 1E9

            self.labelImport.config(text="File imported.")

        except:
            self.labelImport.config(text="Could not import file.")

        try:
            # Calculate scan rate in mV/s
            critpt = int(np.floor(self.nptscycle / 4))
            scanrate = 1000 * ((trace[critpt, 1] - trace[0, 1]) / (trace[critpt, 0] - trace[0, 0]))
            self.labelNu2.config(text="{0:.0f}".format(scanrate))

            self.labelCycles2.config(text=self.ncycles)
            self.labelNpts2.config(text=self.nptscycle)

            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")
        except:
            self.labelImport.config(text="Error processing file.")

    def import_biologic(self, filepath):
        # Import file
        data = []
        try:
            with open(filepath, 'r') as fh:
                for curline in fh:
                    try:
                        curline = curline.split()
                        float(curline[0])
                        data.append(curline)
                    except:
                        pass
                fh.close()
        except:
            self.labelImport.config(text="Could not import file.")

        # Process file into consistent format for ReshapeData
        df = pd.DataFrame(data, columns=["Potential (V)", "Current (A"], dtype=float)
        df = df.values

        df[:, 1] = df[:, 1] * 1E9  # A --> nA

        # Determine number of cycles based on number of max peak potential is reached
        self.ncycles = df[df[:, 0] == np.amax(df[:, 0])]
        self.ncycles = len(self.ncycles)
        self.nptscycle = int(len(df) / self.ncycles)

        self.potential0 = df[0:self.nptscycle, 0]
        self.currents0 = df[:, 1]
        self.labelNu2.config(text="Not available.")

        # Reshape into matrix where rows = cycles
        # If there is an extra point at the end (start/end on same potential), omit this point
        try:
            self.currents_reshape0 = self.currents0.reshape(self.ncycles, self.nptscycle)
        except:
            extrapoint = np.remainder(len(df), self.nptscycle)
            if extrapoint == 1:
                self.currents_reshape0 = self.currents0[:-1].reshape(self.ncycles, self.nptscycle)
            else:
                self.labelImport.config(text="Error processing cycles.")

        self.labelCycles2.config(text=self.ncycles)
        self.labelNpts2.config(text=self.nptscycle)

        self.labelImport.config(text="File imported.")
        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")

    def import_ch_instruments(self, filepath):
        try:
            data = []
            datastart = 0  # toggle for determining if reading point cloud
            index = 0

            # First read to extract data
            with open(filepath, 'r') as fh:
                for curline in fh:
                    try:
                        curline = curline.split(',')
                        if curline == ['Potential/V', ' Current/A\n']:
                            datastart = 1
                        if datastart == 1:
                            float(curline[0])  # check if line contains strings or numbers
                            data.append(curline)  # if number, add to dataframe
                    except:
                        pass  # if string, skip to next line
                fh.close()

            # Second read to extract scan rate
            with open(self.filepath, 'r') as fh2:
                for curline2 in fh2:
                    index = index + 1
                    if index == 13:  # The scan rate info can be found in this line
                        nu = curline2.split('=')
                        nu = 1000 * (float(nu[1].strip('\n')))
                    else:
                        pass

            df = pd.DataFrame(data, dtype='float')
            df = df.values

            df[:, 1] = df[:, 1] * 1E9  # A --> nA

            # Determine number of cycles based on number of max peak potential is reached
            self.ncycles = df[df[:, 0] == np.amax(df[:, 0])]
            self.ncycles = len(self.ncycles)
            self.nptscycle = int(len(df) / self.ncycles)

            self.potential0 = df[0:self.nptscycle, 0]
            self.currents0 = df[:, 1]
            self.currents0 = self.currents0 * (-1)  # polarographic --> IUPAC convention
            self.labelNu2.config(text="{0:.0f}".format(nu))

            # Reshape into matrix where rows = cycles
            # If there is an extra point at the end (start/end on same potential), omit this point
            try:
                self.currents_reshape0 = self.currents0.reshape(self.ncycles, self.nptscycle)
            except:
                extrapoint = np.remainder(len(df), self.nptscycle)
                if extrapoint == 1:
                    self.currents_reshape0 = self.currents0[:-1].reshape(self.ncycles, self.nptscycle)
                else:
                    self.labelImport.config(text="Error processing cycles.")

            self.labelCycles2.config(text=self.ncycles)
            self.labelNpts2.config(text=self.nptscycle)

            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")

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
                    if index <= 20:
                        try:
                            curline = curline.split('\t')
                            header.append(curline)
                        except:
                            pass
                    if index > 20:
                        try:
                            curline = curline.split(',')
                            float(curline[0])
                            data.append(curline)
                        except:
                            pass
                fh.close()

            scanrate = 1000 * (float(header[18][1].strip(' \n')))

            df = pd.DataFrame(data, columns=['Potential (V)', 'Current (A)', 'NA'], dtype=float)
            del df['NA']
            df = df.values
            df[:, 1] = df[:, 1] * 1E9  # A --> nA

            self.ncycles = df[df[:, 0] == np.amax(df[:, 0])]
            self.ncycles = len(self.ncycles)
            nptscycle = int(len(df) / self.ncycles)

            self.potential0 = df[0:nptscycle, 0]
            self.currents0 = df[:, 1]
            self.currents_reshape0 = self.currents0.reshape(self.ncycles, nptscycle)

            self.labelCycles2.config(text=self.ncycles)
            self.labelNpts2.config(text=nptscycle)
            self.labelNu2.config(text="{0:.0f}".format(scanrate))

            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")

        except:
            self.labelImport.config(text="Error importing file.")

    def ReshapeData(self):
        self.potential = self.potential0.copy()
        self.currents_reshape = self.currents_reshape0.copy()

        # Calculate theoretical iss value
        try:
            if self.checkNormalize.var.get() == 1:
                beta = 1 + (0.23 / ((((float(self.entryRg.get())) ** 3) - 0.81) ** 0.36))
                self.iss = 4 * 1E9 * 96485 * beta * (float(self.entryDiff.get())) * (
                            (float(self.entryRadius.get())) / 1E6) * (float(self.entryConc.get()))
                self.labelTheoIssValue.config(text="{0:.3f}".format(self.iss))
            else:
                pass
        except:
            print("Error calculating theoretical steady state current.")

        # Convert units if necessary
        if self.potentialVar.get() == "V":
            pass
        else:  # mV case
            self.potential = self.potential * 1E3

        if self.currentVar.get() == "nA":
            pass
        elif self.currentVar.get() == "µA":
            self.currents_reshape = self.currents_reshape / 1E3
        else:  # pA
            self.currents_reshape = self.currents_reshape * 1E3

        # Calculate formal potential
        try:
            current_deriv = np.gradient(self.currents_reshape[0, :])

            # Find max value of derivative
            check_max = current_deriv == np.amax(current_deriv)
            max_index = np.where(check_max == True)
            max_index = int(max_index[0])
            pot_max = self.potential[max_index]

            # Find min value of derivative
            check_min = current_deriv == np.amin(current_deriv)
            min_index = np.where(check_min == True)
            min_index = int(min_index[0])
            pot_min = self.potential[min_index]

            self.avg_pot = np.mean([pot_max, pot_min])

            if self.checkStdPot.var.get() == 1:
                self.StdPot2.config(text="{0:.3f}".format(self.avg_pot))
            else:
                pass

            # Calculate experimental iss
            if self.statusNormalizeExp.get() == 1:
                try:
                    current_deriv = np.absolute(current_deriv)

                    # Look for two plateaus based on the derivatives
                    # Subtract them to calculate the expiss
                    # First in the beginning of the scan (before first peak),
                    # Second in the middle of the scan (between first and second peak)
                    if min_index > max_index:
                        check_iss = current_deriv[max_index:min_index] == np.amin(current_deriv[max_index:min_index])
                        check_iss2 = current_deriv[0:max_index] == np.amin(current_deriv[0:max_index])
                    else:
                        check_iss = current_deriv[min_index:max_index] == np.amin(current_deriv[min_index:max_index])
                        check_iss2 = current_deriv[0:min_index] == np.amin(current_deriv[0:min_index])

                    # Convert the index of the plateau to its corresponding current
                    iss_index = np.where(check_iss == True)
                    iss_index = int(iss_index[0][-1]) + np.amin([max_index, min_index])
                    iss_index2 = np.where(check_iss2 == True)
                    self.expiss = (self.currents_reshape[0, iss_index] - self.currents_reshape[0, iss_index2])[0, 0]
                    self.ExpIss2.config(text="{0:.3f}".format(self.expiss))

                except:
                    pass
            else:
                pass

        except:
            pass

        # Update figure with CV
        try:
            self.ax1.clear()

            # If loop to determine which cycle(s) to plot
            if self.multicycleVar.get() == "Plot all cycles":
                for i in range(0, self.ncycles):
                    if i == 0:
                        self.ax1.plot(self.potential, self.currents_reshape[i, :], label='Cycle 1')
                    elif i == self.ncycles - 1:
                        self.ax1.plot(self.potential, self.currents_reshape[i, :],
                                      label='Cycle {}'.format(self.ncycles))
                    else:
                        self.ax1.plot(self.potential, self.currents_reshape[i, :].T)
                    self.ax1.legend()

            elif self.multicycleVar.get() == "Plot second cycle to end":
                if self.ncycles == 1:
                    self.labelError.config(text="Error! Only one cycle detected.")
                    self.img = self.ax1.plot(self.potential, self.currents_reshape[0, :], label='Experimental')
                else:
                    self.img = self.ax1.plot(self.potential, (self.currents_reshape[1:-1, :]).T)

            elif self.multicycleVar.get() == "Plot specific cycle":
                try:
                    cycleno = int(self.entrySpCycle.get()) - 1
                    self.ax1.plot(self.potential, self.currents_reshape[cycleno, :],
                                  label='Cycle {}'.format((cycleno + 1)))
                    self.ax1.legend()
                    # Clear error label which might have been present previously
                    self.labelError.config(text="")
                except:
                    try:
                        if cycleno > self.ncycles:
                            self.labelError.config(text="Error! Requested cycle not found.")
                        else:
                            pass
                    except:
                        self.labelError.config(text="Error plotting requested cycle.")

            else:
                self.img = self.ax1.plot(self.potential, self.currents_reshape[0, :], label='Experimental')

            # Update x-axis label with entered reference electrode
            if self.entryRefElec.get() != '':
                self.ax1.set_xlabel('Potential vs. {} ({})'.format(self.entryRefElec.get(), self.potentialVar.get()))
            else:
                self.ax1.set_xlabel('Potential vs. Ag/AgCl ({})'.format(self.potentialVar.get()))
            self.ax1.set_ylabel('Current ({})'.format(self.currentVar.get()))

            # If loop to add theoretical iss line
            if self.checkNormalize.var.get() == 1:
                self.ax1.axhline(y=self.iss, color='black', linewidth=1, label='Theoretical iss')
                self.ax1.legend()
            else:
                pass

            # If loop to add experimental iss line
            if self.checkNormalizeExp.var.get() == 1:

                self.currents_reshape[0, iss_index]
                self.ax1.axhline(y=self.currents_reshape[0, iss_index], color='black', linewidth=1, linestyle=':',
                                 label='Experimental iss')
                self.ax1.axhline(y=self.currents_reshape[0, iss_index2], color='black', linewidth=1, linestyle=':')
                self.ax1.legend()
            else:
                pass

            # If loop to add calculated standard potential
            if self.checkStdPot.var.get() == 1:
                self.ax1.axvline(x=self.avg_pot, color='black', linewidth=1, linestyle='--', label='Formal Potential')
                self.ax1.legend()
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

            self.canvas.draw()
            self.buttonSave.config(state="normal")

        except:
            print("Data imported, call to update canvas CV failed.")

        self.buttonExport.config(state="normal")

    def BoxesSelected(self):
        # Enable/disable entry fields for calculating theoretical iss
        if self.checkNormalize.var.get() == 1:
            self.entryRadius.config(state="normal")
            self.entryRg.config(state="normal")
            self.entryConc.config(state="normal")
            self.entryDiff.config(state="normal")
        else:
            pass

    def SaveFig(self):
        try:
            print("Save requested.")

            self.fig.savefig(fname=asksaveasfilename(
                initialdir="/", title="Select file",
                filetypes=(("png", "*.png"), ("all files", "*.*"))), dpi=400)
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
        fh.write("Units of potential: {} \n".format(self.potentialVar.get()))

        # Report theoretical iss
        if self.statusNormalize.get() == 1:
            iss = self.iss
            fh.write("Theoretical steady state current (nA): {0:.3f} \n".format(iss))
        else:
            iss = 'N/A'
            fh.write("Theoretical steady state current (nA): {} \n".format(iss))

        # Report experimental iss
        if self.statusNormalizeExp.get() == 1:
            expiss = self.expiss
            fh.write("Experimental steady state current: {0:.3f} \n".format(expiss))
        else:
            expiss = 'N/A'
            fh.write("Experimental steady state current: {} \n".format(expiss))

        # Report formal potential
        if self.statusStdPot.get() == 1:
            stdpot = self.avg_pot
            fh.write("Standard potential (V vs. ref): {0:.3f} \n".format(stdpot))
        else:
            stdpot = 'Not calculated.'
            fh.write("Standard potential (V vs. ref): {} \n".format(stdpot))
        fh.write(" \n")

        # Print 1D array of potentials
        fh.write("Potential: \n")
        np.savetxt(fh, self.potential, delimiter=',', fmt='%1.4e')
        fh.write(" \n")

        # Print 2D array of currents
        fh.write("Current ({} cycles): \n".format(self.ncycles))
        np.savetxt(fh, self.currents_reshape.T, delimiter=',', fmt='%1.4e')
        fh.write(" \n")

        fh.close()
        self.labelPlot.config(text="Data exported.")

    def ResetWindow(self):
        print("Reset requested.")

        try:
            del self.df
        except:
            pass

        # Reset graph
        self.ax1.clear()
        #        self.img = self.ax1.plot(potential,currents)
        self.ax1.set_xlabel('Potential vs. Ag/AgCl (V)')
        self.ax1.set_ylabel('Current (nA)')
        self.canvas.draw()

        # Reset labels and buttons to default states

        # Buttons
        self.buttonImport.config(state="disabled")
        self.buttonPlot.config(state="disabled")
        self.buttonSave.config(state="disabled")
        self.buttonExport.config(state="disabled")
        self.textVar.set('None')

        # Labels
        self.labelFile.config(text="")
        self.labelImport.config(text="Select file to continue.")
        self.labelPlot.config(text="Import data to begin.")
        self.labelTheoIssValue.config(text="")
        self.StdPot2.config(text="")
        self.labelCycles2.config(text="")
        self.labelNpts2.config(text="")
        self.labelNu2.config(text="")
        self.labelXCursor.config(text="X : ")
        self.labelYCursor.config(text="Y : ")

        # Entries
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
