# -*- coding: utf-8 -*-
"""  
Flux: Source Code
v1.0
Developed by: Lisa Stephens
License: GNU GPL v3

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

"""
Import packages
"""

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

""" 
Main window
"""

"""
Functions
"""

# Dropdown to select app
def change_dropdown(*args):
    buttonGo.config(state="normal")
    
# Select which app to open
def OpenWindow():
    global root
    global CVroot
    global CAroot
    global PACroot
    
    if tkvar.get() == "Image":
        # Open imaging window
        root=tk.Toplevel()
        root.title('Flux')
        root.wm_iconbitmap('supporting/flux_logo.ico')
#        root.grab_set() # keep focus on window upon events
        ImageApp(root)
        
        ## Set up menubar
        menubar = tk.Menu(root)   
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help",command=MenuPages.GuidePage)
        helpmenu.add_command(label="Theory",command=MenuPages.TheoryPage)
        helpmenu.add_command(label="About",command=MenuPages.AboutPage)
        menubar.add_cascade(label="Help",menu=helpmenu)
        root.config(menu=menubar)
        
        root.mainloop() # Initialize program

    elif tkvar.get() == "Cyclic Voltammogram":     
        ## Main window
        CVroot = tk.Toplevel()
        CVroot.title('Flux') # window title
        CVroot.wm_iconbitmap('supporting/flux_logo.ico') # window icon
#        CVroot.grab_set() # keep focus on window upon events
        CVApp(CVroot) # class where program to run in window is defined

        
        ## Set up menubar
        menubar = tk.Menu(CVroot)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help",command=MenuPagesCV.GuidePage)
        helpmenu.add_command(label="Theory",command=MenuPagesCV.TheoryPage)
        helpmenu.add_command(label="About",command=MenuPagesCV.AboutPage)
        menubar.add_cascade(label="Help",menu=helpmenu)
        CVroot.config(menu=menubar)    
       
        CVroot.mainloop()  # Initialize program     
        
    elif tkvar.get() == "Chronoamperogram":     
        ## Main window
        CAroot = tk.Toplevel()
        CAroot.title('Flux') # window title
        CAroot.wm_iconbitmap('supporting/flux_logo.ico') # window icon
#        CAroot.grab_set() # keep focus on window upon events
        CAApp(CAroot) # class where program to run in window is defined
    
        ## Set up menubar
        menubar = tk.Menu(CAroot)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help",command=MenuPagesCA.GuidePage)
        helpmenu.add_command(label="Theory",command=MenuPagesCA.TheoryPage)
        helpmenu.add_command(label="About",command=MenuPagesCA.AboutPage)
        menubar.add_cascade(label="Help",menu=helpmenu)
        CAroot.config(menu=menubar)    
       
        CAroot.mainloop()  # Initialize program     
        
    elif tkvar.get() == "Approach curve":     
        ## Main window
        PACroot = tk.Toplevel()
        PACroot.title('Flux') # window title
        PACroot.wm_iconbitmap('supporting/flux_logo.ico') # window icon
#        PACroot.grab_set() # keep focus on window upon events
        PACApp(PACroot) # class where program to run in window is defined
    
        ## Set up menubar
        menubar = tk.Menu(PACroot)
        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help",command=MenuPagesPAC.GuidePage)
        helpmenu.add_command(label="Theory",command=MenuPagesPAC.TheoryPage)
        helpmenu.add_command(label="About",command=MenuPagesPAC.AboutPage)
        menubar.add_cascade(label="Help",menu=helpmenu)
        PACroot.config(menu=menubar)    
       
        PACroot.mainloop()  # Initialize program     
    
    else:
        labelSupport.config(text="Still in development.")
        

class ImageApp:
    # Setup main window
    def __init__(self, master):    
        #initial values to be overwritten
        try:
            xpos[0]
        except:
            xpos = np.array([0,1])
            ypos = np.array([0,1])
            currents = np.array([[0,1],[0,1]])
            
            xpos_interp = np.array([0,1])
            ypos_interp = np.array([0,1])
            currents_edges = np.array([[0,1],[0,1]])
        
        # Create containers
        tabs = ttk.Notebook(master)
        frameBase = tk.Frame(tabs)
        frameAnalytics = tk.Frame(tabs)
        frameFormatting = tk.Frame(tabs)
        tabs.add(frameBase, text="  Base  ")
        tabs.add(frameAnalytics, text="  Analytics  ")
        tabs.add(frameFormatting, text="  Formatting  ")
        tabs.pack(expand=1,fill="both",side="top")
        
        framePlot = tk.Frame(master)
        framePlot.pack(side="top",pady=5)
        
        self.frameBottom = tk.Frame(master)
        self.frameBottom.pack(side="bottom")
        
        ###### Top frame: info about file ########  
        
        # set min column sizes to prevent excessive resizing
        for i in range(0,8):
            frameBase.columnconfigure(i,minsize=150)
            framePlot.columnconfigure(i,minsize=140)
            frameFormatting.columnconfigure(i,minsize=140)

        # Intro
        labelIntro = tk.Label(frameBase,text="Import experimental data to be plotted.")
        labelIntro.grid(row=0,column=0,padx=20,pady=5,columnspan=3,sticky="WS")
        
        # Select file
        self.buttonFile = tk.Button(frameBase, text="Select File",command=self.SelectFile)
        self.buttonFile.grid(row=1,column=1,sticky="W"+"E",padx=10)
        self.labelFile = tk.Label(frameBase,pady=10)
        self.labelFile.grid(row=1,column=2,sticky="W")
        
        # Import file
        self.buttonImport = tk.Button(frameBase,text = "Import File",state="disabled",command=self.ImportFile)
        self.buttonImport.grid(row=2,column=1,sticky="W"+"E",padx=10)
        self.labelImport = tk.Label(frameBase,text="Select file to continue.")
        self.labelImport.grid(row=2,column=2,sticky="W")
        
        # Dropdown menu for manufacturer (needed for files of different format, same extension)
        labelText = tk.Label(frameBase,text="Manufacturer: ")
        labelText.grid(row=3,column=1,sticky="E",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.textVar = tk.StringVar(master)
        self.textVar.set('None') # set the default option
        # Dictionary with options
        textChoices = { 'Biologic','CH Instruments','HEKA','Sensolytics','PAR'}
        popupText = tk.OptionMenu(frameBase, self.textVar, *textChoices)
        popupText.configure(width=15)
        popupText.grid(row=3,column=2,sticky="W")        
#        # link function to change dropdown
        self.textVar.trace('w', self.change_dropdown)
        
        # Specify sampling density of raw SECM image
        self.labelXdim = tk.Label(frameBase,text = "Number of x points: ")
        self.labelXdim.grid(row=1,column=3,sticky="W",padx=10)
        self.labelXdim2 = tk.Label(frameBase,text="")
        self.labelXdim2.grid(row=1,column=4,sticky="W")
    
        self.labelYdim = tk.Label(frameBase,text="Number of y points: ")
        self.labelYdim.grid(row=1,column=5,sticky="W",padx=10)
        self.labelYdim2 = tk.Label(frameBase,text="")
        self.labelYdim2.grid(row=1,column=6,sticky="W")
        
        # Specify sampling density of interpolated SECM image
        self.labelXinterp = tk.Label(frameBase,text="Interpolated x: ")
        self.labelXinterp.grid(row=2,column=3,sticky="W",padx=10)
        self.labelXinterp2 = tk.Label(frameBase,text="")
        self.labelXinterp2.grid(row=2,column=4,sticky="W")
        
        self.labelYinterp = tk.Label(frameBase,text="Interpolated y: ")
        self.labelYinterp.grid(row=2,column=5,sticky="W",padx=10)
        self.labelYinterp2 = tk.Label(frameBase,text="")
        self.labelYinterp2.grid(row=2,column=6,sticky="W")
        
        # Toggle for edge detection
        self.statusEdges = tk.IntVar()
        self.checkEdges = tk.Checkbutton(framePlot, text="Detect edges?", variable=self.statusEdges, command=self.BoxesSelected)
        self.checkEdges.var = self.statusEdges
        self.checkEdges.grid(row=0,column=0,sticky="E",padx=10,pady=5)  
        
        # Button for generating plot
        self.buttonPlot = tk.Button(framePlot,text="Plot Data",state="disabled",command=self.ReshapeData)
        self.buttonPlot.grid(row=0,column=1,rowspan=2,sticky="W"+"E")
        self.labelPlot = tk.Label(framePlot,text="Import data to begin.")
        self.labelPlot.grid(row=0,column=2,rowspan=2,sticky="W",padx=10)
        
        # Button for saving the plot
        self.buttonSave = tk.Button(framePlot,text="Save Figure",state="disabled",command=self.SaveFig)
        self.buttonSave.grid(row=0,column=3,rowspan=2,sticky="W"+"E",padx=10)
        
        # Button for exporting to text file
        self.buttonExport = tk.Button(framePlot,text="Export Data", state="disabled", command=self.SaveTxt)
        self.buttonExport.grid(row=0,column=4, sticky="W"+"E",padx=10)
        
        # Button for resetting window
        self.buttonReset = tk.Button(framePlot,text="Reset Window",command=self.ResetWindow)
        self.buttonReset.grid(row=0,column=5,padx=20,sticky="W"+"E")
        
        # Intro
        labelIntro = tk.Label(frameAnalytics,text="Customize the data treatment.")
        labelIntro.grid(row=0,column=0,padx=20,pady=5,columnspan=3,sticky="WS")
        
        # Toggle for normalizing currents
        self.statusNormalize = tk.IntVar()
        self.checkNormalize = tk.Checkbutton(frameAnalytics, text="Normalize currents?", variable=self.statusNormalize, command=self.BoxesSelected)
        self.checkNormalize.var = self.statusNormalize        
        self.checkNormalize.grid(row=1,column=0,sticky="E",padx=10)
                        
        # Toggle for theoretical/experimental normalization
        self.statusNormalizeExp = tk.IntVar()
        self.checkNormalizeExp = tk.Checkbutton(frameAnalytics, state="disabled",text="Using experimental iss?", variable=self.statusNormalizeExp, command=self.BoxesSelected)
        self.checkNormalizeExp.var = self.statusNormalizeExp 
        self.checkNormalizeExp.grid(row=2,column=0,sticky="E",padx=10)  
             
        # Dropdown menu for slope correction choices
        # Label for X-slope correction
        labelXslope = tk.Label(frameAnalytics,text="X-slope correction")
        labelXslope.grid(row=3,column=1,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.slopeXVar = tk.StringVar(master)
        self.slopeXVar.set('None') # set the default option
        # Dictionary with options
        slopeXChoices = { 'None','Y = 0','Y = Max'}
        popupSlopeX = tk.OptionMenu(frameAnalytics, self.slopeXVar, *slopeXChoices)
        popupSlopeX.configure(width=10)
        popupSlopeX.grid(row=4,column=1,sticky="W",padx=10)        
#        # link function to change dropdown
        self.slopeXVar.trace('w', self.change_dropdown)
        
        # Dropdown menu for slope correction choices
        # Label for Y-slope correction
        labelYslope = tk.Label(frameAnalytics,text="Y-slope correction")
        labelYslope.grid(row=3,column=2,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.slopeYVar = tk.StringVar(master)
        self.slopeYVar.set('None') # set the default option
        # Dictionary with options
        slopeYChoices = { 'None','X = 0','X = Max'}
        popupSlopeY = tk.OptionMenu(frameAnalytics, self.slopeYVar, *slopeYChoices)
        popupSlopeY.configure(width=10)
        popupSlopeY.grid(row=4,column=2,sticky="W",padx=10)        
#        # link function to change dropdown
        self.slopeYVar.trace('w', self.change_dropdown)
        
        # Input for accepting experimental iss
        labelIssExp = tk.Label(frameAnalytics,text="Expermental iss (nA)")
        labelIssExp.grid(row=1,column=6,padx=10,sticky="W")
        self.entryIssExp = tk.Entry(frameAnalytics, state="disabled")
        self.entryIssExp.grid(row=2,column =6, padx=10,sticky="W")
        
        # Input for accepting electrode parameters for theoretical iss
        labelRadius = tk.Label(frameAnalytics,text="Radius (µm)")
        labelRadius.grid(row=1,column=1,padx=10,sticky="W")
        self.entryRadius = tk.Entry(frameAnalytics, state="disabled")
        self.entryRadius.grid(row=2,column=1,padx=10,sticky="W")
        
        labelRg = tk.Label(frameAnalytics,text="Rg")
        labelRg.grid(row=1,column=2,padx=10,sticky="W")
        self.entryRg = tk.Entry(frameAnalytics,state="disabled")
        self.entryRg.grid(row=2,column=2,padx=10,sticky="W")
        
        labelConc = tk.Label(frameAnalytics,text="Conc. (mM)")
        labelConc.grid(row=1,column=3,padx=10,sticky="W")
        self.entryConc = tk.Entry(frameAnalytics,state="disabled")
        self.entryConc.grid(row=2,column=3,padx=10,sticky="W")
        
        labelDiff = tk.Label(frameAnalytics,text="Diff. coeff. (m^2/s)")
        labelDiff.grid(row=1,column=4,padx=10,sticky="W")
        self.entryDiff = tk.Entry(frameAnalytics,state="disabled")
        self.entryDiff.grid(row=2,column=4,padx=10,sticky="W")
        
        labelTheoIss = tk.Label(frameAnalytics,text="Theoretical iss (nA)")
        labelTheoIss.grid(row=1,column=5,padx=10,sticky="W")
        self.labelTheoIssValue = tk.Label(frameAnalytics,text="")
        self.labelTheoIssValue.grid(row=2,column=5,padx=10,sticky="W")
        
        ######## Formatting menu ########
        # Intro
        labelFormatting = tk.Label(frameFormatting,text="Customize the formatting of the graph.")
        labelFormatting.grid(row=0,column=0,padx=20,pady=5,columnspan=3,sticky="W")
        
        # Dropdown menu for colormap choices
        # Label for X-slope correction
        labelColormap = tk.Label(frameFormatting,text="Colourmap")
        labelColormap.grid(row=1,column=1,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.colormapVar = tk.StringVar(master)
        self.colormapVar.set('RdYlBu') # set the default option
        # Dictionary with options
        colormapChoices = { 'RdYlBu','coolwarm','jet','grayscale'}
        popupColormap = tk.OptionMenu(frameFormatting, self.colormapVar, *colormapChoices)
        popupColormap.configure(width=10)
        popupColormap.grid(row=2,column=1,sticky="W",padx=10)        
#        # link function to change dropdown
        self.colormapVar.trace('w', self.change_dropdown)
        
        # Dropdown menu for units on distance
        # Label for dropdown menu
        labelDistance = tk.Label(frameFormatting,text="Units (Distances)")
        labelDistance.grid(row=1,column=2,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.distanceVar = tk.StringVar(master)
        self.distanceVar.set('µm') # set the default option
        # Dictionary with options
        distanceChoices = {'mm','µm','nm'}
        popupDistances = tk.OptionMenu(frameFormatting, self.distanceVar, *distanceChoices)
        popupDistances.configure(width=10)
        popupDistances.grid(row=2,column=2,sticky="W",padx=10)        
#        # link function to change dropdown
        self.distanceVar.trace('w', self.change_dropdown)
        
        # Dropdown menu for units on current
        # Label for dropdown menu
        labelCurrent = tk.Label(frameFormatting,text="Units (Current)")
        labelCurrent.grid(row=1,column=3,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.currentVar = tk.StringVar(master)
        self.currentVar.set('nA') # set the default option
        # Dictionary with options
        currentChoices = {'µA','nA','pA'}
        popupCurrent = tk.OptionMenu(frameFormatting, self.currentVar, *currentChoices)
        popupCurrent.configure(width=10)
        popupCurrent.grid(row=2,column=3,sticky="W",padx=10)        
#        # link function to change dropdown
        self.currentVar.trace('w', self.change_dropdown)
        
        # Entry fields for controlling axis limits on plot
        labelXmin = tk.Label(frameFormatting,text="Xmin")
        labelXmin.grid(row=1,column=4,sticky="W",padx=10)
        self.entryXmin = tk.Entry(frameFormatting)
        self.entryXmin.grid(row=2,column=4,sticky="W",padx=10)
        
        labelXmax = tk.Label(frameFormatting,text="Xmax")
        labelXmax.grid(row=3,column=4,sticky="W",padx=10)
        self.entryXmax = tk.Entry(frameFormatting)
        self.entryXmax.grid(row=4,column=4,sticky="W",padx=10)
        
        labelYmin = tk.Label(frameFormatting,text="Ymin")
        labelYmin.grid(row=1,column=5,sticky="W",padx=10)
        self.entryYmin = tk.Entry(frameFormatting)
        self.entryYmin.grid(row=2,column=5,sticky="W",padx=10)
        
        labelYmax = tk.Label(frameFormatting,text="Ymax")
        labelYmax.grid(row=3,column=5,sticky="W",padx=10)
        self.entryYmax = tk.Entry(frameFormatting)
        self.entryYmax.grid(row=4,column=5,sticky="W",padx=10)
        
        labelZmin = tk.Label(frameFormatting,text="Zmin")
        labelZmin.grid(row=1,column=6,sticky="W",padx=10)
        self.entryZmin = tk.Entry(frameFormatting)
        self.entryZmin.grid(row=2,column=6,sticky="W",padx=10)
        
        labelZmax = tk.Label(frameFormatting,text="Zmax")
        labelZmax.grid(row=3,column=6,sticky="W",padx=10)
        self.entryZmax = tk.Entry(frameFormatting)
        self.entryZmax.grid(row=4,column=6,sticky="W",padx=10)

        # Data cursor setup        
        labelCursor = tk.Label(frameFormatting,text="Data Cursor")
        labelCursor.grid(row=1,column=7,sticky="W",padx=10)
        self.labelXCursor = tk.Label(frameFormatting,text="X : ")
        self.labelXCursor.grid(row=2,column=7,sticky="W",padx=10)
        self.labelYCursor = tk.Label(frameFormatting,text="Y : ")
        self.labelYCursor.grid(row=3,column=7,sticky="W",padx=10)
        
        
        ######### Bottom frame: Figure ###########
        # Start creating the plot
        self.fig = Figure(figsize=(9, 4), dpi=120)
        
        ### Left plot: Raw SECM image ###       
        self.ax1 = self.fig.add_subplot(121)
        self.ax1.set_aspect(1)
        self.img = self.ax1.pcolormesh(xpos,ypos,currents,cmap=cm.RdYlBu_r)
        # Generate axes to resize the colorbar properly
        divider = make_axes_locatable(self.ax1) 
        cax = divider.append_axes("right",size="5%",pad=0.1)
        # Add the color bar
        self.cb = self.fig.colorbar(self.img, cax=cax)
        self.cb.set_label('Current (nA)')
        # Set labels
        self.ax1.set_xlabel('X (µm)')
        self.ax1.set_ylabel('Y (µm)')
        
        ### Right plot: Detected edges ###
        self.ax2 = self.fig.add_subplot(122)
        self.ax2.set_aspect(1)
        self.edge = self.ax2.pcolormesh(xpos_interp,ypos_interp,currents_edges,cmap=cm.binary)              
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
        self.fig.subplots_adjust(left=0.07,right=1.0, top=0.95, bottom=0.15)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frameBottom)
        self.canvas.get_tk_widget().grid(row=1,column=0,sticky="S")
        self.canvas.mpl_connect('button_press_event',DataCursor)
        self.canvas.draw()   
        
    def change_dropdown(*args):
        pass
                  
    def SelectFile(self):
        self.filepath = askopenfilename(initialdir="/",
                               title = "Choose a file.")
        folder = []
        
        #check for folder symbols in filepath
        for c in self.filepath:
            folder.append(c == '/')
        folder = [i for i, j in enumerate(folder) if j == True]
        # trim off folder path to retrieve just filename
        self.filename = self.filepath[max(folder)+1:]
         
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
        else:
            pass
           
    def ImportFile(self):
        ## Check if manufacturer needed
        if self.filename[-3:] == 'txt' and self.textVar.get() == 'None':
            self.labelImport.config(text="Specify a manufacturer.")
                       
        ### ASC import ####
        elif self.filename[-3:] == 'asc':
            self.data = []
            try:
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        try:
                            curline = curline.split() # split line into segments
                            float(curline[0]) # check if line contains strings or numbers
                            self.data.append(curline) # if number, add to dataframe
                        except:
                            pass # if string, skip to next line
                self.labelImport.config(text="File imported.")
            except:
                self.labelImport.config(text="Could not import file.")
                
            # Convert raw data to matrix
            try:           
                self.df = pd.DataFrame(self.data,columns=["PtIndex","xpos","Current"],dtype='float')
                self.df = self.df.values
                
                self.df[:,1] = self.df[:,1]*1E6 # m --> um               
                self.df[:,2] = self.df[:,2]*1E9 # A --> nA
                
                self.nptsy = self.df[self.df[:,1] == 0]
                self.nptsy = len(self.nptsy)
                self.nptsx = int(len(self.df)/self.nptsy)
                
                self.labelXdim2.config(text=self.nptsx)
                self.labelYdim2.config(text=self.nptsy)

                # Set up grids for plotting
                self.xpos0 = np.unique(self.df[:,1])
                self.ypos0 = np.linspace(np.amin(self.xpos0),np.amax(self.xpos0), self.nptsy)
                self.currents0 = self.df[:,2]
                self.currents0 = self.currents0.reshape(self.nptsy,self.nptsx)
                
                del self.df
                
            except:
                print("Integer values for the number of points required.")
                
       ### MAT import ####
        elif self.filename[-3:] == 'mat':
           try:
               matdata = scipy.io.loadmat(self.filepath)
               # Delete non-data containing variables
               del matdata['__header__']
               del matdata['__globals__']
               del matdata['__version__']

               self.nptsy = len(matdata)
               data = []
               # Read once to determine dimensions
               for entry in matdata:
                   trace = matdata[entry]
                   self.xpos0 = trace[:,0]
                   self.nptsx = len(self.xpos0)

               # Read a second time to construct the appropriate table
               data = np.empty((self.nptsy, self.nptsx), dtype=float)
               count = 0
               for entry in matdata:
                   trace = matdata[entry]
                   data[count,:] = trace[:,1]
                   count = count + 1

               self.xpos0 = self.xpos0*1E6
               self.ypos0 = np.linspace(np.amin(self.xpos0),np.amax(self.xpos0), self.nptsy)
               self.currents0 = data*1E9

               self.labelImport.config(text="File imported.")

           except:
               self.labelImport.config(text="Could not import file.")

           self.labelXdim2.config(text=self.nptsx)
           self.labelYdim2.config(text=self.nptsy)
           
           
        ### TXT/Biologic import ####
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'Biologic':
            try:
                self.data = []
                datastart = 0 # toggle for determining if reading point cloud
                
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        try:    
                            curline = curline.split()
                            if curline == ['X','Y','Z']:
                                datastart = 1
                            if datastart == 1:
                                float(curline[0]) # check if line contains strings or numbers
                                self.data.append(curline) # if number, add to dataframe
                        except:
                            pass # if string, skip to next line
                
                self.df = pd.DataFrame(self.data, dtype='float')
                self.df = self.df.values
                
                self.df[:,2] = self.df[:,2]*1E9 # A --> nA
                self.nptsx = self.df[self.df[:,0] == 0]
                self.nptsx = len(self.nptsx)
                self.nptsy = int(len(self.df)/self.nptsx)
                
                self.xpos0 = np.unique(self.df[:,0])
                self.xpos0 = self.xpos0 - np.amin(self.xpos0)
                self.ypos0 = np.unique(self.df[:,1])
                self.ypos0 = self.ypos0 - np.amin(self.ypos0)
                self.currents0 = self.df[:,2]
                self.currents0 = self.currents0.reshape(self.nptsy,self.nptsx)                

                
                self.labelImport.config(text="File imported.")                   
                self.labelXdim2.config(text=self.nptsx)
                self.labelYdim2.config(text=self.nptsy)

                    
            except:
                self.labelImport.config(text="Could not import file.")
                
                
        ### TXT/CH instruments import ####
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'CH Instruments':
            try:
                self.data = []
                datastart = 0 # toggle for determining if reading point cloud
                
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        try:    
                            curline = curline.split(',')
                            if curline == ['X/um', ' Y/um', ' Current/A\n']:
                                datastart = 1
                            if datastart == 1:
                                float(curline[0]) # check if line contains strings or numbers
                                self.data.append(curline) # if number, add to dataframe
                        except:
                            pass # if string, skip to next line
                    
                self.df = pd.DataFrame(self.data, dtype='float')
                self.df = self.df.values
                
                self.df[:,2] = self.df[:,2]*1E9 # A --> nA
                self.nptsx = self.df[self.df[:,0] == 0]
                self.nptsx = len(self.nptsx)
                self.nptsy = int(len(self.df)/self.nptsx)
                
                self.xpos0 = np.unique(self.df[:,0])
                self.xpos0 = self.xpos0 - np.amin(self.xpos0)
                self.ypos0 = np.unique(self.df[:,1])
                self.ypos0 = self.ypos0 - np.amin(self.ypos0)
                self.currents0 = self.df[:,2] 
                self.currents0 = self.currents0.reshape(self.nptsy,self.nptsx)  
                self.currents0 = self.currents0*(-1) # polarographic --> IUPAC convention
                
                self.labelImport.config(text="File imported.")                   
                self.labelXdim2.config(text=self.nptsx)
                self.labelYdim2.config(text=self.nptsy)
                    
            except:
                self.labelImport.config(text="Could not import file.")
                
        ### DAT / Sensolytics import ###        
        elif self.filename[-3:] == 'dat':
            self.data = []
            header = []
            index = 0
            
            try: 
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        index = index + 1
                        if index <=23:
                            try:
                                curline = curline.split(':')
                                header.append(curline)
                            except:
                                pass
                        if index > 23:
                            try: 
                                curline = curline.split(',')
                                float(curline[0])
                                self.data.append(curline)
                            except:
                                pass
                    fh.close()
                                
                
                self.df = pd.DataFrame(self.data, columns=['X','Xrel','Y','Yrel','Z','Zrel','Ch1','Ch2'], dtype=float)
                del self.df['Ch2']
                self.df = self.df.values
                
                self.nptsx = int(header[5][1].strip(' \n')) + 1
                self.nptsy = int(header[6][1].strip(' \n')) + 1
                
                self.xpos0 = np.unique(self.df[:,1])
                self.ypos0 = np.unique(self.df[:,3])
                self.currents0 = self.df[:,6]
                self.currents0 = self.currents0.reshape(self.nptsy,self.nptsx)
    
                self.labelImport.config(text="File imported.")                   
                self.labelXdim2.config(text=self.nptsx)
                self.labelYdim2.config(text=self.nptsy)
                
            except:
                self.labelImport.config(text="Could not import file.")
                
                
        ### CSV / PAR import   
        elif self.filename[-3:] == 'csv':
            try:
                self.data = []
                header = []
                index = 0
                with open(self.filepath) as fh:
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
                with open(self.filepath) as fh:
                    self.data = pd.read_csv(fh,header=6, dtype=float)
                    self.ypos0 = self.data.iloc[:,-1]
                    fh.close()
                    
                with open(self.filepath) as fh:
                    # Read the second time, import data to table
                    self.data = pd.read_csv(fh,header=6,index_col=False)
                    fh.close()
                    
            except:
                self.labelImport.config(text="Could not import file.")
             
            # Process data into consistent form needed for ReshapeData
            try:
                # conversion of all quantities to numpy arrays
                self.xpos0 = np.transpose(np.array(header, dtype=float))
                self.xpos0 = np.unique(self.xpos0)
                self.xpos0 = self.xpos0*1E3 # mm --> um
                self.ypos0 = self.ypos0.values
                self.ypos0 = self.ypos0*1E3 # mm --> um
                self.currents0 = self.data.values
                self.currents0 = self.currents0*1E3 # uA --> nA
                
                self.nptsx = len(self.xpos0)
                self.nptsy = len(self.ypos0)
                
                
                self.labelImport.config(text="File imported.")                   
                self.labelXdim2.config(text=self.nptsx)
                self.labelYdim2.config(text=self.nptsy)     
                
            except:
                self.labelImport.config(text="Error processing file.")
                

        # Message to display if one of the above imports does not apply
        else:
            self.labelImport.config(text="File type not supported.")

        self.buttonPlot.config(state="normal")
        self.labelPlot.config(text="")  
        self.checkEdges.config(state="normal")
        
    """
    Looking to extend the import file functionality to support a different file type?
    The ReshapeData function assumes the following is present after the ImportFile function has run:
        > self.xpos0, self.ypos0 = 2 separate 1D numpys array containing unique x and y values respectively in µm
        > self.nptsx, self.nptsy = 2 separate integers containing the number of x and y points respectively
        > self.currents0 = 2D numpy array contianing current values in nA.
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
            self.xposG = self.xpos.copy()*1E3 # m --> um
            self.yposG = self.ypos.copy()*1E3
        elif self.distanceVar.get() == "mm":
            self.xposG = self.xpos.copy()/1E3 # m --> mm
            self.yposG = self.ypos.copy()/1E3 # m --> mm
        else:
            self.xposG = self.xpos.copy()
            self.yposG = self.ypos.copy()
        
        ### Slope correction
        # X-Slope correction
        if self.slopeXVar.get() == 'None':
            pass
        elif self.slopeXVar.get() == 'Y = 0':
            xslope0 = np.polyfit(self.xpos,self.currents[0,:],1)
            for i in range(0,(self.currents.shape[1])):
                self.currents[:,i] = self.currents0[:,i] - xslope0[0]*(self.xpos[i] - self.xpos[0])
        elif self.slopeXVar.get() == 'Y = Max':
            xslopemax = np.polyfit(self.xpos,self.currents0[-1,:],1)
            for i in range(0,(self.currents0.shape[1])):
                self.currents[:,i] = self.currents0[:,i] - xslopemax[0]*(self.xpos[i] - self.xpos[0])
        # Y-Slope correction
        if self.slopeYVar.get() == 'None':
            pass
        elif self.slopeYVar.get() == 'X = 0':
            yslope0 = np.polyfit(self.ypos,self.currents[:,0],1)
            for i in range(0,(self.currents.shape[0])):
                self.currents[i,:] = self.currents0[i,:] - yslope0[0]*(self.ypos[i] - self.ypos[0])
        elif self.slopeYVar.get() == 'X = Max':
            yslopemax = np.polyfit(self.ypos,self.currents[:,-1],1)
            for i in range(0,(self.currents.shape[0])):
                self.currents[i,:] = self.currents0[i,:] - yslopemax[0]*(self.ypos[i] - self.ypos[0])

        ## Normalization; if deselected, iss = 1 (no change)
        # No normalization
        if self.checkNormalize.var.get() == 0:
            self.iss = 1
        # Experimental normalization
        elif self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 1:
            self.iss = float(self.entryIssExp.get())
        # Theoretical normalization
        elif self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 0:
            beta = 1+ (0.23/((((float(self.entryRg.get()))**3) - 0.81)**0.36))                
            self.iss = 4*1E9*96485*beta*(float(self.entryDiff.get()))*((float(self.entryRadius.get()))/1E6)*(float(self.entryConc.get()))
            self.labelTheoIssValue.config(text="{0:.3f}".format(self.iss))
        else:                
            pass           
        
        self.currents = np.divide(self.currents,self.iss)
        
        # Convert current between nA/uA/pA if not normalized
        if self.checkNormalize.var.get() == 0:
            if self.currentVar.get() == "nA":  
                pass
            elif self.currentVar.get() == "µA":
                self.currents = self.currents/1E3
            elif self.currentVar.get() == "pA":
                self.currents = self.currents*1E3
        else:
            pass
        
        self.currents = self.currents.reshape(self.nptsy,self.nptsx)

        # Update interpolated dimension labels
        if self.checkEdges.var.get() == 1:              
            self.labelXinterp2.config(text="Processing...")
            self.labelYinterp2.config(text="Processing...")
            self.labelPlot.config(text="Processing...")
                     
        # Set up grids for plotting
        self.ypos_int = (np.amax(self.xpos) - np.amin(self.xpos))/(self.nptsy-1)
        self.ypos = np.arange(np.amin(self.xpos),(np.amax(self.xpos)+self.ypos_int),self.ypos_int)
        self.xpos_grid,self.ypos_grid = np.meshgrid(self.xpos,self.ypos)
                
        # Update figure with SECM image     
        try:
            self.ax1.clear()
            self.ax1.set_aspect(1)
            self.cb.remove()           
            
            # Colormap selection
            if self.colormapVar.get() == 'RdYlBu':
                self.img = self.ax1.pcolormesh(self.xposG,self.yposG,self.currents,cmap=cm.RdYlBu_r)
            elif self.colormapVar.get() == 'jet':
                 self.img = self.ax1.pcolormesh(self.xposG,self.yposG,self.currents,cmap=cm.jet)
            elif self.colormapVar.get() == 'coolwarm':
                 self.img = self.ax1.pcolormesh(self.xposG,self.yposG,self.currents,cmap=cm.coolwarm)
            elif self.colormapVar.get() == 'grayscale':
                 self.img = self.ax1.pcolormesh(self.xposG,self.yposG,self.currents,cmap=cm.Greys)                
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
            cax = divider.append_axes("right",size="5%",pad=0.1)
            self.cb = self.fig.colorbar(self.img,cax=cax)
                        
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

            # Create df to be compatible with edge detection algorithm
            ypos_int = np.amax(self.xpos)/((self.nptsy)-1)
            self.df = np.reshape(self.currents, (self.nptsx*self.nptsy))    
            self.dfycol = np.linspace(0,((self.nptsx*self.nptsy)-1),(self.nptsx*self.nptsy))
            
            # duct tape hack so that point where the floor function below get assigned to the correct row
            modcol = np.remainder(self.dfycol,self.nptsx)
            for i in range(0,len(modcol)):
                if modcol[i] == 0:
                    self.dfycol[i] = self.dfycol[i] + 1
            self.dfycol = ypos_int*(np.floor(np.divide(self.dfycol,self.nptsx)))
            
            self.df = np.vstack((numpy.matlib.repmat(self.xpos,1,self.nptsy), self.df))
            self.df = np.vstack((self.dfycol,self.df))
            self.df = self.df.T
            
            try:
                # Set up evenly spaced interpolation grids for edge detection
                try:
                    # Check if already evenly spaced; if yes, do nothing; if no, create grid @ 1 pt/um level
                    if self.nptsx != self.nptsy: 
                        xpos_interp = np.linspace(np.amin(self.xpos), np.amax(self.xpos), np.amax(self.xpos)+1)
                        ypos_interp = xpos_interp
                    else:
                        xpos_interp = self.xpos
                        ypos_interp = xpos_interp
                    xpos_unigrid, ypos_unigrid = np.meshgrid(xpos_interp, ypos_interp)
                
                    # Interpolate to prepare for edge detection
                    currents_interp = griddata((self.df[:,1],self.df[:,0]),self.df[:,2],(xpos_unigrid,ypos_unigrid),method='cubic')
                except:
                    print("Error interpolating data to uniform grid.")     
                
                currents_norm = (currents_interp - np.amin(currents_interp))/(np.amax(currents_interp) - np.amin(currents_interp))
                self.currents_edges = feature.canny(currents_norm)
                
                # Unit conversions
                if self.distanceVar.get() == "mm":
                    xpos_interp = xpos_interp.copy()/1E3
                    ypos_interp = ypos_interp.copy()/1E3
                elif self.distanceVar.get() == "nm":
                    xpos_interp = xpos_interp.copy()*1E3
                    ypos_interp = ypos_interp.copy()*1E3
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
                
                self.edge = self.ax2.pcolormesh(xpos_interp,ypos_interp,self.currents_edges,cmap=cm.binary)
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
                self.fig.savefig(fname= asksaveasfilename(
                        initialdir = "/",title = "Select file",
                        filetypes = (("png","*.png"),("all files","*.*"))),dpi=400)
                self.labelPlot.config(text="Figure saved.")
            # If no edges detected, only save SECM image
            else:
                # Determine dimensions of first subplot
                extent = self.ax1.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
                
                # Save the figure, expand the extent by 50% in x and 20% in y to include axis labels and colorbar
                self.fig.savefig(fname= asksaveasfilename(
                        initialdir = "/",title = "Select file",
                        filetypes = (("png","*.png"),("all files","*.*"))),
                        bbox_inches=extent.expanded(1.6,1.3),dpi=400)
                self.labelPlot.config(text="Figure saved.")
            
        except:
            self.labelPlot.config(text="Error saving figure to file.")
            
    def SaveTxt(self):
        
        # Prompt user to select a file name, open a text file with that name
        export = asksaveasfilename(initialdir="/",
                               filetypes =[("TXT File", "*.txt")],
                               title = "Choose a file.")
        fh = open(export + ".txt","w+")
        
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
        fh.write("Matrix of currents:  {} \n".format(self.nptsx*self.nptsy))   
        np.savetxt(fh, self.currents, delimiter=',', fmt='%1.4e')
        fh.write(" \n")
        
        # Print 2D array of detected edges
        if self.statusEdges.get() == 1:
            fh.write("Detected edges: \n")
            np.savetxt(fh, self.currents_edges, delimiter=',',fmt='%i')
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
        xpos = np.array([0,1])
        ypos = np.array([0,1])
        currents = np.array([[0,1],[0,1]])
        
        xpos_interp = np.array([0,1])
        ypos_interp = np.array([0,1])
        currents_edges = np.array([[0,1],[0,1]])
        
        # Reset graph
        self.ax1.clear()
        self.ax1.set_aspect(1)
        self.cb.remove()
#        self.fig.subplots_adjust(left=0.07,right=1.0)
        self.img = self.ax1.pcolormesh(xpos,ypos,currents,cmap=cm.RdYlBu_r)
        divider = make_axes_locatable(self.ax1) 
        cax = divider.append_axes("right",size="5%",pad=0.1)
        self.cb = self.fig.colorbar(self.img, cax=cax)
        self.cb.set_label('Current (nA)')
        self.ax1.set_xlabel('X (µm)')
        self.ax1.set_ylabel('Y (µm)')
        self.canvas.draw()
        self.ax2.clear()
        self.fig.subplots_adjust(left=0.07,right=1.0)
        self.edge = self.ax2.pcolormesh(xpos_interp,ypos_interp,currents_edges,cmap=cm.binary)
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
        self.entryIssExp.delete(0,"end")
        self.entryIssExp.config(state="disabled")
        self.entryRadius.delete(0,"end")
        self.entryRadius.config(state="disabled")
        self.entryRg.delete(0,"end")
        self.entryRg.config(state="disabled")
        self.entryConc.delete(0,"end")
        self.entryConc.config(state="disabled")
        self.entryDiff.delete(0,"end")
        self.entryDiff.config(state="disabled")
        self.entryXmin.delete(0,"end")
        self.entryXmax.delete(0,"end")
        self.entryYmin.delete(0,"end")
        self.entryYmax.delete(0,"end")
        self.entryZmin.delete(0,"end")
        self.entryZmax.delete(0,"end")
        
        
class CVApp:    
    def __init__(self, master):                    
        # Create containers
        tabs = ttk.Notebook(master)
        frameBase = tk.Frame(tabs)
        frameAnalytics = tk.Frame(tabs)
        frameFormatting = tk.Frame(tabs)
        tabs.add(frameBase, text="  Base  ")
        tabs.add(frameAnalytics, text="  Analytics  ")
        tabs.add(frameFormatting, text="  Formatting  ")
        tabs.pack(expand=1,fill="both",side="top")
        
        framePlot = tk.Frame(master)
        framePlot.pack(side="top",pady=5)
                     
        self.frameBottom = tk.Frame(master)
        self.frameBottom.pack(side="bottom")
        
        # set min column sizes to prevent excessive resizing
        for i in range(0,8):
            frameBase.columnconfigure(i,minsize=150)
            framePlot.columnconfigure(i,minsize=140)
            frameFormatting.columnconfigure(i,minsize=140)

        
        ###### Base frame #####
        # Intro
        labelIntro = tk.Label(frameBase,text="Import experimental data to be plotted.")
        labelIntro.grid(row=0,column=0,columnspan=6,padx=20,pady=10,sticky="WS")
                
        # Select file
        self.buttonFile = tk.Button(frameBase, text="Select File",command=self.SelectFile)
        self.buttonFile.grid(row=1,column=1,sticky="W"+"E",padx=10)
        self.labelFile = tk.Label(frameBase,text="")
        self.labelFile.grid(row=1,column=2,sticky="W")
        
        # Import file
        self.buttonImport = tk.Button(frameBase,text = "Import File",state="disabled",command=self.ImportFile)
        self.buttonImport.grid(row=2,column=1,sticky="W"+"E",padx=10)
        self.labelImport = tk.Label(frameBase,text="Select file to continue.")
        self.labelImport.grid(row=2,column=2,sticky="W")
        
        # Dropdown menu for manufacturer (needed for files of different format, same extension)
        labelText = tk.Label(frameBase,text="Manufacturer: ")
        labelText.grid(row=3,column=1,sticky="E",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.textVar = tk.StringVar(master)
        self.textVar.set('None') # set the default option
        # Dictionary with options
        textChoices = { 'Biologic','CH Instruments','HEKA','Sensolytics'}
        popupText = tk.OptionMenu(frameBase, self.textVar, *textChoices)
        popupText.configure(width=15)
        popupText.grid(row=3,column=2,sticky="W")        
#        # link function to change dropdown
        self.textVar.trace('w', self.change_dropdown)
        
        # Label for number of cycles
        labelCycles = tk.Label(frameBase,text="# cycles:")
        labelCycles.grid(row=1,column=3,padx=10,sticky="E")
        self.labelCycles2 = tk.Label(frameBase,text="")
        self.labelCycles2.grid(row=1,column=4,padx=10,sticky="W")
        
        # Label for number of point in each cycle
        labelNpts = tk.Label(frameBase,text="Pts/cycle:")
        labelNpts.grid(row=2,column=3,padx=10,sticky="E")
        self.labelNpts2 = tk.Label(frameBase,text="")
        self.labelNpts2.grid(row=2,column=4,padx=10,sticky="W")
        
        # Label for scan rate
        labelNu = tk.Label(frameBase,text="Scan rate (mV/s):")
        labelNu.grid(row=3,column=3,padx=10,pady=5,sticky="E")
        self.labelNu2 = tk.Label(frameBase,text="")
        self.labelNu2.grid(row=3,column=4,padx=10,sticky="W")
        
        # Dropdown menu for multicycle support
        # Create a stringvar which will contian the eventual choice
        self.multicycleVar = tk.StringVar(master)
        self.multicycleVar.set('Plot first cycle') # set the default option
        # Dictionary with options
        choices = { 'Plot first cycle','Plot second cycle to end','Plot all cycles','Plot specific cycle'}
        popupMulticycle = tk.OptionMenu(frameBase, self.multicycleVar, *choices)
        popupMulticycle.configure(width=20)
        popupMulticycle.grid(row=1,column=5,sticky="W",padx=10)        
#        # link function to change dropdown
        self.multicycleVar.trace('w', self.change_dropdown)
        
        # Entry field for getting specific cycle number to plot
        labelSpCycle = tk.Label(frameBase,text="Specific cycle: ")
        labelSpCycle.grid(row=2,column=5,sticky="W",padx=10)
        self.entrySpCycle = tk.Entry(frameBase, state='disabled')
        self.entrySpCycle.grid(row=3,column=5,sticky="W",padx=10)
        
        # Input for accepting reference electrode
        labelRefElec = tk.Label(frameBase,text="Reference electrode")
        labelRefElec.grid(row=1,column=6,padx=50,sticky="W")
        self.entryRefElec = tk.Entry(frameBase)
        self.entryRefElec.grid(row=2,column=6, padx=50,sticky="W")
        
        # Label for returning error if only one cycle
        self.labelError = tk.Label(frameBase,text="")
        self.labelError.grid(row=0,column=5,sticky="W",padx=10)
        
        ###### Analytics frame #####
        # Intro
        labelAnalytics = tk.Label(frameAnalytics,text="Customize the data treatment.")
        labelAnalytics.grid(row=0,column=0,padx=20,pady=10,sticky="WS")
        
        # Toggle for calculating theoretical steady state current
        self.statusNormalize = tk.IntVar()
        self.checkNormalize = tk.Checkbutton(frameAnalytics, text="Plot theoretical iss?", variable=self.statusNormalize, command=self.BoxesSelected)
        self.checkNormalize.var = self.statusNormalize        
        self.checkNormalize.grid(row=1,column=0,sticky="E",padx=10)
        
        # Toggle for calculating experimental steady state current
        self.statusNormalizeExp = tk.IntVar()
        self.checkNormalizeExp = tk.Checkbutton(frameAnalytics, text="Calculate experimental iss?", variable=self.statusNormalizeExp)
        self.checkNormalizeExp.var = self.statusNormalizeExp        
        self.checkNormalizeExp.grid(row=2,column=0,sticky="E",padx=10)
                
        # Toggle for calculating standard potential
        self.statusStdPot = tk.IntVar()
        self.checkStdPot = tk.Checkbutton(frameAnalytics, text="Calculate formal potential?", variable=self.statusStdPot, command=self.BoxesSelected)
        self.checkStdPot.var = self.statusStdPot
        self.checkStdPot.grid(row=3,column=0,rowspan=2,sticky="E",padx=10,pady=10)  
        
        # Label for reporting calculated standard potential
        labelStdPot = tk.Label(frameAnalytics,text="Formal potential (V vs. ref)")
        labelStdPot.grid(row=3,column=1,padx=10)
        self.StdPot2 = tk.Label(frameAnalytics,text="")
        self.StdPot2.grid(row=4,column=1,padx=10,sticky="W")
 
        # Input for accepting electrode parameters for theoretical iss
        labelRadius = tk.Label(frameAnalytics,text="Radius (µm)")
        labelRadius.grid(row=1,column=1,padx=10,sticky="W")
        self.entryRadius = tk.Entry(frameAnalytics, state="disabled")
        self.entryRadius.grid(row=2,column=1,padx=10,sticky="W")
        
        labelRg = tk.Label(frameAnalytics,text="Rg")
        labelRg.grid(row=1,column=2,padx=10,sticky="W")
        self.entryRg = tk.Entry(frameAnalytics,state="disabled")
        self.entryRg.grid(row=2,column=2,padx=10,sticky="W")
        
        labelConc = tk.Label(frameAnalytics,text="Conc. (mM)")
        labelConc.grid(row=1,column=3,padx=10,sticky="W")
        self.entryConc = tk.Entry(frameAnalytics,state="disabled")
        self.entryConc.grid(row=2,column=3,padx=10,sticky="W")
        
        labelDiff = tk.Label(frameAnalytics,text="Diff. coeff. (m^2/s)")
        labelDiff.grid(row=1,column=4,padx=10,sticky="W")
        self.entryDiff = tk.Entry(frameAnalytics,state="disabled")
        self.entryDiff.grid(row=2,column=4,padx=10,sticky="W")
        
        labelTheoIss = tk.Label(frameAnalytics,text="Theoretical iss (nA)")
        labelTheoIss.grid(row=1,column=5,padx=10,sticky="W")
        self.labelTheoIssValue = tk.Label(frameAnalytics,text="")
        self.labelTheoIssValue.grid(row=2,column=5,padx=10,sticky="W")
        
        # Label for reporting calculated experimental steady state current
        labelExpIss = tk.Label(frameAnalytics,text="Experimental iss (nA)")
        labelExpIss.grid(row=1,column=6,padx=10)
        self.ExpIss2 = tk.Label(frameAnalytics,text="")
        self.ExpIss2.grid(row=2,column=6,padx=10,sticky="W")
        
        
        
        # Button for generating plot
        self.buttonPlot = tk.Button(framePlot,text="Plot Data",state="disabled",command=self.ReshapeData)
        self.buttonPlot.grid(row=0,column=1,rowspan=2,sticky="W"+"E")
        self.labelPlot = tk.Label(framePlot,text="Import data to begin.")
        self.labelPlot.grid(row=0,column=2,rowspan=2,sticky="W",padx=10)
        
        # Button for saving the plot
        self.buttonSave = tk.Button(framePlot,text="Save Figure",state="disabled",command=self.SaveFig)
        self.buttonSave.grid(row=0,column=3,rowspan=2,sticky="W"+"E",padx=10)
        
        # Button for exporting to text file
        self.buttonExport = tk.Button(framePlot,text="Export Data", state="disabled", command=self.SaveTxt)
        self.buttonExport.grid(row=0,column=4, sticky="W"+"E",padx=10)
        
        # Button for resetting window
        self.buttonReset = tk.Button(framePlot,text="Reset Window",command=self.ResetWindow)
        self.buttonReset.grid(row=0,column=5,padx=20,pady=10,sticky="W"+"E")
        
        ######## Formatting menu ########
        # Intro
        labelFormatting = tk.Label(frameFormatting,text="Customize the formatting of the graph.")
        labelFormatting.grid(row=0,column=0,padx=20,pady=5,columnspan=3,sticky="W")
               
        # Dropdown menu for units on distance
        # Label for dropdown menu
        labelPotential = tk.Label(frameFormatting,text="Units (Potential)")
        labelPotential.grid(row=1,column=1,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.potentialVar = tk.StringVar(master)
        self.potentialVar.set('V') # set the default option
        # Dictionary with options
        potentialChoices = {'V','mV'}
        popupPotential = tk.OptionMenu(frameFormatting, self.potentialVar, *potentialChoices)
        popupPotential.configure(width=10)
        popupPotential.grid(row=2,column=1,sticky="W",padx=10)        
#        # link function to change dropdown
        self.potentialVar.trace('w', self.change_dropdown)
        
        # Dropdown menu for units on current
        # Label for dropdown menu
        labelCurrent = tk.Label(frameFormatting,text="Units (Current)")
        labelCurrent.grid(row=1,column=2,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.currentVar = tk.StringVar(master)
        self.currentVar.set('nA') # set the default option
        # Dictionary with options
        currentChoices = {'µA','nA','pA'}
        popupCurrent = tk.OptionMenu(frameFormatting, self.currentVar, *currentChoices)
        popupCurrent.configure(width=10)
        popupCurrent.grid(row=2,column=2,sticky="W",padx=10)        
#        # link function to change dropdown
        self.currentVar.trace('w', self.change_dropdown)
        
        # Entry fields for controlling axis limits on plot
        labelXmin = tk.Label(frameFormatting,text="Xmin")
        labelXmin.grid(row=1,column=3,sticky="W",padx=10)
        self.entryXmin = tk.Entry(frameFormatting)
        self.entryXmin.grid(row=2,column=3,sticky="W",padx=10)
        
        labelXmax = tk.Label(frameFormatting,text="Xmax")
        labelXmax.grid(row=3,column=3,sticky="W",padx=10)
        self.entryXmax = tk.Entry(frameFormatting)
        self.entryXmax.grid(row=4,column=3,sticky="W",padx=10)
        
        labelYmin = tk.Label(frameFormatting,text="Ymin")
        labelYmin.grid(row=1,column=4,sticky="W",padx=10)
        self.entryYmin = tk.Entry(frameFormatting)
        self.entryYmin.grid(row=2,column=4,sticky="W",padx=10)
        
        labelYmax = tk.Label(frameFormatting,text="Ymax")
        labelYmax.grid(row=3,column=4,sticky="W",padx=10)
        self.entryYmax = tk.Entry(frameFormatting)
        self.entryYmax.grid(row=4,column=4,sticky="W",padx=10)
        
        # Data cursor setup        
        labelCursor = tk.Label(frameFormatting,text="Data Cursor")
        labelCursor.grid(row=1,column=5,sticky="W",padx=10)
        self.labelXCursor = tk.Label(frameFormatting,text="X : ")
        self.labelXCursor.grid(row=2,column=5,sticky="W",padx=10)
        self.labelYCursor = tk.Label(frameFormatting,text="Y : ")
        self.labelYCursor.grid(row=3,column=5,sticky="W",padx=10)
           
               
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

        self.fig.subplots_adjust(top=0.95,bottom=0.15,left=0.2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frameBottom)
        self.canvas.get_tk_widget().grid(row=1,column=0,sticky="S")
        self.canvas.mpl_connect('button_press_event',DataCursor)
        self.canvas.draw()   
        

    def change_dropdown(self, *args):
        if self.multicycleVar.get() == 'Plot specific cycle':
            self.entrySpCycle.config(state="normal")
        else:
            self.entrySpCycle.config(state="disabled")
    
    def SelectFile(self):
        self.filepath = askopenfilename(initialdir="/",
                               title = "Choose a file.")
        folder = []
        
        #check for folder symbols in filepath
        for c in self.filepath:
            folder.append(c == '/')
        folder = [i for i, j in enumerate(folder) if j == True]
        # trim off folder path to retrieve just filename
        self.filename = self.filepath[max(folder)+1:]
         
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
            # Import data file
            self.data=[]
            try:
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        try:
                            curline = curline.split() # split line into segments
                            float(curline[0]) # check if line contains strings or numbers
                            self.data.append(curline) # if number, add to dataframe
                        except:
                            pass # if string, skip to next line
                    fh.close()       
                    
            except:
                self.labelImport.config(text="Error importing file.")
                
            # Convert raw data to matrix
            try:           
                df = pd.DataFrame(self.data,columns=["PtIndex","Time (s)","Current (A)","Time (s)","Potential (V)"],dtype='float')
                df = df.values
    
                df[:,2] = df[:,2]*1E9 # A --> nA
                
                # Determine number of cycles
                self.ncycles = df[df[:,1] == 0]
                self.ncycles = len(self.ncycles)
                nptscycle = int(len(df)/self.ncycles)
    
                self.potential0 = df[0:nptscycle,4]
                self.currents0 = df[:,2]
                self.currents_reshape0 = self.currents0.reshape(self.ncycles,nptscycle)
                
                # Calculate scan rate in mV/s
                critpt = int(np.floor(nptscycle/4))
                print(critpt)
                scanrate = 1000*((df[critpt,4] - df[0,4])/(df[critpt,1] - df[0,1]))
                self.labelNu2.config(text="{0:.0f}".format(scanrate))
                           
                self.labelCycles2.config(text=self.ncycles)
                self.labelNpts2.config(text=nptscycle)
                
                self.labelImport.config(text="File imported.")
                self.buttonPlot.config(state="normal")
                self.labelPlot.config(text="")  
           
            except:
                self.labelImport.config(text="Could not import file.")
                
                
       ### MAT / HEKA import ####
        elif self.filename[-3:] == 'mat':
           try:
               matdata = scipy.io.loadmat(self.filepath)
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
                   self.potential0 = trace[:,1]
                   self.nptscycle = len(self.potential0)
    
               # Read a second time to construct the appropriate table
               data = np.empty((self.ncycles, self.nptscycle), dtype=float)
               count = 0
               for entry in matdata:
                   try:
                       # Trace A_B_C_1 = Current
                       if np.remainder(count,2) == 0:
                           trace2 = matdata[entry]
                           data[count,:] = trace2[:,1]
                       # Trace A_B_C_2 = Potential
                       else:
                           pass
                   except:
                       pass
                   count = count + 1
               self.currents_reshape0 = data*1E9
    
               self.labelImport.config(text="File imported.")

           except:
               self.labelImport.config(text="Could not import file.")

           try:
                # Calculate scan rate in mV/s
                critpt = int(np.floor(self.nptscycle/4))
                scanrate = 1000*((trace[critpt,1] - trace[0,1])/(trace[critpt,0] - trace[0,0]))
                self.labelNu2.config(text="{0:.0f}".format(scanrate))

                self.labelCycles2.config(text=self.ncycles)
                self.labelNpts2.config(text=self.nptscycle)
                
                self.buttonPlot.config(state="normal")
                self.labelPlot.config(text="")  
           except:
                self.labelImport.config(text="Error processing file.")
                
                
        ### TXT / Biologic import ###
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'Biologic':
            
            # Import file
            self.data = []
            try:
                with open(self.filepath,'r') as fh:
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
            df = pd.DataFrame(self.data, columns = ["Potential (V)","Current (A"], dtype=float)
            df = df.values
            
            df[:,1] = df[:,1] * 1E9 # A --> nA
            
            # Determine number of cycles based on number of max peak potential is reached
            self.ncycles = df[df[:,0] == np.amax(df[:,0])]
            self.ncycles = len(self.ncycles)
            self.nptscycle = int(len(df)/self.ncycles)
            
            self.potential0 = df[0:self.nptscycle,0]
            self.currents0 = df[:,1]
            self.labelNu2.config(text="Not available.")
            
            
            # Reshape into matrix where rows = cycles
            # If there is an extra point at the end (start/end on same potential), omit this point
            try:
                self.currents_reshape0 = self.currents0.reshape(self.ncycles,self.nptscycle)
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
            
            
        ### TXT/CH instruments import ####
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'CH Instruments':
            try:
                self.data = []
                datastart = 0 # toggle for determining if reading point cloud
                index = 0
                
                # First read to extract data
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        try: 
                            curline = curline.split(',')
                            if curline == ['Potential/V', ' Current/A\n']:
                                datastart = 1
                            if datastart == 1:
                                float(curline[0]) # check if line contains strings or numbers
                                self.data.append(curline) # if number, add to dataframe
                        except:
                            pass # if string, skip to next line
                    fh.close()
                                                    
                # Second read to extract scan rate
                with open(self.filepath,'r') as fh2:
                    for curline2 in fh2:
                        index = index + 1
                        if index == 13: # The scan rate info can be found in this line
                            nu = curline2.split('=')
                            nu = 1000*(float(nu[1].strip('\n')))
                        else:
                            pass
                    
                df = pd.DataFrame(self.data, dtype='float')
                df = df.values
                
                df[:,1] = df[:,1] * 1E9 # A --> nA
                            
                # Determine number of cycles based on number of max peak potential is reached
                self.ncycles = df[df[:,0] == np.amax(df[:,0])]
                self.ncycles = len(self.ncycles)
                self.nptscycle = int(len(df)/self.ncycles)
                
                self.potential0 = df[0:self.nptscycle,0]
                self.currents0 = df[:,1]
                self.currents0 = self.currents0*(-1) # polarographic --> IUPAC convention
                self.labelNu2.config(text="{0:.0f}".format(nu))
                
                # Reshape into matrix where rows = cycles
                # If there is an extra point at the end (start/end on same potential), omit this point
                try:
                    self.currents_reshape0 = self.currents0.reshape(self.ncycles,self.nptscycle)
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
                
                
        ### DAT / Sensolytics import ###        
        elif self.filename[-3:] == 'dat':
            self.data = []
            header = []
            index = 0
            
            try: 
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        index = index + 1
                        if index <=20:
                            try:
                                curline = curline.split('\t')
                                header.append(curline)
                            except:
                                pass
                        if index > 20:
                            try: 
                                curline = curline.split(',')
                                float(curline[0])
                                self.data.append(curline)
                            except:
                                pass
                    fh.close()
                                
                scanrate = 1000*(float(header[18][1].strip(' \n'))) 
                
                df = pd.DataFrame(self.data, columns=['Potential (V)','Current (A)','NA'], dtype=float)
                del df['NA']
                df = df.values
                df[:,1] = df[:,1]*1E9 # A --> nA
                
                self.ncycles = df[df[:,0] == np.amax(df[:,0])]
                self.ncycles = len(self.ncycles)
                nptscycle = int(len(df)/self.ncycles)
                
                self.potential0 = df[0:nptscycle,0]
                self.currents0 = df[:,1]
                self.currents_reshape0 = self.currents0.reshape(self.ncycles,nptscycle)
                
                self.labelCycles2.config(text=self.ncycles)
                self.labelNpts2.config(text=nptscycle)
                self.labelNu2.config(text="{0:.0f}".format(scanrate))
    
                self.labelImport.config(text="File imported.")
                self.buttonPlot.config(state="normal")
                self.labelPlot.config(text="")                 
                
            except:
                self.labelImport.config(text="Error importing file.")
            
        
        else:
            self.labelImport.config(text="File type not supported.")
        

    """
    Looking to extend the import file functionality to support a different file type?
    The ReshapeData function assumes the following is present after the ImportFile function has run:
        > self.potential = 1D numpy array containing potential values in volts for one sweep
        > self.currents_reshape = 2D numpy array containing current values in amps; each row is one cycle
        > self.ncycles = Integer corresponding to the number of cycles
        
    """

    def ReshapeData(self):
        self.potential = self.potential0.copy()
        self.currents_reshape = self.currents_reshape0.copy()
        
        # Calculate theoretical iss value
        try:
            if self.checkNormalize.var.get() == 1:
                beta = 1+ (0.23/((((float(self.entryRg.get()))**3) - 0.81)**0.36))                
                self.iss = 4*1E9*96485*beta*(float(self.entryDiff.get()))*((float(self.entryRadius.get()))/1E6)*(float(self.entryConc.get()))
                self.labelTheoIssValue.config(text="{0:.3f}".format(self.iss))
            else:                
                pass           
        except:
            print("Error calculating theoretical steady state current.")

        # Convert units if necessary
        if self.potentialVar.get() == "V":
            pass
        else: # mV case
            self.potential = self.potential*1E3
            
        if self.currentVar.get() == "nA":
            pass
        elif self.currentVar.get() == "µA":
            self.currents_reshape = self.currents_reshape/1E3
        else: # pA
            self.currents_reshape = self.currents_reshape*1E3
            
        # Calculate formal potential       
        try:
            current_deriv = np.gradient(self.currents_reshape[0,:])
        
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
            
            self.avg_pot = np.mean([pot_max,pot_min])
            
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
                    else:
                        check_iss = current_deriv[min_index:max_index] == np.amin(current_deriv[min_index:max_index])
                    
                    # Convert the index of the plateau to its corresponding current
                    iss_index = np.where(check_iss == True)
                    iss_index = int(iss_index[0][-1]) + np.amin([max_index, min_index])    
                    self.expiss = self.currents_reshape[0,iss_index]
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
#                self.img = self.ax1.plot(self.potential,self.currents_reshape.T)
                for i in range(0,self.ncycles):
                    if i == 0:
                        self.ax1.plot(self.potential, self.currents_reshape[i,:], label = 'Cycle 1')
                    elif i == self.ncycles-1:
                        self.ax1.plot(self.potential, self.currents_reshape[i,:], label = 'Cycle {}'.format(self.ncycles))
                    else:
                        self.ax1.plot(self.potential, self.currents_reshape[i,:].T)
                    self.ax1.legend()
                
            elif self.multicycleVar.get() == "Plot second cycle to end":
                if self.ncycles == 1:
                    self.labelError.config(text="Error! Only one cycle detected.")
                    self.img = self.ax1.plot(self.potential,self.currents_reshape[0,:],label='Experimental')
                else:
                    self.img = self.ax1.plot(self.potential,(self.currents_reshape[1:-1,:]).T)
                    
            elif self.multicycleVar.get() == "Plot specific cycle":
                try:
                    cycleno = int(self.entrySpCycle.get()) - 1
                    self.ax1.plot(self.potential,self.currents_reshape[cycleno,:],label = 'Cycle {}'.format((cycleno+1)))
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
                self.img = self.ax1.plot(self.potential,self.currents_reshape[0,:],label='Experimental')

            # Update x-axis label with entered reference electrode
            if self.entryRefElec.get() != '':
                self.ax1.set_xlabel('Potential vs. {} ({})'.format(self.entryRefElec.get(), self.potentialVar.get()))
            else:
                self.ax1.set_xlabel('Potential vs. Ag/AgCl ({})'.format(self.potentialVar.get()))
            self.ax1.set_ylabel('Current ({})'.format(self.currentVar.get()))
            
            # If loop to add theoretical iss line
            if self.checkNormalize.var.get() == 1:
                self.ax1.axhline(y=self.iss,color='black',linewidth=1,label='Theoretical iss')
                self.ax1.legend()
            else:
                pass
            
            # If loop to add experimental iss line
            if self.checkNormalizeExp.var.get() == 1:
                self.ax1.axhline(y=self.expiss,color='black',linewidth=1,linestyle=':', label='Experimental iss')
                self.ax1.legend()
            else:
                pass
            
            # If loop to add calculated standard potential
            if self.checkStdPot.var.get() == 1:
                self.ax1.axvline(x=self.avg_pot,color='black',linewidth=1,linestyle='--',label='Formal Potential')
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

            self.fig.savefig(fname= asksaveasfilename(
                    initialdir = "/",title = "Select file",
                    filetypes = (("png","*.png"),("all files","*.*"))), dpi=400)
            self.labelPlot.config(text="Figure saved.")

            
        except:
            self.labelPlot.config(text="Error saving figure to file.")

    def SaveTxt(self):
    
        # Prompt user to select a file name, open a text file with that name
        export = asksaveasfilename(initialdir="/",
                               filetypes =[("TXT File", "*.txt")],
                               title = "Choose a file.")
        fh = open(export + ".txt","w+")
        
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
        self.entryRadius.delete(0,"end")
        self.entryRadius.config(state="disabled")
        self.entryRg.delete(0,"end")
        self.entryRg.config(state="disabled")
        self.entryConc.delete(0,"end")
        self.entryConc.config(state="disabled")
        self.entryDiff.delete(0,"end")
        self.entryDiff.config(state="disabled")
        self.entryXmin.delete(0,"end")
        self.entryXmax.delete(0,"end")
        self.entryYmin.delete(0,"end")
        self.entryYmax.delete(0,"end")

class CAApp:    
    def __init__(self, master):                   
        # Create containers
        tabs = ttk.Notebook(master)
        frameBase = tk.Frame(tabs)
        frameAnalytics = tk.Frame(tabs)
        frameFormatting = tk.Frame(tabs)
        tabs.add(frameBase, text="  Base  ")
        tabs.add(frameAnalytics, text="  Analytics  ")
        tabs.add(frameFormatting, text="  Formatting  ")
        tabs.pack(expand=1,fill="both",side="top")
        
        framePlot = tk.Frame(master)
        framePlot.pack(side="top",pady=5)
                     
        self.frameBottom = tk.Frame(master)
        self.frameBottom.pack(side="bottom")
        
        # set min column sizes to prevent excessive resizing
        for i in range(0,8):
            frameBase.columnconfigure(i,minsize=120)
            framePlot.columnconfigure(i,minsize=140)
            frameFormatting.columnconfigure(i,minsize=140)
        
        ###### Base frame #####
        # Intro
        labelIntro = tk.Label(frameBase,text="Import experimental data to be plotted.")
        labelIntro.grid(row=0,column=0,columnspan=6, padx=20,pady=10,sticky="WS")
                
        # Select file
        self.buttonFile = tk.Button(frameBase, text="Select File",command=self.SelectFile)
        self.buttonFile.grid(row=1,column=1,sticky="W"+"E",padx=10,pady=5)
        self.labelFile = tk.Label(frameBase,text="")
        self.labelFile.grid(row=1,column=2,sticky="W")
        
        # Import file
        self.buttonImport = tk.Button(frameBase,text = "Import File",state="disabled",command=self.ImportFile)
        self.buttonImport.grid(row=2,column=1,sticky="W"+"E",padx=10)
        self.labelImport = tk.Label(frameBase,text="Select file to continue.")
        self.labelImport.grid(row=2,column=2,sticky="W")
        
        # Dropdown menu for manufacturer (needed for files of different format, same extension)
        labelText = tk.Label(frameBase,text="Manufacturer: ")
        labelText.grid(row=3,column=1,sticky="E",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.textVar = tk.StringVar(master)
        self.textVar.set('None') # set the default option
        # Dictionary with options
        textChoices = { 'Biologic','CH Instruments','HEKA','Sensolytics'}
        popupText = tk.OptionMenu(frameBase, self.textVar, *textChoices)
        popupText.configure(width=15)
        popupText.grid(row=3,column=2,sticky="W")        
#        # link function to change dropdown
        self.textVar.trace('w', self.change_dropdown)
        
        # Label for number of pts
        labelPts = tk.Label(frameBase,text="# pts:")
        labelPts.grid(row=1,column=3,padx=10,sticky="E")
        self.labelPts2 = tk.Label(frameBase,text="")
        self.labelPts2.grid(row=1,column=4,padx=10,sticky="W")
        
        # Label for constant potential applied
        labelConPot = tk.Label(frameBase,text="Potential (V vs. ref):")
        labelConPot.grid(row=2,column=3,padx=10,sticky="E")
        self.ConPot2 = tk.Label(frameBase,text="")
        self.ConPot2.grid(row=2,column=4,padx=10,sticky="W")
               
        
        ###### Analytics frame #####
        # Intro
        labelAnalytics = tk.Label(frameAnalytics,text="Customize the data treatment.")
        labelAnalytics.grid(row=0,column=0,padx=20,pady=10,sticky="WS")
        
        # Toggle for calculating theoretical steady state current
        self.statusNormalize = tk.IntVar()
        self.checkNormalize = tk.Checkbutton(frameAnalytics, text="Plot theoretical iss?", variable=self.statusNormalize, command=self.BoxesSelected)
        self.checkNormalize.var = self.statusNormalize        
        self.checkNormalize.grid(row=1,column=0,sticky="E",padx=10)
        
        # Toggle for calculating experimental steady state current
        self.statusNormalizeExp = tk.IntVar()
        self.checkNormalizeExp = tk.Checkbutton(frameAnalytics, text="Calculate experimental iss?", variable=self.statusNormalizeExp)
        self.checkNormalizeExp.var = self.statusNormalizeExp        
        self.checkNormalizeExp.grid(row=2,column=0,sticky="E",padx=10)
 
        # Input for accepting electrode parameters for theoretical iss
        labelRadius = tk.Label(frameAnalytics,text="Radius (µm)")
        labelRadius.grid(row=1,column=1,padx=10,sticky="W")
        self.entryRadius = tk.Entry(frameAnalytics, state="disabled")
        self.entryRadius.grid(row=2,column=1,padx=10,sticky="W")
        
        labelRg = tk.Label(frameAnalytics,text="Rg")
        labelRg.grid(row=1,column=2,padx=10,sticky="W")
        self.entryRg = tk.Entry(frameAnalytics,state="disabled")
        self.entryRg.grid(row=2,column=2,padx=10,sticky="W")
        
        labelConc = tk.Label(frameAnalytics,text="Conc. (mM)")
        labelConc.grid(row=1,column=3,padx=10,sticky="W")
        self.entryConc = tk.Entry(frameAnalytics,state="disabled")
        self.entryConc.grid(row=2,column=3,padx=10,sticky="W")
        
        labelDiff = tk.Label(frameAnalytics,text="Diff. coeff. (m^2/s)")
        labelDiff.grid(row=1,column=4,padx=10,sticky="W")
        self.entryDiff = tk.Entry(frameAnalytics,state="disabled")
        self.entryDiff.grid(row=2,column=4,padx=10,sticky="W")
        
        labelTheoIss = tk.Label(frameAnalytics,text="Theoretical iss (nA)")
        labelTheoIss.grid(row=1,column=5,padx=10,sticky="W")
        self.labelTheoIssValue = tk.Label(frameAnalytics,text="")
        self.labelTheoIssValue.grid(row=2,column=5,padx=10,sticky="W")
        
        # Label for reporting calculated experimental steady state current
        labelExpIss = tk.Label(frameAnalytics,text="Experimental iss (nA)")
        labelExpIss.grid(row=1,column=6,padx=10)
        self.ExpIss2 = tk.Label(frameAnalytics,text="")
        self.ExpIss2.grid(row=2,column=6,padx=10,sticky="W")
        
        # Toggle for calculating response time
        self.statusResponsetime = tk.IntVar()
        self.checkResponsetime = tk.Checkbutton(frameAnalytics, text="Calculate response time?", variable=self.statusResponsetime)
        self.checkResponsetime.var = self.statusResponsetime      
        self.checkResponsetime.grid(row=3,column=0,rowspan=2,sticky="E",padx=10)
        
        # Label for reporting calculated response time
        labelResponsetime = tk.Label(frameAnalytics,text="Response time (s)")
        labelResponsetime.grid(row=3,column=1,padx=10,sticky="W")
        self.labelResponsetime = tk.Label(frameAnalytics,text="")
        self.labelResponsetime.grid(row=4,column=1,padx=10,sticky="W")
        
        ######## Formatting menu ########
        # Intro
        labelFormatting = tk.Label(frameFormatting,text="Customize the formatting of the graph.")
        labelFormatting.grid(row=0,column=0,padx=20,pady=5,columnspan=3,sticky="W")
               
        # Dropdown menu for units on distance
        # Label for dropdown menu
        labelTime = tk.Label(frameFormatting,text="Units (Time)")
        labelTime.grid(row=1,column=1,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.timeVar = tk.StringVar(master)
        self.timeVar.set('s') # set the default option
        # Dictionary with options
        timeChoices = {'s','min','ms'}
        popupTime = tk.OptionMenu(frameFormatting, self.timeVar, *timeChoices)
        popupTime.configure(width=10)
        popupTime.grid(row=2,column=1,sticky="W",padx=10)        
#        # link function to change dropdown
        self.timeVar.trace('w', self.change_dropdown)
        
        # Dropdown menu for units on current
        # Label for dropdown menu
        labelCurrent = tk.Label(frameFormatting,text="Units (Current)")
        labelCurrent.grid(row=1,column=2,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.currentVar = tk.StringVar(master)
        self.currentVar.set('nA') # set the default option
        # Dictionary with options
        currentChoices = {'µA','nA','pA'}
        popupCurrent = tk.OptionMenu(frameFormatting, self.currentVar, *currentChoices)
        popupCurrent.configure(width=10)
        popupCurrent.grid(row=2,column=2,sticky="W",padx=10)        
#        # link function to change dropdown
        self.currentVar.trace('w', self.change_dropdown)
        
        # Entry fields for controlling axis limits on plot
        labelXmin = tk.Label(frameFormatting,text="Xmin")
        labelXmin.grid(row=1,column=3,sticky="W",padx=10)
        self.entryXmin = tk.Entry(frameFormatting)
        self.entryXmin.grid(row=2,column=3,sticky="W",padx=10)
        
        labelXmax = tk.Label(frameFormatting,text="Xmax")
        labelXmax.grid(row=3,column=3,sticky="W",padx=10)
        self.entryXmax = tk.Entry(frameFormatting)
        self.entryXmax.grid(row=4,column=3,sticky="W",padx=10)
        
        labelYmin = tk.Label(frameFormatting,text="Ymin")
        labelYmin.grid(row=1,column=4,sticky="W",padx=10)
        self.entryYmin = tk.Entry(frameFormatting)
        self.entryYmin.grid(row=2,column=4,sticky="W",padx=10)
        
        labelYmax = tk.Label(frameFormatting,text="Ymax")
        labelYmax.grid(row=3,column=4,sticky="W",padx=10)
        self.entryYmax = tk.Entry(frameFormatting)
        self.entryYmax.grid(row=4,column=4,sticky="W",padx=10)
        
        # Data cursor setup        
        labelCursor = tk.Label(frameFormatting,text="Data Cursor")
        labelCursor.grid(row=1,column=5,sticky="W",padx=10)
        self.labelXCursor = tk.Label(frameFormatting,text="X : ")
        self.labelXCursor.grid(row=2,column=5,sticky="W",padx=10)
        self.labelYCursor = tk.Label(frameFormatting,text="Y : ")
        self.labelYCursor.grid(row=3,column=5,sticky="W",padx=10)
        
        
        ############ Plot frame #############
        # Button for generating plot
        self.buttonPlot = tk.Button(framePlot,text="Plot Data",state="disabled",command=self.ReshapeData)
        self.buttonPlot.grid(row=0,column=1,rowspan=2,sticky="W"+"E")
        self.labelPlot = tk.Label(framePlot,text="Import data to begin.")
        self.labelPlot.grid(row=0,column=2,rowspan=2,sticky="W",padx=10)
        
        # Button for saving the plot
        self.buttonSave = tk.Button(framePlot,text="Save Figure",state="disabled",command=self.SaveFig)
        self.buttonSave.grid(row=0,column=3,rowspan=2,sticky="W"+"E",padx=10)
               
        # Button for exporting to text file
        self.buttonExport = tk.Button(framePlot,text="Export Data", state="disabled", command=self.SaveTxt)
        self.buttonExport.grid(row=0,column=4, sticky="W"+"E",padx=10)
        
        # Button for resetting window
        self.buttonReset = tk.Button(framePlot,text="Reset Window",command=self.ResetWindow)
        self.buttonReset.grid(row=0,column=5,padx=20,pady=10,sticky="W"+"E")
               
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
        self.fig = Figure(figsize=(5, 4), dpi=120)
        
        # Plot CV using dummy values
        self.ax1 = self.fig.add_subplot(111)
#        self.img = self.ax1.plot(self.time,self.currents)
        self.ax1.set_xlabel('Time (s)')
        self.ax1.set_ylabel('Current (nA)')

        self.fig.subplots_adjust(top=0.95,bottom=0.15,left=0.2)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frameBottom)
        self.canvas.get_tk_widget().grid(row=1,column=0,sticky="S")
        self.canvas.mpl_connect('button_press_event',DataCursor)
        self.canvas.draw()   
        
    def change_dropdown(*args):
        pass
    
    def SelectFile(self):
        self.filepath = askopenfilename(initialdir="/",
                               title = "Choose a file.")
        folder = []
        
        #check for folder symbols in filepath
        for c in self.filepath:
            folder.append(c == '/')
        folder = [i for i, j in enumerate(folder) if j == True]
        # trim off folder path to retrieve just filename
        self.filename = self.filepath[max(folder)+1:]
         
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
            
        ### ASC / HEKA import ###
        if self.filename[-3:] == 'asc':
            # Import data file
            self.data=[]
            try:
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        try:
                            curline = curline.split() # split line into segments
                            float(curline[0]) # check if line contains strings or numbers
                            self.data.append(curline) # if number, add to dataframe
                        except:
                            pass # if string, skip to next line
                    fh.close()
                            
            except:
                self.labelImport.config(text="Could not import file.")
                
            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")     
            
            
            # Convert raw data to matrix
            try:           
                df = pd.DataFrame(self.data,columns=["PtIndex","Time (s)","Current (A)","Time (s)","Potential (V)"],dtype='float')
                df = df.values
                df[:,2] = df[:,2]*1E9 # A --> nA
                
                # Determine number of pts
                npts = len(df)
                conpot = np.mean(df[-20:-1,4])
                self.expiss = np.mean(df[-20:-1,2])
        
                # Create current and potential columns accordingly
                self.time = df[:,1]
                self.currents = df[:,2]
                           
                self.labelPts2.config(text=npts)
                self.ConPot2.config(text="{0:.3f}".format(conpot))
                
                if self.checkNormalizeExp.var.get() == 1:
                    self.ExpIss2.config(text="{0:.3f}".format(self.expiss))
                else:
                    pass
           
            except:
                print("Error importing data.")
            
            
        elif self.filename[-3:] == 'txt' and self.textVar.get() == "Biologic":
            # Import file
            self.data = []
            try:
                with open(self.filepath,'r') as fh:
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
            df = pd.DataFrame(self.data, columns = ["Time (s)","Current (A)"], dtype=float)
            df = df.values
            
            df[:,1] = df[:,1] * 1E9 # A --> nA
            
            # Update labels
            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")  
            
            # Reshape data
            try: 
                # Determine number of pts
                npts = len(df)
                self.expiss = np.mean(df[-20:-1,1])
        
                # Create time and current variables
                self.time = df[:,0]
                self.currents = df[:,1]
                self.labelPts2.config(text=npts)
    
                # Potential not present in this file format, configure label.
                self.ConPot2.config(text="Not available.")
                
            except:
                self.labelImport.config(text="Error importing file.")
                
        elif self.filename[-3:] == 'txt' and self.textVar.get() == "CH Instruments":
            # Import file
            self.data = []
            index = 0
            try:
                # First read to extract data
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        try: 
                            curline = curline.split(',')
                            if curline == ['Time/sec', ' Current/A\n']:
                                datastart = 1
                            if datastart == 1:
                                float(curline[0]) # check if line contains strings or numbers
                                self.data.append(curline) # if number, add to dataframe
                        except:
                            pass # if string, skip to next line
                    fh.close()
                    
                # Second read to extract constant potential
                with open(self.filepath,'r') as fh2:
                    for curline2 in fh2:
                        index = index + 1
                        if index == 10: # The scan rate info can be found in this line
                            conpot = curline2.split('=')
                            conpot = float(conpot[1].strip('\n'))
                        else:
                            pass
            except:
                self.labelImport.config(text="Could not import file.")
                
            # Process file into consistent format for ReshapeData
            df = pd.DataFrame(self.data, columns = ["Time (s)","Current (A)"], dtype=float)
            df = df.values
            
            df[:,1] = df[:,1] * 1E9 # A --> nA
            
            # Update labels
            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")  
            
            # Reshape data
            try: 
                # Determine number of pts
                npts = len(df)
                self.expiss = np.mean(df[-20:-1,1])
        
                # Create time and current variables
                self.time = df[:,0]
                self.currents = df[:,1]
                self.currents = self.currents*(-1) # polarographic --> IUPAC convention
                self.labelPts2.config(text=npts)
    
                # Potential not present in this file format, configure label.
                self.ConPot2.config(text="{0:.3f}".format(conpot))
                
            except:
                self.labelImport.config(text="Error importing file.")
                
        elif self.filename[-3:] == 'dat':
            self.data = []
            header = []
            index = 0
            
            try:
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        if curline[0] == '#':
                            curline = curline.split('\t')
                            header.append(curline)
                        else:
                            curline = curline.split(',')
                            self.data.append(curline)
                fh.close()
                
                # Determine number of channels from header line 3, use to determine number of cols needed
                nchannels =  str(header[2]).split(':')
                nchannels = int(nchannels[1].strip(" \]n'"))
                    
                # Determine experimental type from header line 2 (determines whether col 2 is a potential or a current)
                method = str(header[1])
                method = method.split(': ')    
                                     
                if nchannels == 2:         
                    df = pd.DataFrame(self.data, columns=['Time (s)','Current (A)','NA'], dtype=float)
                    del df['NA']
                    
                    # replace commas with periods so the values will be interpreted correctly
                    header[17][1] = header[17][1].replace(",",".") 
                    conpot = float(header[17][1].strip(' \n'))
                    
                elif nchannels == 3:
                    # Case 1 : Pulsed amperometry (1 WE)
                    if method[1][0:3] == 'Pul':
                        df = pd.DataFrame(self.data, columns=['Time (s)','Potential (V)','Current (A)','NA'], dtype=float)
                        # rearrange so current is in col index 1 as before
                        df = df[['Time (s)','Current (A)','Potential (V)','NA']]
                        del df['NA']
                        
                        conpot = 'Pulse sequence.'
                    # Case 2: Amperometry (2 WE)
                    else:
                        df = pd.DataFrame(self.data, columns=['Time (s)','Current1 (A)','Current2 (A)','NA'], dtype=float)
                        # rearrange so current is in col index 1 as before
                        del df['NA']    
                        
                        # replace commas with periods so the values will be interpreted correctly
                        header[19][1] = header[19][1].replace(",",".") 
                        conpot = float(header[19][1].strip(' \n'))
                        
                elif nchannels == 4:
                    df = pd.DataFrame(self.data,columns = ['Time (s)','Potential (V)','Current1 (A)','Current2 (A)','NA'], dtype=float)
                    df = df[['Time (s)','Current1 (A)','Potential (V)','Current2 (A)','NA']]
                    del df['NA']
                    
                    conpot = 'Pulse sequence.'
                        
                    
                df = df.values
                df[:,1] = df[:,1]*1E9 # A --> nA
                
                # Update labels
                self.labelImport.config(text="File imported.")
                self.buttonPlot.config(state="normal")
                self.labelPlot.config(text="")  
                
                
               # Reshape data
                try: 
                    # Determine number of pts
                    npts = len(df)
                    self.expiss = np.mean(df[-20:-1,1])
            
                    # Create time and current variables
                    self.time = df[:,0]
                    self.currents = df[:,1]
                    self.labelPts2.config(text=npts)
        
                    if type(conpot) == float:                    
                        self.ConPot2.config(text="{0:.3f}".format(conpot))
                    else:
                        self.ConPot2.config(text=conpot)
                        
                except:
                    self.labelImport.config(text="Error importing file.")
                    
            except:
                self.labelImport.config(text="Error importing file.")
        
        else:
            self.labelImport.config(text="File type not supported.")
        


    """
    Looking to extend the import file functionality to support a different file type?
    The ReshapeData function assumes the following is present after the ImportFile function has run:
        > self.time = 1D numpy array containing sampling times
        > self.currents = 1D numpy array containing currents
        > self.expiss = Experimental steady state current
        
    """

    def ReshapeData(self):
        
        # Report experimental iss if requested
        if self.checkNormalizeExp.var.get() == 1:
            self.ExpIss2.config(text="{0:.3f}".format(self.expiss))
        else:
            pass    
        
        # Calculate response time
        try:
            critvalue = abs(1.1*self.expiss)
            
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
                self.time = self.time*1E3
                self.crittime = self.crittime*1E3
            elif self.timeVar.get() == "min":
                self.time = self.time/60
                self.crittime = self.crittime/60        
                
        except:
            print("Error calculating response time.")

        # Calculate theoretical iss
        try:
            if self.checkNormalize.var.get() == 1:
                beta = 1+ (0.23/((((float(self.entryRg.get()))**3) - 0.81)**0.36))                
                self.iss = 4*1E9*96485*beta*(float(self.entryDiff.get()))*((float(self.entryRadius.get()))/1E6)*(float(self.entryConc.get()))
                self.labelTheoIssValue.config(text="{0:.3f}".format(self.iss))
            else:                
                pass           
        except:
            print("Error calculating theoretical steady state current.")
            
        # Convert current units if requested
        if self.currentVar.get() == "nA":
            pass
        elif self.currentVar.get() == "µA":
            self.currents = self.currents/1E3
            try:
                self.iss = self.iss/1E3
            except:
                pass
            try:
                self.expiss = self.expiss/1E3
            except:
                pass
        elif self.currentVar.get() == "pA":
            self.currents = self.currents*1E3
            try:
                self.iss = self.iss*1E3
            except:
                pass
            try:
                self.expiss = self.expiss*1E3
            except:
                pass

        # Update figure with CA    
        try:
            self.ax1.clear()
            
            # Query other properties of the graph to figure out if a legend label is needed
            if self.checkNormalize.var.get() == 1 or self.checkNormalizeExp.var.get() == 1 or self.checkResponsetime.var.get() == 1:
                self.img = self.ax1.plot(self.time,self.currents,label='Experimental')
            else:
                self.img = self.ax1.plot(self.time,self.currents)
            self.ax1.set_xlabel('Time ({})'.format(self.timeVar.get()))
            self.ax1.set_ylabel('Current ({})'.format(self.currentVar.get()))

            # If loop to add theoretical iss line
            if self.checkNormalize.var.get() == 1:
                self.ax1.axhline(y=self.iss,color='black',linewidth=1,linestyle='--',label='Theoretical iss')
                self.ax1.legend()
            else:
                pass
            
            # If loop to add experimental iss line
            if self.checkNormalizeExp.var.get() == 1:
                self.ax1.axhline(y=self.expiss,color='black',linewidth=1,label='Experimental iss')
                self.ax1.legend()
            else:
                pass
            
            # If loop to add response time line
            if self.checkResponsetime.var.get() == 1:
                self.ax1.axvline(x=self.crittime,color='red',linewidth=1,label='Response time')
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

            self.fig.savefig(fname= asksaveasfilename(
                    initialdir = "/",title = "Select file",
                    filetypes = (("png","*.png"),("all files","*.*"))), dpi=400)
            self.labelPlot.config(text="Figure saved.")

            
        except:
            self.labelPlot.config(text="Error saving figure to file.")

    def SaveTxt(self):
        # Prompt user to select a file name, open a text file with that name
        export = asksaveasfilename(initialdir="/",
                               filetypes =[("TXT File", "*.txt")],
                               title = "Choose a file.")
        fh = open(export + ".txt","w+")
        
        # Header lines: print details about the file and data treatment
        fh.write("Original file: {} \n".format(self.filename))
        fh.write("Units of current: {} \n".format(self.currentVar.get()))
        fh.write("Units of time: {} \n".format(self.timeVar.get()))
        
        if self.statusNormalize.get() == 1:   
            theoiss = self.iss         
            fh.write("Theoretical steady state current (nA): {0:.3f} \n".format(theoiss))
   
            if self.statusNormalizeExp.get() == 1:
                expiss = self.expiss
                fh.write("Experimental steady state current (nA): {0:.3f} \n".format(expiss))
            else:
                expiss = 'Not calculated' 
                fh.write("Experimental steady state current (nA): {} \n".format(expiss))
        else:
            theoiss = 'Not calculated'
            fh.write("Theoretical steady state current (nA): {} \n".format(theoiss))

        if self.statusResponsetime.get() == 1:
            rt = self.crittime
        else:
            pass
            
        fh.write("Response time: {0:.3f} \n".format(rt))   
        fh.write(" \n")
        
        # Print 1D array of time 
        fh.write("Time: \n")   
        np.savetxt(fh, self.time, delimiter=',', fmt='%1.4e')
        fh.write(" \n")
        
        # Print 1D array of current
        fh.write("Current: \n")   
        np.savetxt(fh, self.currents, delimiter=',', fmt='%1.4e')
        fh.write(" \n")
        
        fh.close()
        self.labelPlot.config(text="Data exported.")


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
        self.entryRadius.delete(0,"end")
        self.entryRadius.config(state="disabled")
        self.entryRg.delete(0,"end")
        self.entryRg.config(state="disabled")
        self.entryConc.delete(0,"end")
        self.entryConc.config(state="disabled")
        self.entryDiff.delete(0,"end")
        self.entryDiff.config(state="disabled")
        self.entryXmin.delete(0,"end")
        self.entryXmax.delete(0,"end")
        self.entryYmin.delete(0,"end")
        self.entryYmax.delete(0,"end")

class PACApp:    
    def __init__(self, master):                   
        # Create containers
        tabs = ttk.Notebook(master)
        frameBase = tk.Frame(tabs)
        frameAnalytics = tk.Frame(tabs)
        frameFormatting = tk.Frame(tabs)
        tabs.add(frameBase, text="  Base  ")
        tabs.add(frameAnalytics, text="  Analytics  ")
        tabs.add(frameFormatting, text="  Formatting  ")
        tabs.pack(expand=1,fill="both",side="top")
        
        framePlot = tk.Frame(master)
        framePlot.pack(side="top",pady=5)
                     
        self.frameBottom = tk.Frame(master)
        self.frameBottom.pack(side="bottom")
        
        # set min column sizes to prevent excessive resizing
        for i in range(0,8):
            frameBase.columnconfigure(i,minsize=120)
            framePlot.columnconfigure(i,minsize=110)
        
        ###### Base frame #####
        # Intro
        labelIntro = tk.Label(frameBase,text="Import experimental data to be plotted.")
        labelIntro.grid(row=0,column=0, columnspan=6, padx=20,pady=10,sticky="WS")
                
        # Select file
        self.buttonFile = tk.Button(frameBase, text="Select File",command=self.SelectFile)
        self.buttonFile.grid(row=1,column=1,sticky="W"+"E",padx=10,pady=5)
        self.labelFile = tk.Label(frameBase,text="")
        self.labelFile.grid(row=1,column=2,sticky="W")
        
        # Import file
        self.buttonImport = tk.Button(frameBase,text = "Import File",state="disabled",command=self.ImportFile)
        self.buttonImport.grid(row=2,column=1,sticky="W"+"E",padx=10)
        self.labelImport = tk.Label(frameBase,text="Select file to continue.")
        self.labelImport.grid(row=2,column=2,sticky="W")
        
        # Dropdown menu for manufacturer (needed for files of different format, same extension)
        labelText = tk.Label(frameBase,text="Manufacturer: ")
        labelText.grid(row=3,column=1,sticky="E",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.textVar = tk.StringVar(master)
        self.textVar.set('None') # set the default option
        # Dictionary with options
        textChoices = { 'Biologic','CH Instruments','HEKA','Sensolytics','PAR'}
        popupText = tk.OptionMenu(frameBase, self.textVar, *textChoices)
        popupText.configure(width=15)
        popupText.grid(row=3,column=2,sticky="W")        
#        # link function to change dropdown
        self.textVar.trace('w', self.change_dropdown)
        
        # Label for number of points in data set (before processing)
        labelNpts = tk.Label(frameBase,text="# pts (original):")
        labelNpts.grid(row=1,column=3,padx=10,sticky="E")
        self.labelNpts2 = tk.Label(frameBase,text="")
        self.labelNpts2.grid(row=1,column=4,padx=10,sticky="W")
        
        # Label for number of points in data set (after processing)
        labelNpts3 = tk.Label(frameBase,text="# pts (post-processing):")
        labelNpts3.grid(row=2,column=3,padx=10,sticky="E")
        self.labelNpts4 = tk.Label(frameBase,text="")
        self.labelNpts4.grid(row=2,column=4,padx=10,sticky="W")
        
        # Label for zero tip-substrate distance dropdown
        labelZerod = tk.Label(frameBase,text="Method of determining d = 0")
        labelZerod.grid(row=1,column=5,sticky="W",padx=10)
        
        # Dropdown menu for method of determining zero tip-substrate distance
        # Create a stringvar which will contian the eventual choice
        self.zerodVar = tk.StringVar(master)
        self.zerodVar.set('First point with data') # set the default option
        # Dictionary with options
        choices = { 'First point with data','First derivative analysis','No calibration'}
        popupMulticycle = tk.OptionMenu(frameBase, self.zerodVar, *choices)
        popupMulticycle.configure(width=20)
        popupMulticycle.grid(row=2,column=5,sticky="W",padx=10)        
        # link function to change dropdown
        self.zerodVar.trace('w', self.change_dropdown)
                
        ###### Analytics frame #####
        # Intro
        labelAnalytics = tk.Label(frameAnalytics,text="Customize the data treatment.")
        labelAnalytics.grid(row=0,column=0,padx=20,pady=10,sticky="WS")
        
        # Toggle for normalizing currents
        self.statusNormalize = tk.IntVar()
        self.checkNormalize = tk.Checkbutton(frameAnalytics, text="Normalize?", variable=self.statusNormalize, command=self.BoxesSelected)
        self.checkNormalize.var = self.statusNormalize        
        self.checkNormalize.grid(row=1,column=0,sticky="E",padx=10)
                        
        # Toggle for experimental normalization
        self.statusNormalizeExp = tk.IntVar()
        self.checkNormalizeExp = tk.Checkbutton(frameAnalytics, state="disabled",text="Experimental iss?", variable=self.statusNormalizeExp, command=self.BoxesSelected)
        self.checkNormalizeExp.var = self.statusNormalizeExp 
        self.checkNormalizeExp.grid(row=2,column=0,sticky="E",padx=10)  
                        
        # Input for accepting electrode parameters for theoretical iss
        labelRadius = tk.Label(frameAnalytics,text="Radius (µm)")
        labelRadius.grid(row=1,column=1,padx=10,sticky="W")
        self.entryRadius = tk.Entry(frameAnalytics)
        self.entryRadius.grid(row=2,column=1,padx=10,sticky="W")
        
        labelRg = tk.Label(frameAnalytics,text="Rg")
        labelRg.grid(row=1,column=2,padx=10,sticky="W")
        self.entryRg = tk.Entry(frameAnalytics)
        self.entryRg.grid(row=2,column=2,padx=10,sticky="W")
        
        labelConc = tk.Label(frameAnalytics,text="Conc. (mM)")
        labelConc.grid(row=1,column=3,padx=10,sticky="W")
        self.entryConc = tk.Entry(frameAnalytics,state="disabled")
        self.entryConc.grid(row=2,column=3,padx=10,sticky="W")
        
        labelDiff = tk.Label(frameAnalytics,text="Diff. coeff. (m^2/s)")
        labelDiff.grid(row=1,column=4,padx=10,sticky="W")
        self.entryDiff = tk.Entry(frameAnalytics,state="disabled")
        self.entryDiff.grid(row=2,column=4,padx=10,sticky="W")
        
        labelTheoIss = tk.Label(frameAnalytics,text="Theoretical iss (nA)")
        labelTheoIss.grid(row=1,column=5,padx=10,sticky="W")
        self.labelTheoIssValue = tk.Label(frameAnalytics,text="")
        self.labelTheoIssValue.grid(row=2,column=5,padx=10,sticky="W")
        
        # Input for accepting experimental iss
        labelIssExp = tk.Label(frameAnalytics,text="Expermental iss (nA)")
        labelIssExp.grid(row=1,column=6,padx=10,sticky="W")
        self.entryIssExp = tk.Entry(frameAnalytics, state="disabled")
        self.entryIssExp.grid(row=2,column =6, padx=10,sticky="W")
        
        # Labels only to be used for error reporting
        self.labelRadiusErr = tk.Label(frameAnalytics,text="")
        self.labelRadiusErr.grid(row=3,column=1,padx=10,sticky="W")
        self.labelRgErr = tk.Label(frameAnalytics,text="")
        self.labelRgErr.grid(row=3,column=2,padx=10,sticky="W")
        self.labelConcErr = tk.Label(frameAnalytics,text="")
        self.labelConcErr.grid(row=3,column=3,padx=10,sticky="W")
        self.labelDiffErr = tk.Label(frameAnalytics,text="")
        self.labelDiffErr.grid(row=3,column=4,padx=10,sticky="W")
        self.labelIssExpErr = tk.Label(frameAnalytics,text="")
        self.labelIssExpErr.grid(row=3,column=6,padx=10,sticky="W")
        
        # Toggle for fitting Rg
        self.statusFitRg = tk.IntVar()
        self.checkFitRg = tk.Checkbutton(frameAnalytics, text="Fit Rg?", variable=self.statusFitRg, command=self.BoxesSelected)
        self.checkFitRg.var = self.statusFitRg     
        self.checkFitRg.grid(row=4,column=1,rowspan=2,sticky="E",padx=10)
        
        labelEstRg = tk.Label(frameAnalytics, text = "Estimated Rg")
        labelEstRg.grid(row=4,column=2,padx=10,sticky="W")
        self.labelEstRg2 = tk.Label(frameAnalytics, text="")
        self.labelEstRg2.grid(row=5,column=2,padx=10,sticky="W")
        
        # Toggle for fitting kappa
        self.statusFitKappa = tk.IntVar()
        self.checkFitKappa = tk.Checkbutton(frameAnalytics, text="Fit kappa?", variable=self.statusFitKappa, command=self.BoxesSelected)
        self.checkFitKappa.var = self.statusFitKappa     
        self.checkFitKappa.grid(row=4,column=3,rowspan=2,sticky="E",padx=10)
        
        labelEstKappa = tk.Label(frameAnalytics, text = "Estimated kappa")
        labelEstKappa.grid(row=4,column=4,padx=10,sticky="W")
        self.labelEstKappa2 = tk.Label(frameAnalytics, text="")
        self.labelEstKappa2.grid(row=5,column=4,padx=10,sticky="W")
        
        labelEstK = tk.Label(frameAnalytics, text = "Estimated k (cm/s)")
        labelEstK.grid(row=4,column=5,padx=10,sticky="W")
        self.labelEstK2 = tk.Label(frameAnalytics, text="")
        self.labelEstK2.grid(row=5,column=5,padx=10,sticky="W")
        
        ####### Formatting tab ##########
        # Intro
        labelFormatting = tk.Label(frameFormatting,text="Customize the formatting of the graph.")
        labelFormatting.grid(row=0,column=0,padx=20,pady=5,columnspan=3,sticky="W")
        
        # Toggle for displaying pure feedback lines
        self.statusFeedback = tk.IntVar()
        self.checkFeedback = tk.Checkbutton(frameFormatting, text="Show pure feedback cases?", variable=self.statusFeedback)
        self.checkFeedback.var = self.statusFeedback        
        self.checkFeedback.grid(row=1,column=1,sticky="E",padx=10)
        
        # Dropdown menu for units on distance
        # Label for dropdown menu
        labelDistance = tk.Label(frameFormatting,text="Units (Distance)")
        labelDistance.grid(row=1,column=2,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.distanceVar = tk.StringVar(master)
        self.distanceVar.set('µm') # set the default option
        # Dictionary with options
        distanceChoices = {'mm','µm','nm'}
        popupDistances = tk.OptionMenu(frameFormatting, self.distanceVar, *distanceChoices)
        popupDistances.configure(width=10)
        popupDistances.grid(row=2,column=2,sticky="W",padx=10)        
#        # link function to change dropdown
        self.distanceVar.trace('w', self.change_dropdown)
        
        # Dropdown menu for units on current
        # Label for dropdown menu
        labelCurrent = tk.Label(frameFormatting,text="Units (Current)")
        labelCurrent.grid(row=1,column=3,sticky="W",padx=10)
        # Create a stringvar which will contian the eventual choice
        self.currentVar = tk.StringVar(master)
        self.currentVar.set('nA') # set the default option
        # Dictionary with options
        currentChoices = {'µA','nA','pA'}
        popupCurrent = tk.OptionMenu(frameFormatting, self.currentVar, *currentChoices)
        popupCurrent.configure(width=10)
        popupCurrent.grid(row=2,column=3,sticky="W",padx=10)        
#        # link function to change dropdown
        self.currentVar.trace('w', self.change_dropdown)
        
        # Entry fields for controlling axis limits on plot
        labelXmin = tk.Label(frameFormatting,text="Xmin")
        labelXmin.grid(row=1,column=4,sticky="W",padx=10)
        self.entryXmin = tk.Entry(frameFormatting)
        self.entryXmin.grid(row=2,column=4,sticky="W",padx=10)
        
        labelXmax = tk.Label(frameFormatting,text="Xmax")
        labelXmax.grid(row=3,column=4,sticky="W",padx=10)
        self.entryXmax = tk.Entry(frameFormatting)
        self.entryXmax.grid(row=4,column=4,sticky="W",padx=10)
        
        labelXmin2 = tk.Label(frameFormatting,text="Xmin (norm.)")
        labelXmin2.grid(row=1,column=5,sticky="W",padx=10)
        self.labelXmin3 = tk.Label(frameFormatting,text="")
        self.labelXmin3.grid(row=2,column=5,sticky="W",padx=10)
        
        labelXmax2 = tk.Label(frameFormatting,text="Xmax (norm.)")
        labelXmax2.grid(row=3,column=5,sticky="W",padx=10)
        self.labelXmax3 = tk.Label(frameFormatting,text="")
        self.labelXmax3.grid(row=4,column=5,sticky="W",padx=10)
        
        labelYmin = tk.Label(frameFormatting,text="Ymin")
        labelYmin.grid(row=1,column=6,sticky="W",padx=10)
        self.entryYmin = tk.Entry(frameFormatting)
        self.entryYmin.grid(row=2,column=6,sticky="W",padx=10)
        
        labelYmax = tk.Label(frameFormatting,text="Ymax ")
        labelYmax.grid(row=3,column=6,sticky="W",padx=10)
        self.entryYmax = tk.Entry(frameFormatting)
        self.entryYmax.grid(row=4,column=6,sticky="W",padx=10)
        
        labelYmin2 = tk.Label(frameFormatting,text="Ymin (norm.)")
        labelYmin2.grid(row=1,column=7,sticky="W",padx=10)
        self.labelYmin3 = tk.Label(frameFormatting,text="")
        self.labelYmin3.grid(row=2,column=7,sticky="W",padx=10)
        
        labelYmax2 = tk.Label(frameFormatting,text="Ymax (norm.)")
        labelYmax2.grid(row=3,column=7,sticky="W",padx=10)
        self.labelYmax3 = tk.Label(frameFormatting,text="")
        self.labelYmax3.grid(row=4,column=7,sticky="W",padx=10)
        
        # Data cursor setup        
        labelCursor = tk.Label(frameFormatting,text="Data Cursor")
        labelCursor.grid(row=1,column=8,sticky="W",padx=10)
        self.labelXCursor = tk.Label(frameFormatting,text="X : ")
        self.labelXCursor.grid(row=2,column=8,sticky="W",padx=10)
        self.labelYCursor = tk.Label(frameFormatting,text="Y : ")
        self.labelYCursor.grid(row=3,column=8,sticky="W",padx=10)
        
        
        ###### Plot control ###########
        # Button for generating plot
        self.buttonPlot = tk.Button(framePlot,text="Plot Data",state="disabled",command=self.ReshapeData)
        self.buttonPlot.grid(row=0,column=1,rowspan=2,sticky="W"+"E")
        self.labelPlot = tk.Label(framePlot,text="Import data to begin.")
        self.labelPlot.grid(row=0,column=2,rowspan=2,sticky="W",padx=10)
        
        # Button for saving the plot
        self.buttonSave = tk.Button(framePlot,text="Save Figure",state="disabled",command=self.SaveFig)
        self.buttonSave.grid(row=0,column=3,rowspan=2,sticky="W"+"E",padx=10)
        
        # Label for what portion to save
        labelSave = tk.Label(framePlot,text="Region to save: ")
        labelSave.grid(row=0,column=4,rowspan=3,sticky="E",padx=10)
        
        # Dropdown menu for what portion of graph to save
        # Create a stringvar which will contian the eventual choice
        self.figsaveVar = tk.StringVar(master)
        self.figsaveVar.set('Normalized PAC') # set the default option
        # Dictionary with options
        choices = { 'Normalized PAC','Non-normalized PAC','Both'}
        popupSave = tk.OptionMenu(framePlot, self.figsaveVar, *choices)
        popupSave.configure(width=20)
        popupSave.grid(row=0,column=5,sticky="W",padx=10)        
        # link function to change dropdown
        self.figsaveVar.trace('w', self.change_dropdown)
        
        # Button for exporting to text file
        self.buttonExport = tk.Button(framePlot,text="Export Data", state="disabled", command=self.SaveTxt)
        self.buttonExport.grid(row=0,column=6, sticky="W"+"E",padx=10)
                
        # Button for resetting window
        self.buttonReset = tk.Button(framePlot,text="Reset Window",command=self.ResetWindow)
        self.buttonReset.grid(row=0,column=7,padx=20,pady=10,sticky="W"+"E")
               
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
        self.canvas.get_tk_widget().grid(row=1,column=0,sticky="S")
        self.canvas.mpl_connect('button_press_event',DataCursor)
        self.canvas.draw()   

    def change_dropdown(*args):
        pass
    
    def SelectFile(self):
        self.filepath = askopenfilename(initialdir="/",
                               title = "Choose a file.")
        folder = []
        
        #check for folder symbols in filepath
        for c in self.filepath:
            folder.append(c == '/')
        folder = [i for i, j in enumerate(folder) if j == True]
        # trim off folder path to retrieve just filename
        self.filename = self.filepath[max(folder)+1:]
         
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
        else:
            pass
           
    def ImportFile(self):
        ## Check if manufacturer needed
        if self.filename[-3:] == 'txt' and self.textVar.get() == 'None':
            self.labelImport.config(text="Specify a manufacturer.")
        
        ### ASC / HEKA import ###
        elif self.filename[-3:] == 'asc':
            # Import data file
            self.data=[]
            try:
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        try:
                            curline = curline.split() # split line into segments
                            float(curline[0]) # check if line contains strings or numbers
                            self.data.append(curline) # if number, add to dataframe
                        except:
                            pass # if string, skip to next line
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
                    df = pd.DataFrame(self.data,columns=["PtIndex","Distance (m)","Current (A)","Distance (m)","Current (A)"],dtype=float)
                elif ncols == 3:
                    df = pd.DataFrame(self.data,columns=["PtIndex","Distance (m)","Current (A)"], dtype=float )
                
                df = df.values
                try:
                    df[:,1] = df[:,1]*1E6 # m --> um
                    df[:,2] = df[:,2]*1E9 # A --> nA
                    df[:,4] = df[:,4]*1E9 # A --> nA
                except:
                    pass
                
                # Determine number of pts
                nptsorig = len(df)
    
                # Create distance and current variables
                self.distances0 = df[:,1]
                self.currents0 = df[:,2]
                           
                self.labelNpts2.config(text=nptsorig)
            except:
                print("Error importing data.")
                
        ### MAT / HEKA import ###
        elif self.filename[-3:] == 'mat':
            
            self.zerodVar.set('First point with data')
            
            try: 
                matdata = scipy.io.loadmat(self.filepath)
                
                # Delete non-data containing variables
                del matdata['__header__']
                del matdata['__globals__']
                del matdata['__version__']
                
                for entry in matdata:
                    trace = matdata[entry]
                    self.distances0 = trace[:,0]
                    self.currents0 = trace[:,1]
                    
                self.distances0 = self.distances0*1E6 # m --> um
                self.currents0 = self.currents0*1E9 # A --> nA
                
                nptsorig = len(self.distances0)
                self.labelNpts2.config(text=nptsorig)
                
                self.labelImport.config(text="File imported.")
                self.buttonPlot.config(state="normal")
                self.labelPlot.config(text="")  
                          
            except:
                self.labelImport.config(text="Error importing file.")
            
        ### TXT / Biologic import ###
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'Biologic':
            
            self.zerodVar.set('No calibration')
            
            # Import file
            self.data = []
            try:
                with open(self.filepath,'r') as fh:
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
            df = pd.DataFrame(self.data, columns = ["Time (s)","Current (A)"], dtype=float)
            df = df.values
            
            df[:,1] = df[:,1] * 1E9 # A --> nA
            
            # Update labels
            self.labelImport.config(text="File imported.")
            self.buttonPlot.config(state="normal")
            self.labelPlot.config(text="")  
            
            
            # Convert raw data to matrix
            try:           
                df = pd.DataFrame(self.data,columns=["Distance (µm)","Current (A)"],dtype='float')
                df = df.values
                df[:,1] = df[:,1]*1E9 # A --> nA
                
                # Determine number of pts
                nptsorig = len(df)
    
                # Create distance and current variables
                self.distances0 = df[:,0]
                self.distances0 = self.distances0 - np.amin(self.distances0)
                self.currents0 = df[:,1]
                           
                self.labelNpts2.config(text=nptsorig)
            except:
                print("Error importing data.")
                
        ### TXT / CH Instruments import ###
        elif self.filename[-3:] == 'txt' and self.textVar.get() == 'CH Instruments':
            try:
                self.data = []
                datastart = 0 # toggle for determining if reading point cloud
                index = 0
                
                # First read to extract data
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        try: 
                            curline = curline.split(',')
                            if curline == ['Distance/um', ' Current/A\n']:
                                datastart = 1
                            if datastart == 1:
                                float(curline[0]) # check if line contains strings or numbers
                                self.data.append(curline) # if number, add to dataframe
                        except:
                            pass # if string, skip to next line
                    fh.close()
                                                    
                # Second read to extract constant potential
                with open(self.filepath,'r') as fh2:
                    for curline2 in fh2:
                        index = index + 1
                        if index == 9: # The scan rate info can be found in this line
                            conpot = curline2.split('=')
                            conpot = float(conpot[1].strip('\n'))
                        else:
                            pass
                        
                self.labelImport.config(text="File imported.")
                self.buttonPlot.config(state="normal")
                self.labelPlot.config(text="")  
                        
                # Convert raw data to matrix
                try:           
                    df = pd.DataFrame(self.data,columns=["Distance (µm)","Current (A)"],dtype='float')
                    df = df.values
                    df[:,1] = df[:,1]*1E9 # A --> nA
                    
                    # Determine number of pts
                    nptsorig = len(df)
        
                    # Create distance and current variables
                    self.distances0 = df[:,0]
                    self.distances0 = np.amax(self.distances0) - self.distances0
                    self.currents0 = df[:,1]
                    self.currents0 = self.currents0*(-1) # polarographic --> IUPAC convention

                               
                    self.labelNpts2.config(text=nptsorig)
                    
                except:
                    self.labelImport.config(text="Error importing file.")
            except:
                self.labelImport.config(text="Error importing file.")
                
        ### DAT / Sensolytics import ###
        elif self.filename[-3:] == 'dat':
            try:
                self.data = []
                header = []
                index = 0
                
                with open(self.filepath,'r') as fh:
                    for curline in fh: 
                        index = index + 1
                        if index <=15:
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
                    
                df = pd.DataFrame(self.data, columns=['Distance (um)','Index','Current (nA)','NA'], dtype=float)
                del df['NA']
                df = df.values
                
                nptsorig = len(df)

                self.distances0 = df[:,0]
                self.currents0 = df[:,2]  
                
                self.labelNpts2.config(text=nptsorig)
                    
            except:
                self.labelImport.config(text="Error importing file.")
                
                
        ### CSV / PAR import ###
        elif self.filename[-3:] == 'csv':
            try:
                with open(self.filepath) as fh:
                    data = pd.read_csv(fh,header=3)
                    fh.close()
                
                data = data.values
                self.distances0 = data[:,1]*1E3 # mm --> um
                self.distances0 = np.amax(self.distances0) - self.distances0
                self.currents0 = data[:,2]*1E3 # uA --> nA

                self.labelImport.config(text="File imported.")
                self.buttonPlot.config(state="normal")
                self.labelPlot.config(text="")  
                
                nptsorig = len(self.distances0)
                self.labelNpts2.config(text=nptsorig)
                    
            except:
                self.labelImport.config(text="Error importing file.")
                
        else:
            self.labelImport.config(text="File type not supported.")
            
    """
    Looking to extend the import file functionality to support a different file type?
    The ReshapeData function assumes the following is present after the ImportFile function has run:
        > self.distances = 1D numpy array containing distances (in µm)
        >>> These are assumed to be positive values in order of increasing d.
        > self.currents = 1D numpy array containing currents (in nA) 
    """
            
    def ReshapeData(self):
        self.distances = self.distances0.copy()
        self.currents = self.currents0.copy()

        ## Calculate zero tip substrate distance
        # Strip off any NaN points, make first point containing a current value the new zero
        critrow = np.amin(np.where(np.isnan(self.currents) == False))
        self.distances = self.distances[critrow:]
        self.currents = self.currents[critrow:]
        
        if self.zerodVar.get() != 'No calibration':
            self.distances = self.distances - np.amin(self.distances) # correct to min
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
                self.distancesnorm = self.distances/(float(self.entryRadius.get()))
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
            self.distances = self.distances/1E3
        elif self.distanceVar.get() == "nm":
            self.distances = self.distances*1E3

        # Calculate theoretical steady state value
        try:
            if self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 0:
                beta = 1+ (0.23/((((float(self.entryRg.get()))**3) - 0.81)**0.36))                
                self.issTheo = 4*1E9*96485*beta*(float(self.entryDiff.get()))*((float(self.entryRadius.get()))/1E6)*(float(self.entryConc.get()))
                self.labelTheoIssValue.config(text="{0:.3f}".format(self.issTheo))
            else:                
                pass           
        except:
            print("Error calculating theoretical steady state current.")         
            
        # Normalize currents
        if self.checkNormalize.var.get() == 1 and self.checkNormalizeExp.var.get() == 0:
            try:
                self.currentsnorm = self.currents/self.issTheo
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
                self.currentsnorm = self.currents/(float(self.entryIssExp.get()))
            except:
                self.labelRadiusErr.config(text="Enter a value.")
        else:
            pass
        
        # Update current units if needed
        if self.currentVar.get() == "nA":
            pass
        elif self.currentVar.get() == "µA":
            self.currents = self.currents/1E3
        elif self.currentVar.get() == "pA":
            self.currents = self.currents*1E3
                   
        # Update figure with PAC pre-treatment
        try:
            self.ax1.clear()
            self.img = self.ax1.plot(self.distances,self.currents)
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
                self.estRg = scipy.optimize.curve_fit(self.negfbfit, self.distancesnorm, self.currentsnorm)
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
                self.estKappa = scipy.optimize.curve_fit(self.kappafit, self.distancesnorm, self.currentsnorm)
                self.estKappa = float(self.estKappa[0])
                self.labelEstKappa2.config(text="{0:.3f}".format(self.estKappa))
            except:
                self.labelEstKappa2.config(text="Err")
                
            try:
                self.estK = (1E8 *self.estKappa * float(self.entryDiff.get()))/ (float(self.entryRadius.get()))
                self.labelEstK2.config(text="{0:.3f}".format(self.estK))
            except:
                self.labelDiffErr.config(text = "Enter a value.")
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
                    self.ax2.plot(self.distancesnorm,self.currentsnorm,label='Experimental')
                    self.ax2.plot(self.distancesnorm,self.theonegfb,color='red',label='Negative feedback')
                    self.ax2.plot(self.distancesnorm,self.theoposfb,color='green',label='Positive feedback')
                    self.ax2.legend()
                    self.ax2.set_xlabel('Normalized distance')
                    self.ax2.set_ylabel('Normalized current')
                    self.ax2.set_ylim([0,3])
                else:
                    self.ax2.plot(self.distancesnorm,self.currentsnorm)
                    self.ax2.set_xlabel('Normalized distance')
                    self.ax2.set_ylabel('Normalized current')
                    
                # Check if the fit line should be plotted as well
                if self.checkFitKappa.var.get() == 1:
                    self.ax2.plot(self.distancesnorm, self.theokappatheo, label='Fit curve')
                    self.ax2.legend()
                    self.ax2.set_xlabel('Normalized distance')
                    self.ax2.set_ylabel('Normalized current')
                    self.ax2.set_ylim([0,3])
                    
                    
                # Set X/Y limits on normalized axes, update labels
                try:
                    xmin_norm = float(self.entryXmin.get())/float(self.entryRadius.get())
                    xmax_norm = float(self.entryXmax.get())/float(self.entryRadius.get())
                    self.ax2.set_xlim([xmin_norm,xmax_norm])
                    self.labelXmin3.config(text="{0:.2f}".format(xmin_norm))
                    self.labelXmax3.config(text="{0:.2f}".format(xmax_norm))
                except:
                    pass
                try:
                    ymin_norm = float(self.entryYmin.get())/float(self.entryRadius.get())
                    ymax_norm = float(self.entryYmin.get())/float(self.entryRadius.get())
                    self.labelYmin3.config(text="{0:.2f}".format(ymin_norm))
                    self.labelYmax3.config(text="{0:.2f}".format(ymax_norm))
                    self.ax2.set_ylim([ymin_norm,ymax_norm])                
                except:
                    pass
            else:
                pass        
        except:
            print("Data imported, call 2 to update canvas PAC failed.")
            
        self.canvas.draw()         
        self.buttonSave.config(state="normal")
        self.buttonExport.config(state="normal")
               
    def negfbfit(self, distancesnorm, Rg):       
        Lvalues = self.distancesnorm
        
        # Build up the analytical approximation
        currentsins_pt1 = ((2.08/(Rg**0.358))*(Lvalues - (0.145/Rg))) + 1.585
        currentsins_pt2 = (2.08/(Rg**0.358)*(Lvalues + (0.0023*Rg))) + 1.57
        currentsins_pt3 = (np.log(Rg)/Lvalues) + (2/(np.pi*Rg)*(np.log(1+(np.pi*Rg)/(2*Lvalues))))
        currentsins = currentsins_pt1/(currentsins_pt2 + currentsins_pt3)
        
        return currentsins
    
    def kappafit(self, distancesnorm, kappa):       
        Lvalues = self.distancesnorm
        Rg = float(self.entryRg.get())        
        
        # negfb
        currentsins_pt1 = ((2.08/(Rg**0.358))*(Lvalues - (0.145/Rg))) + 1.585
        currentsins_pt2 = (2.08/(Rg**0.358)*(Lvalues + (0.0023*Rg))) + 1.57
        currentsins_pt3 = (np.log(Rg)/Lvalues) + (2/(np.pi*Rg)*(np.log(1+(np.pi*Rg)/(2*Lvalues))))
        currentsins = currentsins_pt1/(currentsins_pt2 + currentsins_pt3)
        
        # positive fb
        alpha = np.log(2) + np.log(2)*(1 - (2/np.pi)*np.arccos(1/Rg)) - np.log(2)*(1 - ((2/np.pi)*np.arccos(1/Rg))**2);
        beta = 1 + 0.639*(1 - (2/np.pi)*np.arccos(1/Rg)) - 0.186*(1 - ((2/np.pi)*np.arccos(1/Rg))**2);
        currentsmixed_pt0 = alpha + (1/beta)*(np.pi/(4*np.arctan(Lvalues + (1/kappa)))) + (1 - alpha - (0.5/beta))*(2/np.pi)*np.arctan(Lvalues + (1/kappa));
        
        # Merge neg/posfb expressions into analytical approx.
        currentsmixed_pt1 = currentsins - 1
        currentsmixed_pt2 = 1 + (2.47*Lvalues*kappa)*(Rg**0.31)
        currentsmixed_pt3 = 1 + (Lvalues**((0.006*Rg +0.113)))*(kappa**((-0.0236*Rg +0.91)))

        currentsmixed = currentsmixed_pt0 + ((currentsmixed_pt1)/(currentsmixed_pt2 * currentsmixed_pt3))

        return currentsmixed
        
    def negfb(self):       
        if self.checkFitRg.var.get() == 1:
            Rg = self.estRg
        else:
            Rg = float(self.entryRg.get())        
        
        Lvalues = self.distancesnorm
        
        # Build up the analytical approximation
        currentsins_pt1 = ((2.08/(Rg**0.358))*(Lvalues - (0.145/Rg))) + 1.585
        currentsins_pt2 = (2.08/(Rg**0.358)*(Lvalues + (0.0023*Rg))) + 1.57
        currentsins_pt3 = (np.log(Rg)/Lvalues) + (2/(np.pi*Rg)*(np.log(1+(np.pi*Rg)/(2*Lvalues))))
        currentsins = currentsins_pt1/(currentsins_pt2 + currentsins_pt3)
        
        return currentsins
    
    def kappa(self):       
        Lvalues = self.distancesnorm
        Rg = float(self.entryRg.get())  
        kappa = self.estKappa
        
        # negfb
        currentsins_pt1 = ((2.08/(Rg**0.358))*(Lvalues - (0.145/Rg))) + 1.585
        currentsins_pt2 = (2.08/(Rg**0.358)*(Lvalues + (0.0023*Rg))) + 1.57
        currentsins_pt3 = (np.log(Rg)/Lvalues) + (2/(np.pi*Rg)*(np.log(1+(np.pi*Rg)/(2*Lvalues))))
        currentsins = currentsins_pt1/(currentsins_pt2 + currentsins_pt3)
        
        # positive fb
        alpha = np.log(2) + np.log(2)*(1 - (2/np.pi)*np.arccos(1/Rg)) - np.log(2)*(1 - ((2/np.pi)*np.arccos(1/Rg))**2);
        beta = 1 + 0.639*(1 - (2/np.pi)*np.arccos(1/Rg)) - 0.186*(1 - ((2/np.pi)*np.arccos(1/Rg))**2);
        currentsmixed_pt0 = alpha + (1/beta)*(np.pi/(4*np.arctan(Lvalues + (1/kappa)))) + (1 - alpha - (0.5/beta))*(2/np.pi)*np.arctan(Lvalues + (1/kappa));
        
        # Merge neg/posfb expressions into analytical approx.
        currentsmixed_pt1 = currentsins - 1
        currentsmixed_pt2 = 1 + (2.47*Lvalues*kappa)*(Rg**0.31)
        currentsmixed_pt3 = 1 + (Lvalues**((0.006*Rg +0.113)))*(kappa**((-0.0236*Rg +0.91)))

        currentsmixed = currentsmixed_pt0 + ((currentsmixed_pt1)/(currentsmixed_pt2 * currentsmixed_pt3))

        return currentsmixed
      
    def posfb(self):
        if self.checkFitRg.var.get() == 1:
            Rg = self.estRg
        else:
            Rg = float(self.entryRg.get())     
        
        Lvalues = self.distancesnorm
    
        # Build up the analytical approximation
        alpha = np.log(2) + np.log(2)*(1 - (2/np.pi)*np.arccos(1/Rg)) - np.log(2)*(1 - ((2/np.pi)*np.arccos(1/Rg))**2);
        beta = 1 + 0.639*(1 - (2/np.pi)*np.arccos(1/Rg)) - 0.186*(1 - ((2/np.pi)*np.arccos(1/Rg))**2);
        currentscond = alpha + (1/beta)*(np.pi/(4*np.arctan(Lvalues))) + (1 - alpha - (0.5/beta))*(2/np.pi)*np.arctan(Lvalues);
        
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

    def SaveFig(self):
        try:
            print("Save requested.")
            
            # Save full image
            if self.figsaveVar.get() == "Both":     
                self.fig.savefig(fname= asksaveasfilename(
                        initialdir = "/",title = "Select file",
                        filetypes = (("png","*.png"),("all files","*.*"))), dpi=400)
                self.labelPlot.config(text="Figure saved.")
                
            # Save left image only
            elif self.figsaveVar.get() == "Non-normalized PAC":
                # Determine dimensions of first subplot
                extent = self.ax1.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
                
                # Save the figure, expand the extent by 50% in x and 20% in y to include axis labels and colorbar
                self.fig.savefig(fname= asksaveasfilename(
                        initialdir = "/",title = "Select file",
                        filetypes = (("png","*.png"),("all files","*.*"))),
                        bbox_inches=extent.expanded(1.5,1.3), dpi=400)
                self.labelPlot.config(text="Figure saved.")
                
            # Save right image only
            else:
                # Determine dimensions of second subplot
                extent = self.ax2.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
                
                # Save the figure, expand the extent by 50% in x and 20% in y to include axis labels and colorbar
                self.fig.savefig(fname= asksaveasfilename(
                        initialdir = "/",title = "Select file",
                        filetypes = (("png","*.png"),("all files","*.*"))),
                        bbox_inches=extent.expanded(1.5,1.3), dpi=400)
                self.labelPlot.config(text="Figure saved.")                
            
        except:
            self.labelPlot.config(text="Error saving figure to file.")
        
    def SaveTxt(self):
        # Prompt user to select a file name, open a text file with that name
        export = asksaveasfilename(initialdir="/",
                               filetypes =[("TXT File", "*.txt")],
                               title = "Choose a file.")
        fh = open(export + ".txt","w+")
        
        # Header lines: print details about the file and data treatment
        fh.write("Original file: {} \n".format(self.filename))
        fh.write("Units of current: {} \n".format(self.currentVar.get()))
        fh.write("Units of distance: {} \n".format(self.distanceVar.get()))
        
        # Report theoretical and experimental steady state currents
        if self.statusNormalize.get() == 1:   
            if self.statusNormalizeExp.get() == 1:
                expiss = float(self.entryIssExp.get())
                fh.write("Experimental steady state current (nA): {0:.3f} \n".format(expiss))
            else:
                theoiss = self.issTheo         
                fh.write("Theoretical steady state current (nA): {0:.3f} \n".format(theoiss))
                
                expiss = 'Not calculated' 
                fh.write("Experimental steady state current (nA): {} \n".format(expiss))
        else:
            theoiss = 'Not calculated'
            fh.write("Theoretical steady state current (nA): {} \n".format(theoiss))

        # Report Rg
        if self.statusFitRg.get() == 1:
            fh.write("Rg (fit): {0:.1f} \n".format(self.estRg))
        else:
            try:
                inputRg = float(self.entryRg.get())
                fh.write("Rg (input): {0:.1f} \n".format(inputRg))
            except:
                fh.write("Rg: Not available \n")
                
        # Report kappa
        if self.statusFitKappa.get() == 1:
            fh.write("kappa (fit): {0:.1f} \n".format(self.estKappa))
            try:
                fh.write("k (cm/s): {0:.3f} \n".format(self.estK))
            except:
                pass
        else:
            fh.write("kappa (fit): Not calculate \n")
            fh.write("k (cm/s): Not calculated \n") 
            
        # Insert blank line between header and data
        fh.write(" \n")
                    
        # Print 1D array of distance
        fh.write("Tip-substrate distance: \n")   
        np.savetxt(fh, self.distances, delimiter=',', fmt='%1.4e')
        fh.write(" \n")
        
        # Print 1D array of current
        fh.write("Current: \n")   
        np.savetxt(fh, self.currents, delimiter=',', fmt='%1.4e')
        fh.write(" \n")
        
        # Print normalized quantities, if applicable
        if self.statusNormalize.get() == 1:
            
            # Normalized distance
            fh.write("Normalized tip-substrate distance: \n")   
            np.savetxt(fh, self.distancesnorm, delimiter=',', fmt='%1.4e')
            fh.write(" \n")
            
            # Normalized current
            fh.write("Normalized current: \n")   
            np.savetxt(fh, self.currentsnorm, delimiter=',', fmt='%1.4e')
            fh.write(" \n")
            
        else:
            fh.write(" \n")
            
        # Print mixed feedback line for est kappa, if applicable
        if self.statusFitKappa.get() == 1:
            fh.write("Theoretical line for estimated kappa: \n")   
            np.savetxt(fh, self.theokappatheo, delimiter=',', fmt='%1.4e')
            fh.write(" \n")      
        else:
            fh.write(" \n")
            
        # Print pure feedback lines, if applicable
        if self.statusFeedback.get() == 1:
            
            # Positive feedback
            fh.write("Theoretical positive feedback: \n")   
            np.savetxt(fh, self.theoposfb, delimiter=',', fmt='%1.4e')
            fh.write(" \n")    
            
            # Negative feedback
            fh.write("Theoretical negative feedback: \n")   
            np.savetxt(fh, self.theonegfb, delimiter=',', fmt='%1.4e')
            fh.write(" \n")    
        else:
            fh.write(" \n")
            
            
        fh.close()
        self.labelPlot.config(text="Data exported.")
    

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
        self.entryIssExp.delete(0,"end")
        self.entryIssExp.config(state="disabled")
        self.entryRadius.delete(0,"end")
        self.entryRg.delete(0,"end")
        self.entryRg.config(state="disabled")
        self.entryConc.delete(0,"end")
        self.entryConc.config(state="disabled")
        self.entryDiff.delete(0,"end")
        self.entryDiff.config(state="disabled")
        self.entryXmin.delete(0,"end")
        self.entryXmax.delete(0,"end")
        self.entryYmin.delete(0,"end")
        self.entryYmax.delete(0,"end")

class MenuPages:       
    def TheoryPage():       
        windowTheory = tk.Toplevel(root)
        windowTheory.title('Flux') # window title
        windowTheory.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameTheory = tk.Frame(windowTheory)
        frameTheory.configure(background="white",height=root.winfo_rootx())
        frameTheory.pack(side="top")  
        
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarTheory = tk.Scrollbar(frameTheory)
        scrollbarTheory.pack(side="right",fill="y")
      
        textTheory = tk.Text(frameTheory, height=30,width=40, yscrollcommand=scrollbarTheory.set,borderwidth=0,background="white",font='Arial 10')

        # Import external files/images which contain the contents of the help page
        try:
            # Part 0A: General description of experiment
            with open('supporting/text_Image_general.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            # Part 1B: Normalization - equation
            imageIss=tk.PhotoImage(file="supporting/eqn_steadystate.gif")
            textTheory.image_create("end",image=imageIss)
            textTheory.insert("end","\n")

            
            # Part 1A: Normalization - text
            with open('supporting/text_Image_normalization.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            # Part 1B: Normalization - equation
            imageIss=tk.PhotoImage(file="supporting/eqn_steadystate.gif")
            textTheory.image_create("end",image=imageIss)
            textTheory.insert("end","\n")

            # Part 2A: Beta - text
            with open('supporting/text_Image_beta.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            # Part 2B: Beta - equation
            imageBeta=tk.PhotoImage(file="supporting/eqn_beta.gif")
            textTheory.image_create("end",image=imageBeta)
            textTheory.insert("end","\n")
            
            # Part 3A: Edge detection - text
            with open('supporting/text_Image_edge.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()

        except:
            print("Error importing help text.") 
            
        textTheory.config(padx=20,pady=20,wrap="word")       
        textTheory.pack()
        scrollbarTheory.config(command=textTheory.yview)
        
        windowTheory.mainloop()
        
    def GuidePage():        
        windowGuide = tk.Toplevel(root)
        windowGuide.title('Flux') # window title
        windowGuide.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameGuide = tk.Frame(windowGuide)
        frameGuide.configure(background="white",height=root.winfo_rootx())
        frameGuide.pack(side="top")  
        
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarGuide = tk.Scrollbar(frameGuide)
        scrollbarGuide.pack(side="right",fill="y")
#        
        textGuide = tk.Text(frameGuide, height=30,width=40, yscrollcommand=scrollbarGuide.set,borderwidth=0,background="white",font='Arial 10')

        # Import external files/images which contain the contents of the page
        try:
            with open('supporting/text_Image_guide.txt','r') as fh:
                for line in fh:
                    textBlockGuide = fh.readline()
                    textGuide.insert("end",textBlockGuide)
                    textGuide.insert("end","\n")
            fh.close()

        except:
            print("Error importing help text.") 
            
        textGuide.config(padx=20,pady=20,wrap="word")       
        textGuide.pack()
        scrollbarGuide.config(command=textGuide.yview)
        
        windowGuide.mainloop()
        
    def AboutPage():
        windowAbout = tk.Toplevel(root)
        windowAbout.title('Flux')
        windowAbout.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameLogo = tk.Frame(windowAbout)
        frameLogo.pack(side="left")
        frameAbout = tk.Frame(windowAbout)
        frameAbout.pack(side="right")

        imageLogo = tk.PhotoImage(file="supporting/flux_logo_large.gif")
        labelLogo = tk.Label(frameLogo,image=imageLogo)
        labelLogo.grid(row=0,column=0,padx=30,pady=30)
        
        labelAbout = tk.Label(frameAbout,text="Flux v1.0", font=36)
        labelAbout.grid(row=0,column=0, sticky="W"+"N",pady=10)
        labelAbout = tk.Label(frameAbout,text="GUI for treating SECM data\n Licensed under GNU GPL v3")
        labelAbout.grid(row=1,column=0, sticky="W"+"N",padx=10)
        
        windowAbout.mainloop()
     
class MenuPagesCV:
    def __init__(self,master):
        pass
        
    def TheoryPage():
        windowTheory = tk.Toplevel(CVroot)
        windowTheory.title('Flux') # window title
        windowTheory.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameTheory = tk.Frame(windowTheory)
        frameTheory.configure(background="white")
        frameTheory.pack(side="top")  
        
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarTheory = tk.Scrollbar(frameTheory)
        scrollbarTheory.pack(side="right",fill="y")

        textTheory = tk.Text(frameTheory, height=30,width=40, yscrollcommand=scrollbarTheory.set,borderwidth=0,background="white",font='Arial 10')

        # Import external files/images which contain the contents of the help page
        try:
            # Part 0A: Normalization - text
            with open('supporting/text_CV_general.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            # Part 1B: Normalization - equation
            imageIss=tk.PhotoImage(file="supporting/eqn_steadystate.gif")
            textTheory.image_create("end",image=imageIss)
            textTheory.insert("end","\n")
            
            # Part 1A: Normalization - text
            with open('supporting/text_CV_normalization.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            # Part 1B: Normalization - equation
            imageIss=tk.PhotoImage(file="supporting/eqn_steadystate.gif")
            textTheory.image_create("end",image=imageIss)
            textTheory.insert("end","\n")

            # Part 2A: Beta - text
            with open('supporting/text_CV_beta.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            # Part 2B: Beta - equation
            imageBeta=tk.PhotoImage(file="supporting/eqn_beta.gif")
            textTheory.image_create("end",image=imageBeta)
            textTheory.insert("end","\n")
            
            # Part 3A: Formal potential - text
            with open('supporting/text_CV_nernst.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            
            # Part 2B: Beta - equation
            imageNernst=tk.PhotoImage(file="supporting/eqn_nernst.gif")
            textTheory.image_create("end",image=imageNernst)
            textTheory.insert("end","\n")

        except:
            print("Error importing help text.") 
            
        textTheory.config(padx=20,pady=20,wrap="word")       
        textTheory.pack()
        scrollbarTheory.config(command=textTheory.yview)
        
        windowTheory.mainloop()
        
        
    def GuidePage():     
        windowGuide = tk.Toplevel(CVroot)
        windowGuide.title('Flux') # window title
        windowGuide.wm_iconbitmap('supporting/flux_logo.ico') # window icon
    
        
        frameGuide = tk.Frame(windowGuide)
        frameGuide.configure(background="white")
        frameGuide.pack(side="top")  
        
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarGuide = tk.Scrollbar(frameGuide)
        scrollbarGuide.pack(side="right",fill="y")
       
        textGuide = tk.Text(frameGuide, height=30,width=40, yscrollcommand=scrollbarGuide.set,borderwidth=0,background="white",font='Arial 10')

        
        # Import external files/images which contain the contents of the page
        try:
            with open('supporting/text_CV_guide.txt','r') as fh:
                for line in fh:
                    textBlockGuide = fh.readline()
                    textGuide.insert("end",textBlockGuide)
                    textGuide.insert("end","\n")
            fh.close()

        except:
            print("Error importing help text.") 
                      
        textGuide.config(padx=20,pady=20,wrap="word")       
        textGuide.pack()
        scrollbarGuide.config(command=textGuide.yview)
        
        windowGuide.mainloop()
     
    def AboutPage():
        windowAbout = tk.Toplevel(CVroot)
        windowAbout.title('Flux')
        windowAbout.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameLogo = tk.Frame(windowAbout)
        frameLogo.pack(side="left")
        frameAbout = tk.Frame(windowAbout)
        frameAbout.pack(side="right")

        imageLogo = tk.PhotoImage(file="supporting/flux_logo_large.gif")
        labelLogo = tk.Label(frameLogo,image=imageLogo)
        labelLogo.grid(row=0,column=0,padx=30,pady=30)
        
        labelAbout = tk.Label(frameAbout,text="Flux v1.0", font=36)
        labelAbout.grid(row=0,column=0, sticky="W"+"N",pady=10)
        labelAbout = tk.Label(frameAbout,text="GUI for treating SECM data\n Licensed under GNU GPL v3")
        labelAbout.grid(row=1,column=0, sticky="W"+"N",padx=10)
        
        windowAbout.mainloop()
        
        
class MenuPagesCA:
    def __init__(self,master):
        pass
        
    def TheoryPage():
        windowTheory = tk.Toplevel(CAroot)
        windowTheory.title('Flux') # window title
        windowTheory.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameTheory = tk.Frame(windowTheory)
        frameTheory.configure(background="white")
        frameTheory.pack(side="top")  
        
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarTheory = tk.Scrollbar(frameTheory)
        scrollbarTheory.pack(side="right",fill="y")

        textTheory = tk.Text(frameTheory, height=30,width=60, yscrollcommand=scrollbarTheory.set,borderwidth=0,background="white",font='Arial 10')

        # Import external files/images which contain the contents of the help page
        try:
            # Part 1A: CA theory
            with open('supporting/text_CA_theory.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            
            # Part 1B: UME CA pt1
            imageCA1=tk.PhotoImage(file="supporting/eqn_ume_ca.gif")
            textTheory.image_create("end",image=imageCA1)
            textTheory.insert("end","\n")
            
            # Part 1C: UME CA pt2
            imageCA2=tk.PhotoImage(file="supporting/eqn_ume_ca_tau.gif")
            textTheory.image_create("end",image=imageCA2)
            textTheory.insert("end","\n")
            
            # Part 1D: UME CA pt3
            imageCA3=tk.PhotoImage(file="supporting/eqn_ume_ca_tau2.gif")
            textTheory.image_create("end",image=imageCA3)
            textTheory.insert("end","\n")

        except:
            print("Error importing help text.") 
            
        textTheory.config(padx=20,pady=20,wrap="word")       
        textTheory.pack()
        
        scrollbarTheory.config(command=textTheory.yview)
        
        windowTheory.mainloop()
        
        
    def GuidePage():     
        windowGuide = tk.Toplevel(CAroot)
        windowGuide.title('Flux') # window title
        windowGuide.wm_iconbitmap('supporting/flux_logo.ico') # window icon
    
        
        frameGuide = tk.Frame(windowGuide)
        frameGuide.configure(background="white")
        frameGuide.pack(side="top")  
        
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarGuide = tk.Scrollbar(frameGuide)
        scrollbarGuide.pack(side="right",fill="y")
       
        textGuide = tk.Text(frameGuide, height=30,width=40, yscrollcommand=scrollbarGuide.set,borderwidth=0,background="white",font='Arial 10')

        # Import external files/images which contain the contents of the page
        try:
            with open('supporting/text_CA_guide.txt','r') as fh:
                for line in fh:
                    textBlockGuide = fh.readline()
                    textGuide.insert("end",textBlockGuide)
                    textGuide.insert("end","\n")
            fh.close()

        except:
            print("Error importing help text.") 
                      
        textGuide.config(padx=20,pady=20,wrap="word")       
        textGuide.pack()
        
        scrollbarGuide.config(command=textGuide.yview)
        
        windowGuide.mainloop()
     
    def AboutPage():
        windowAbout = tk.Toplevel(CAroot)
        windowAbout.title('Flux')
        windowAbout.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameLogo = tk.Frame(windowAbout)
        frameLogo.pack(side="left")
        frameAbout = tk.Frame(windowAbout)
        frameAbout.pack(side="right")

        imageLogo = tk.PhotoImage(file="supporting/flux_logo_large.gif")
        labelLogo = tk.Label(frameLogo,image=imageLogo)
        labelLogo.grid(row=0,column=0,padx=30,pady=30)
        
        labelAbout = tk.Label(frameAbout,text="Flux v1.0", font=36)
        labelAbout.grid(row=0,column=0, sticky="W"+"N",pady=10)
        labelAbout = tk.Label(frameAbout,text="GUI for treating SECM data\n Licensed under GNU GPL v3")
        labelAbout.grid(row=1,column=0, sticky="W"+"N",padx=10)
        
        windowAbout.mainloop()
        
class MenuPagesPAC:
    def __init__(self,master):
        pass
        
    def TheoryPage():
        windowTheory = tk.Toplevel(PACroot)
        windowTheory.title('Flux') # window title
        windowTheory.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameTheory = tk.Frame(windowTheory)
        frameTheory.configure(background="white")
        frameTheory.pack(side="top")  
        
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarTheory = tk.Scrollbar(frameTheory)
        scrollbarTheory.pack(side="right",fill="y")

        textTheory = tk.Text(frameTheory, height=30,width=60, yscrollcommand=scrollbarTheory.set,borderwidth=0,background="white",font='Arial 10')

        # Import external files/images which contain the contents of the help page
        try:
            # Part 0A: Normalization - text
            with open('supporting/text_PAC_general.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            # Part 1B: Normalization - equation
            imageIss=tk.PhotoImage(file="supporting/eqn_steadystate.gif")
            textTheory.image_create("end",image=imageIss)
            textTheory.insert("end","\n")
            
            
            # Part 1A: Normalization - text
            with open('supporting/text_CV_normalization.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            # Part 1B: Normalization - equation
            imageIss=tk.PhotoImage(file="supporting/eqn_steadystate.gif")
            textTheory.image_create("end",image=imageIss)
            textTheory.insert("end","\n")
    
            # Part 2A: Beta - text
            with open('supporting/text_CV_beta.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
            fh.close()
            # Part 2B: Beta - equation
            imageBeta=tk.PhotoImage(file="supporting/eqn_beta.gif")
            textTheory.image_create("end",image=imageBeta)
            textTheory.insert("end","\n")
            
            # Part 4A: Negfb - text
            with open('supporting/text_PAC_negfb.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
                    
            fh.close()
            
            # Part 3B: Negfb - equation
            imageNegfb=tk.PhotoImage(file="supporting/eqn_negfb.gif")
            textTheory.image_create("end",image=imageNegfb)
            textTheory.insert("end","\n")
            
            # Part 4A: Posfb - text
            with open('supporting/text_PAC_posfb.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
                    
            fh.close()
            
            # Part 4B: Posfb - equation
            imagePosfb=tk.PhotoImage(file="supporting/eqn_posfb.gif")
            textTheory.image_create("end",image=imagePosfb)
            textTheory.insert("end","\n")
            
            # Part 4C: Posfb (alpha) - equation
            imagePosfb2=tk.PhotoImage(file="supporting/eqn_posfb_alpha.gif")
            textTheory.image_create("end",image=imagePosfb2)
            textTheory.insert("end","\n")
            
            # Part 5A: Mixed fb - text
            with open('supporting/text_PAC_mixedfb.txt','r') as fh:
                for line in fh:
                    textBlockTheory = fh.readline()
                    textTheory.insert("end",textBlockTheory)
                    textTheory.insert("end","\n")
                    
            fh.close()
            
            # Part 5E: Mixed kinetics - equation
            imageMixedfb=tk.PhotoImage(file="supporting/eqn_mixedfb.gif")
            textTheory.image_create("end",image=imageMixedfb)
            textTheory.insert("end","\n")

        except:
            print("Error importing help text.") 
            
        textTheory.config(padx=20,pady=20,wrap="word")       
        textTheory.pack()
        
        scrollbarTheory.config(command=textTheory.yview)
        
        windowTheory.mainloop()
        
        
    def GuidePage():     
        windowGuide = tk.Toplevel(PACroot)
        windowGuide.title('Flux') # window title
        windowGuide.wm_iconbitmap('supporting/flux_logo.ico') # window icon
    
        
        frameGuide = tk.Frame(windowGuide)
        frameGuide.configure(background="white")
        frameGuide.pack(side="top")  
        
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarGuide = tk.Scrollbar(frameGuide)
        scrollbarGuide.pack(side="right",fill="y")
       
        textGuide = tk.Text(frameGuide, height=30,width=40, yscrollcommand=scrollbarGuide.set,borderwidth=0,background="white",font='Arial 10')

        
        # Import external files/images which contain the contents of the page
        try:
            with open('supporting/text_PAC_guide.txt','r') as fh:
                for line in fh:
                    textBlockGuide = fh.readline()
                    textGuide.insert("end",textBlockGuide)
                    textGuide.insert("end","\n")
            fh.close()

        except:
            print("Error importing help text.") 
                      
        textGuide.config(padx=20,pady=20,wrap="word")       
        textGuide.pack()
        
        scrollbarGuide.config(command=textGuide.yview)
        
        windowGuide.mainloop()
     
    def AboutPage():
        windowAbout = tk.Toplevel(CAroot)
        windowAbout.title('Flux')
        windowAbout.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameLogo = tk.Frame(windowAbout)
        frameLogo.pack(side="left")
        frameAbout = tk.Frame(windowAbout)
        frameAbout.pack(side="right")

        imageLogo = tk.PhotoImage(file="supporting/flux_logo_large.gif")
        labelLogo = tk.Label(frameLogo,image=imageLogo)
        labelLogo.grid(row=0,column=0,padx=30,pady=30)
        
        labelAbout = tk.Label(frameAbout,text="Flux v1.0", font=36)
        labelAbout.grid(row=0,column=0, sticky="W"+"N",pady=10)
        labelAbout = tk.Label(frameAbout,text="GUI for treating SECM data\n Licensed under GNU GPL v3")
        labelAbout.grid(row=1,column=0, sticky="W"+"N",padx=10)
        
        windowAbout.mainloop()


class MenuPagesTop:
    def __init__(self,master):
        pass
        
    def AboutPage():
        windowAbout = tk.Toplevel(main)
        windowAbout.title('Flux')
        windowAbout.wm_iconbitmap('supporting/flux_logo.ico') # window icon
        
        frameLogo = tk.Frame(windowAbout)
        frameLogo.pack(side="left")
        frameAbout = tk.Frame(windowAbout)
        frameAbout.pack(side="right")
        
        labelAbout = tk.Label(frameLogo,text="Flux v1.0", font=45)
        labelAbout.grid(row=0,column=0, sticky="W"+"N",pady=10, padx=30)
        labelDes = tk.Label(frameLogo,text="GUI for treating SECM data\n Licensed under GNU GPL v3")
        labelDes.grid(row=1,column=0, sticky="W"+"N", padx=30)
        
        imageLogo = tk.PhotoImage(file="supporting/flux_logo_large.gif")
        labelLogo = tk.Label(frameLogo,image=imageLogo)
        labelLogo.grid(row=2,column=0,padx=30,pady=30)
        
        
        frameMission = tk.Frame(windowAbout)
        frameMission.pack(side="top")
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarGuide = tk.Scrollbar(frameMission)
        scrollbarGuide.pack(side="right",fill="y")
    
        textGuide = tk.Text(frameMission, height=25,width=55, yscrollcommand=scrollbarGuide.set,borderwidth=0, font='Arial 10')
        
        # Import external files/images which contain the contents of the page
        try:
            with open('supporting/text_mission.txt','r') as fh:
                for line in fh:
                    textBlockGuide = fh.readline()
                    textGuide.insert("end",textBlockGuide)
                    textGuide.insert("end","\n")
            fh.close()

        except:
            print("Error importing help text.") 
                      
        textGuide.config(padx=20,pady=20,wrap="word")       
        textGuide.pack()
        scrollbarGuide.config(command=textGuide.yview)
        
        windowAbout.mainloop()

        
"""
Main Window
"""

main = tk.Tk()
main.title("Flux")
main.wm_iconbitmap('supporting/flux_logo.ico')
main.resizable(False,False)

## Set up menubar
menubar = tk.Menu(main)   
helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About",command=MenuPagesTop.AboutPage)
menubar.add_cascade(label="Help",menu=helpmenu)
main.config(menu=menubar)

# Create the basic frames
frameLogo = tk.Frame(main)
frameLogo.pack(side="left")
frameDropdown = tk.Frame(main)
frameDropdown.pack(side="right")


##### Left hand frame: logo ####### 
## Display flux logo
imageLogo = tk.PhotoImage(file="supporting/flux_logo_large.gif")
labelLogo = tk.Label(frameLogo,image=imageLogo)
labelLogo.grid(row=0,column=0,padx=30,pady=30)

##### Right hand frame: dropdown menu and info"
labelWelcome = tk.Label(frameDropdown,text="Welcome to Flux!",font='Arial 16')
labelWelcome.grid(row=1,column=0,padx=10,sticky="W")
labelDescription = tk.Label(frameDropdown,text="GUI for treating SECM data.")
labelDescription.grid(row=2,column=0,padx=10,sticky="W")
labelSpace=tk.Label(frameDropdown,text="")
labelSpace.grid(row=3,column=0,pady=10)


## Actual menu ###
labelSelect = tk.Label(frameDropdown, text="Select experiment type to start.")
labelSelect.grid(row=4, column= 0,sticky="W",padx=10)

# Create a stringvar which will contian the eventual choice
tkvar = tk.StringVar(main)
tkvar.set('   ') # set the default option
# Dictionary with options
choices = { 'Cyclic Voltammogram','Chronoamperogram','Approach curve','Image'}
popupMenu = tk.OptionMenu(frameDropdown, tkvar, *choices)
popupMenu.configure(width=20)
popupMenu.grid(row=5,column=0,sticky="W",padx=10)

## Go button
buttonGo = tk.Button(frameDropdown,text="Go!",state="disabled",command=OpenWindow)
buttonGo.grid(row=5,column=1,sticky="W",padx=10)
 
# Temporary label for indicating whether analysis is supported
labelSupport = tk.Label(frameDropdown,text="")
labelSupport.grid(row=6,column=0,sticky="W",padx=10)

# link function to change dropdown
tkvar.trace('w', change_dropdown)
 
main.mainloop()