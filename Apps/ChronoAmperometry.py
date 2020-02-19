# GUI
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename
from tkinter import ttk as ttk

# Numerical analysis
import numpy as np
import pandas as pd

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


class CAApp:
    """Handles data from chronoamperometry experiments.
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
            framePlot.columnconfigure(i, minsize=140)
            frameFormatting.columnconfigure(i, minsize=140)

        # Base frame
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
        textChoices = {'Biologic', 'CH Instruments', 'HEKA', 'Sensolytics'}
        popupText = tk.OptionMenu(frameBase, self.textVar, *textChoices)
        popupText.configure(width=15)
        popupText.grid(row=3, column=2, sticky="W")
        #        # link function to change dropdown
        self.textVar.trace('w', self.change_dropdown)

        # Label for number of pts
        labelPts = tk.Label(frameBase, text="# pts:")
        labelPts.grid(row=1, column=3, padx=10, sticky="E")
        self.labelPts2 = tk.Label(frameBase, text="")
        self.labelPts2.grid(row=1, column=4, padx=10, sticky="W")

        # Label for constant potential applied
        labelConPot = tk.Label(frameBase, text="Potential (V vs. ref):")
        labelConPot.grid(row=2, column=3, padx=10, sticky="E")
        self.ConPot2 = tk.Label(frameBase, text="")
        self.ConPot2.grid(row=2, column=4, padx=10, sticky="W")

        # Analytics frame
        # Intro
        labelAnalytics = tk.Label(frameAnalytics, text="Customize the data treatment.")
        labelAnalytics.grid(row=0, column=0, padx=20, pady=10, sticky="WS")

        # Toggle for calculating theoretical steady state current
        self.statusNormalize = tk.IntVar()
        self.checkNormalize = tk.Checkbutton(frameAnalytics, text="Plot theoretical iss?", variable=self.statusNormalize, command=self.BoxesSelected)
        self.checkNormalize.var = self.statusNormalize
        self.checkNormalize.grid(row=1, column=0, sticky="E", padx=10)

        # Toggle for calculating experimental steady state current
        self.statusNormalizeExp = tk.IntVar()
        self.checkNormalizeExp = tk.Checkbutton(frameAnalytics, text="Calculate experimental iss?", variable=self.statusNormalizeExp)
        self.checkNormalizeExp.var = self.statusNormalizeExp
        self.checkNormalizeExp.grid(row=2, column=0, sticky="E", padx=10)

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

        # Toggle for calculating response time
        self.statusResponsetime = tk.IntVar()
        self.checkResponsetime = tk.Checkbutton(frameAnalytics, text="Calculate response time?", variable=self.statusResponsetime)
        self.checkResponsetime.var = self.statusResponsetime
        self.checkResponsetime.grid(row=3, column=0, rowspan=2, sticky="E", padx=10)

        # Label for reporting calculated response time
        labelResponsetime = tk.Label(frameAnalytics, text="Response time (s)")
        labelResponsetime.grid(row=3, column=1, padx=10, sticky="W")
        self.labelResponsetime = tk.Label(frameAnalytics, text="")
        self.labelResponsetime.grid(row=4, column=1, padx=10, sticky="W")

        # Formatting menu
        # Intro
        labelFormatting = tk.Label(frameFormatting, text="Customize the formatting of the graph.")
        labelFormatting.grid(row=0, column=0, padx=20, pady=5, columnspan=3, sticky="W")

        # Dropdown menu for units on distance
        # Label for dropdown menu
        labelTime = tk.Label(frameFormatting, text="Units (Time)")
        labelTime.grid(row=1, column=1, sticky="W", padx=10)
        # Create a stringvar which will contian the eventual choice
        self.timeVar = tk.StringVar(master)
        self.timeVar.set('s')  # set the default option
        # Dictionary with options
        timeChoices = {'s', 'min', 'ms'}
        popupTime = tk.OptionMenu(frameFormatting, self.timeVar, *timeChoices)
        popupTime.configure(width=10)
        popupTime.grid(row=2, column=1, sticky="W", padx=10)
        #        # link function to change dropdown
        self.timeVar.trace('w', self.change_dropdown)

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

        ############ Plot frame #############
        # Button for generating plot
        self.buttonPlot = tk.Button(framePlot, text="Plot Data", state="disabled", command=self.ReshapeData)
        self.buttonPlot.grid(row=0, column=1, rowspan=2, sticky="W" + "E")
        self.labelPlot = tk.Label(framePlot, text="Import data to begin.")
        self.labelPlot.grid(row=0, column=2, rowspan=2, sticky="W", padx=10)

        # Button for saving the plot
        self.buttonSave = tk.Button(framePlot, text="Save Figure", state="disabled", command=self.save_figure)
        self.buttonSave.grid(row=0, column=3, rowspan=2, sticky="W" + "E", padx=10)

        # Button for exporting to text file
        self.buttonExport = tk.Button(framePlot, text="Export Data", state="disabled", command=self.export_data_action)
        self.buttonExport.grid(row=0, column=4, sticky="W" + "E", padx=10)

        # Button for resetting window
        self.buttonReset = tk.Button(framePlot, text="Reset Window", command=self.ResetWindow)
        self.buttonReset.grid(row=0, column=5, padx=20, pady=10, sticky="W" + "E")

        # Bottom frame: Figure

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
        self.fig = Figure(figsize=(5, 4), dpi=120)

        # Plot CV using dummy values
        self.ax1 = self.fig.add_subplot(111)
        #        self.img = self.ax1.plot(self.time,self.currents)
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Current (nA)')

        self.fig.subplots_adjust(top=0.95, bottom=0.15, left=0.2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frameBottom)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="S")
        self.canvas.mpl_connect('button_press_event', DataCursor)
        self.canvas.draw()

        self.last_dir = ""
        # values that will hold the status of the checkboxes at the time the data was last plotted
        self.statNorm = 0
        self.statRT = 0
        self.statNormXP = 0

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
            if self.filename[-3:].lower() == 'asc':
                self.textVar.set('HEKA')
            elif self.filename[-3:].lower() == 'mat':
                self.textVar.set('HEKA')
            elif self.filename[-3:].lower() == 'dat':
                self.textVar.set('Sensolytics')
            else:
                pass
        except:
            self.ResetWindow()

    def ImportFile(self):
        # Check if manufacturer needed
        if self.filename[-3:].lower() == 'txt' and self.textVar.get() == 'None':
            self.labelImport.config(text="Specify a manufacturer.")
        ### ASC / HEKA import ###
        if self.filename[-3:].lower() == 'asc':
            self.import_heka(self.filepath)
        ### Biologic import ###
        elif self.filename[-3:].lower() == 'txt' and self.textVar.get() == "Biologic":
            self.import_biologic(self.filepath)
        ### CH Instruments import ###
        elif self.filename[-3:].lower() == 'txt' and self.textVar.get() == "CH Instruments":
            self.import_ch_instruments(self.filepath)
        ### Sensolytics import ###
        elif self.filename[-3:].lower() == 'dat':
            self.import_sensolytics(self.filepath)
        else:
            self.labelImport.config(text="File type not supported.")

    """
    Looking to extend the import file functionality to support a different file type?
    The ReshapeData function assumes the following is present after the ImportFile function has run:
        > self.time = 1D numpy array containing sampling times
        > self.currents = 1D numpy array containing currents
        > self.expiss = Experimental steady state current

    """

    def import_heka(self, filepath):
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
            self.labelImport.config(text="Could not import file.")

        self.labelImport.config(text="File imported.")
        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")

        # Convert raw data to matrix
        try:
            df = pd.DataFrame(data, columns=["PtIndex", "Time (s)", "Current (A)", "Time (s)", "Potential (V)"], dtype='float')
            df = df.values
            df[:, 2] = df[:, 2] * 1E9  # A --> nA

            # Determine number of pts
            npts = len(df)
            conpot = np.mean(df[-20:-1, 4])

            # Determine iss from last 5% of data points
            npts_iss = int(np.floor(npts) * 0.05)
            self.expiss = np.mean(df[-npts_iss:-1, 2])

            # Create current and potential columns accordingly
            self.time = df[:, 1]
            self.currents = df[:, 2]

            self.labelPts2.config(text=npts)
            self.ConPot2.config(text="{0:.3f}".format(conpot))

            if self.checkNormalizeExp.var.get() == 1:
                self.ExpIss2.config(text="{0:.3f}".format(self.expiss))
            else:
                pass

        except:
            print("Error importing data.")

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
        df = pd.DataFrame(data, columns=["Time (s)", "Current (A)"], dtype=float)
        df = df.values

        df[:, 1] = df[:, 1] * 1E9  # A --> nA

        # Update labels
        self.labelImport.config(text="File imported.")
        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")

        # Reshape data
        try:
            # Determine number of pts
            npts = len(df)

            # Determine iss from last 5% of data points
            npts_iss = int(np.floor(npts) * 0.05)
            self.expiss = np.mean(df[-npts_iss:-1, 1])
            #                self.expiss = np.mean(df[-20:-1,1])

            # Create time and current variables
            self.time = df[:, 0]
            self.currents = df[:, 1]
            self.labelPts2.config(text=npts)

            # Potential not present in this file format, configure label.
            self.ConPot2.config(text="Not available.")

        except:
            self.labelImport.config(text="Error importing file.")

    def import_ch_instruments(self, filepath):
        # Import file
        data = []
        index = 0
        try:
            # First read to extract data
            with open(filepath, 'r') as fh:
                for curline in fh:
                    try:
                        curline = curline.split(',')
                        if curline == ['Time/sec', ' Current/A\n']:
                            datastart = 1
                        if datastart == 1:
                            float(curline[0])  # check if line contains strings or numbers
                            data.append(curline)  # if number, add to dataframe
                    except:
                        pass  # if string, skip to next line
                fh.close()

            # Second read to extract constant potential
            with open(filepath, 'r') as fh2:
                for curline2 in fh2:
                    index = index + 1
                    if index == 10:  # The scan rate info can be found in this line
                        conpot = curline2.split('=')
                        conpot = float(conpot[1].strip('\n'))
                    else:
                        pass
        except:
            self.labelImport.config(text="Could not import file.")

        # Process file into consistent format for ReshapeData
        df = pd.DataFrame(data, columns=["Time (s)", "Current (A)"], dtype=float)
        df = df.values

        df[:, 1] = df[:, 1] * 1E9  # A --> nA

        # Update labels
        self.labelImport.config(text="File imported.")
        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")

        # Reshape data
        try:
            # Determine number of pts
            npts = len(df)

            # Determine iss from last 5% of data points
            npts_iss = int(np.floor(npts) * 0.05)
            self.expiss = np.mean(df[-npts_iss:-1, 1])
            #                self.expiss = np.mean(df[-20:-1,1])

            # Create time and current variables
            self.time = df[:, 0]
            self.currents = df[:, 1]
            self.currents = self.currents * (-1)  # polarographic --> IUPAC convention
            self.labelPts2.config(text=npts)

            # Potential not present in this file format, configure label.
            self.ConPot2.config(text="{0:.3f}".format(conpot))

        except:
            self.labelImport.config(text="Error importing file.")

    def import_sensolytics(self, filepath):
        data = []
        header = []
        index = 0

        try:
            with open(filepath, 'r') as fh:
                for curline in fh:
                    if curline[0] == '#':
                        curline = curline.split('\t')
                        header.append(curline)
                    else:
                        curline = curline.split(',')
                        data.append(curline)
            fh.close()

            # Determine number of channels from header line 3, use to determine number of cols needed
            nchannels = str(header[2]).split(':')
            nchannels = int(nchannels[1].strip(" \]n'"))

            # Determine experimental type from header line 2 (determines whether col 2 is a potential or a current)
            method = str(header[1])
            method = method.split(': ')

            if nchannels == 2:
                df = pd.DataFrame(data, columns=['Time (s)', 'Current (A)', 'NA'], dtype=float)
                del df['NA']

                # replace commas with periods so the values will be interpreted correctly
                header[17][1] = header[17][1].replace(",", ".")
                conpot = float(header[17][1].strip(' \n'))

            elif nchannels == 3:
                # Case 1 : Pulsed amperometry (1 WE)
                if method[1][0:3] == 'Pul':
                    df = pd.DataFrame(data, columns=['Time (s)', 'Potential (V)', 'Current (A)', 'NA'], dtype=float)
                    # rearrange so current is in col index 1 as before
                    df = df[['Time (s)', 'Current (A)', 'Potential (V)', 'NA']]
                    del df['NA']

                    conpot = 'Pulse sequence.'
                # Case 2: Amperometry (2 WE)
                else:
                    df = pd.DataFrame(data, columns=['Time (s)', 'Current1 (A)', 'Current2 (A)', 'NA'], dtype=float)
                    # rearrange so current is in col index 1 as before
                    del df['NA']

                    # replace commas with periods so the values will be interpreted correctly
                    header[19][1] = header[19][1].replace(",", ".")
                    conpot = float(header[19][1].strip(' \n'))

            elif nchannels == 4:
                df = pd.DataFrame(data, columns=['Time (s)', 'Potential (V)', 'Current1 (A)', 'Current2 (A)', 'NA'],
                                  dtype=float)
                df = df[['Time (s)', 'Current1 (A)', 'Potential (V)', 'Current2 (A)', 'NA']]
                del df['NA']

                conpot = 'Pulse sequence.'

            df = df.values
            df[:, 1] = df[:, 1] * 1E9  # A --> nA

            # Update labels
            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")

            # Reshape data
            try:
                # Determine number of pts
                npts = len(df)

                # Determine iss from last 5% of data points
                npts_iss = int(np.floor(npts) * 0.05)
                self.expiss = np.mean(df[-npts_iss:-1, 1])
                #                    self.expiss = np.mean(df[-20:-1,1])

                # Create time and current variables
                self.time = df[:, 0]
                self.currents = df[:, 1]
                self.labelPts2.config(text=npts)

                if type(conpot) == float:
                    self.ConPot2.config(text="{0:.3f}".format(conpot))
                else:
                    self.ConPot2.config(text=conpot)

            except:
                self.labelImport.config(text="Error importing file.")

        except:
            self.labelImport.config(text="Error importing file.")

    def ReshapeData(self):

        # Report experimental iss if requested
        if self.checkNormalizeExp.var.get() == 1:
            self.ExpIss2.config(text="{0:.3f}".format(self.expiss))
        else:
            pass

        # Calculate response time
        try:
            critvalue = abs(1.1 * self.expiss)

            # Procedure: Search trace from end to find the first point where the current is 110% iss
            if self.expiss < 0:
                rtcurrent = np.flip(np.absolute(self.currents))
            elif self.expiss > 0:
                rtcurrent = np.flip(self.currents)
            else:
                print('Error in detecting iss. Cannot calculate response time.')
            modcol = rtcurrent > critvalue
            critpt = np.amin(np.where(modcol == True))
            self.crittime = self.time[-critpt]

            if self.checkResponsetime.var.get() == 1:
                self.labelResponsetime.config(text="{0:.3f}".format(self.crittime))
            else:
                pass

            # Convert time variable + response time depending on user choice
            if self.timeVar.get() == "s":
                pass
            elif self.timeVar.get() == "ms":
                self.time = self.time * 1E3
                self.crittime = self.crittime * 1E3
            elif self.timeVar.get() == "min":
                self.time = self.time / 60
                self.crittime = self.crittime / 60

        except:
            print("Error calculating response time.")

        # Calculate theoretical iss
        try:
            if self.checkNormalize.var.get() == 1:
                beta = 1 + (0.23 / ((((float(self.entryRg.get())) ** 3) - 0.81) ** 0.36))
                self.iss = 4 * 1E9 * 96485 * beta * (float(self.entryDiff.get())) * ((float(self.entryRadius.get())) / 1E6) * (float(self.entryConc.get()))
                self.labelTheoIssValue.config(text="{0:.3f}".format(self.iss))
            else:
                pass
        except:
            print("Error calculating theoretical steady state current.")

        # Convert current units if requested
        if self.currentVar.get() == "nA":
            pass
        elif self.currentVar.get() == "µA":
            self.currents = self.currents / 1E3
            try:
                self.iss = self.iss / 1E3
            except:
                pass
            try:
                self.expiss = self.expiss / 1E3
            except:
                pass
        elif self.currentVar.get() == "pA":
            self.currents = self.currents * 1E3
            try:
                self.iss = self.iss * 1E3
            except:
                pass
            try:
                self.expiss = self.expiss * 1E3
            except:
                pass

        # Update figure with CA
        try:
            self.ax1.clear()

            # Query other properties of the graph to figure out if a legend label is needed
            if self.checkNormalize.var.get() == 1 or self.checkNormalizeExp.var.get() == 1 or self.checkResponsetime.var.get() == 1:
                self.img = self.ax1.plot(self.time, self.currents, label='Experimental')
            else:
                self.img = self.ax1.plot(self.time, self.currents)
            self.ax1.set_xlabel('Time ({})'.format(self.timeVar.get()))
            self.ax1.set_ylabel('Current ({})'.format(self.currentVar.get()))

            # If loop to add theoretical iss line
            if self.checkNormalize.var.get() == 1:
                self.ax1.axhline(y=self.iss, color='black', linewidth=1, linestyle='--', label='Theoretical iss')
                self.ax1.legend()
            else:
                pass

            # If loop to add experimental iss line
            if self.checkNormalizeExp.var.get() == 1:
                self.ax1.axhline(y=self.expiss, color='black', linewidth=1, label='Experimental iss')
                self.ax1.legend()
            else:
                pass

            # If loop to add response time line
            if self.checkResponsetime.var.get() == 1:
                self.ax1.axvline(x=self.crittime, color='red', linewidth=1, label='Response time')
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
            self.buttonExport.config(state="normal")

        except:
            print("Data imported, call to update canvas CA failed.")
        # save checkbox statuses
        self.statNorm = self.statusNormalize.get()
        self.statNormXP = self.statusNormalizeExp.get()
        self.statRT = self.statusResponsetime.get()

    def BoxesSelected(self):
        # Enable/disable entry fields for calculating theoretical iss
        if self.checkNormalize.var.get() == 1:
            self.entryRadius.config(state="normal")
            self.entryRg.config(state="normal")
            self.entryConc.config(state="normal")
            self.entryDiff.config(state="normal")
        else:
            pass

    def save_figure(self):
        """Saves the figure that is currently being displayed by the app"""
        try:
            filepath = asksaveasfilename(initialdir=self.last_dir + "/", title="Select file",
                                         filetypes=(("png", "*.png"), ("all files", "*.*")))
            filename_start = filepath.rindex('/')
            self.last_dir = filepath[:filename_start]
            self.fig.savefig(fname=filepath, dpi=400)
            self.labelPlot.config(text="Figure saved.")

        except:
            self.labelPlot.config(text="Error saving figure to file.")

    def export_data_action(self):
        """Exports the data in an ASCII file that can be read by most 3rd-party plotting software.
        The data is formatted as follows:
        #Headings
        #
        #Time, current
        t,I
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
                    fh.write("#FLUX: CA\n")
                    fh.write("#Original file: {} \n".format(self.filename))
                    fh.write("#Units of current: {} \n".format(self.currentVar.get()))
                    fh.write("#Units of time: {} \n".format(self.timeVar.get()))

                    if self.statNorm == 1:
                        theoiss = self.iss
                        fh.write("#Theoretical steady state current (nA): {0:.3f} \n".format(theoiss))
                    else:
                        theoiss = 'Not calculated'
                        fh.write("#Theoretical steady state current (nA): {} \n".format(theoiss))

                    if self.statNormXP == 1:
                        expiss = self.expiss
                    else:
                        expiss = 'Not calculated'
                    fh.write("#Experimental steady state current (nA): {} \n".format(expiss))

                    if self.statRT == 1:
                        rt = self.crittime
                        fh.write("#Response time: {0:.3f} \n".format(rt))
                    else:
                        fh.write("#Response time: Not calculated \n")

                    fh.write("# \n")
                    # Data block
                    fh.write("#Time, Current")
                    for t in range(len(self.time)):
                        fh.write("\n{0:1.4E},{1:1.4E}".format(self.time[t], self.currents[t]))
                    # Below is the old data export code:
                    # Print 1D array of time
                    # fh.write("Time: \n")
                    # np.savetxt(fh, self.time, delimiter=',', fmt='%1.4e')
                    # fh.write(" \n")

                    # Print 1D array of current
                    # fh.write("Current: \n")
                    # np.savetxt(fh, self.currents, delimiter=',', fmt='%1.4e')
                    # fh.write(" \n")

                    fh.close()
                    self.labelPlot.config(text="Data exported.")
            except:
                self.labelPlot.config(text="Error whilst exporting data.")

    def ResetWindow(self):
        print("Reset requested.")

        # Reset graph
        self.ax1.clear()
        #        self.img = self.ax1.plot(self.time,self.currents)
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Current (nA)')
        self.canvas.draw()

        # Checkboxes
        self.checkNormalize.var.set(0)
        self.checkNormalizeExp.var.set(0)
        self.checkResponsetime.var.set(0)

        # Buttons
        self.buttonImport.config(state="disabled")
        self.buttonPlot.config(state="disabled")
        self.buttonSave.config(state="disabled")
        self.buttonExport.config(state="disabled")

        # Labels
        self.labelFile.config(text="")
        self.labelImport.config(text="Select file to continue.")
        self.labelPlot.config(text="Import data to begin.")
        self.labelTheoIssValue.config(text="")
        self.labelPts2.config(text="")
        self.ConPot2.config(text="")
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
