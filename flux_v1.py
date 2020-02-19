import tkinter as tk
# Import apps
from Apps.Image import ImageApp
from Apps.ApproachCurve import PACApp
from Apps.ChronoAmperometry import CAApp
from Apps.CyclicVoltammetry import CVApp
# Import menus
from Menus.MMain import MenuPagesTop
from Menus.MApproachCurve import MenuPagesPAC
from Menus.MChronoAmperometry import MenuPagesCA
from Menus.MCyclicVoltammetry import MenuPagesCV
from Menus.MImage import MenuPagesImage

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
6. save_figure(s) : Save figure to .png file
7. export_data_action : Save processed data to .txt file
8. ResetWindow : Clear dataset, figure, and labels

Flux has been tested with the following package versions: numpy v1.16.2, 
pandas v0.24.1, scipy v1.2.1, scikit-image v0.14.2, matplotlib v3.0.3; some 
stability issues have been observed with other versions (particularly between 
numpy/scikit-image).


"""

"""
Functions
"""

FLUXVERSION = "Flux v1.0.2"


# Dropdown to select app
def change_dropdown(*args):
    buttonGo.config(state="normal")


# Select which app to open
def open_window():

    if tkvar.get() == "Image":
        start_image()

    elif tkvar.get() == "Cyclic Voltammogram":
        start_cyclicvoltammetry()

    elif tkvar.get() == "Chronoamperogram":
        start_chronoamperometry()

    elif tkvar.get() == "Approach curve":
        start_approach_curve()

    else:
        labelSupport.config(text="Still in development.")


def start_image():
    """Opens the image app and sets-up the menu bar"""
    # Open imaging window
    Imageroot = tk.Toplevel()
    Imageroot.title('Flux')
    Imageroot.wm_iconbitmap('supporting/flux_logo.ico')
    #        root.grab_set() # keep focus on window upon events
    ImageApp(Imageroot)

    # Set up menubar
    menubar = tk.Menu(Imageroot)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help", command=(lambda: MenuPagesImage.guide_page(Imageroot)))
    helpmenu.add_command(label="Theory", command=(lambda: MenuPagesImage.theory_page(Imageroot)))
    helpmenu.add_command(label="About", command=(lambda: MenuPagesImage.about_page(Imageroot, FLUXVERSION)))
    helpmenu.add_command(label="Report bug / request feature", command=(lambda: MenuPagesImage.github_page(Imageroot)))
    menubar.add_cascade(label="Help", menu=helpmenu)
    Imageroot.config(menu=menubar)

    Imageroot.mainloop()  # Run the program's main loop


def start_cyclicvoltammetry():
    """Opens the cyclic voltammetry app and sets-up the menu bar"""
    # Main window
    CVroot = tk.Toplevel()
    CVroot.title('Flux')  # window title
    CVroot.wm_iconbitmap('supporting/flux_logo.ico')  # window icon
    #        CVroot.grab_set() # keep focus on window upon events
    CVApp(CVroot)  # class where program to run in window is defined

    # Set up menubar
    menubar = tk.Menu(CVroot)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help", command=(lambda: MenuPagesCV.guide_page(CVroot)))
    helpmenu.add_command(label="Theory", command=(lambda: MenuPagesCV.theory_page(CVroot)))
    helpmenu.add_command(label="About", command=(lambda: MenuPagesCV.about_page(CVroot, FLUXVERSION)))
    helpmenu.add_command(label="Report bug / request feature", command=(lambda: MenuPagesCV.github_page(CVroot)))
    menubar.add_cascade(label="Help", menu=helpmenu)
    CVroot.config(menu=menubar)

    CVroot.mainloop()  # Run the program's main loop


def start_chronoamperometry():
    """opens the chronoamperometry app and sets-up the menu"""
    # Main window
    CAroot = tk.Toplevel()
    CAroot.title('Flux')  # window title
    CAroot.wm_iconbitmap('supporting/flux_logo.ico')  # window icon
    #        CAroot.grab_set() # keep focus on window upon events
    CAApp(CAroot)  # class where program to run in window is defined

    # Set up menubar
    menubar = tk.Menu(CAroot)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help", command=(lambda: MenuPagesCA.guide_page(CAroot)))
    helpmenu.add_command(label="Theory", command=(lambda: MenuPagesCA.theory_page(CAroot)))
    helpmenu.add_command(label="About", command=(lambda: MenuPagesCA.about_page(CAroot, FLUXVERSION)))
    helpmenu.add_command(label="Report bug / request feature", command=(lambda: MenuPagesCA.github_page(CAroot)))
    menubar.add_cascade(label="Help", menu=helpmenu)
    CAroot.config(menu=menubar)

    CAroot.mainloop()  # Run the program's main loop


def start_approach_curve():
    """Opens the approach curve app and sets-up the menu bar"""
    # Main window
    PACroot = tk.Toplevel()
    PACroot.title('Flux')  # window title
    PACroot.wm_iconbitmap('supporting/flux_logo.ico')  # window icon
    #        PACroot.grab_set() # keep focus on window upon events
    PACApp(PACroot)  # class where program to run in window is defined

    # Set up menubar
    menubar = tk.Menu(PACroot)
    helpmenu = tk.Menu(menubar, tearoff=0)
    helpmenu.add_command(label="Help", command=(lambda: MenuPagesPAC.guide_page(PACroot)))
    helpmenu.add_command(label="Theory", command=(lambda: MenuPagesPAC.theory_page(PACroot)))
    helpmenu.add_command(label="About", command=(lambda: MenuPagesPAC.about_page(PACroot, FLUXVERSION)))
    helpmenu.add_command(label="Report bug / request feature", command=(lambda: MenuPagesPAC.github_page(PACroot)))
    menubar.add_cascade(label="Help", menu=helpmenu)
    PACroot.config(menu=menubar)

    PACroot.mainloop()  # Run the program's main loop


"""
Main Window
"""
main = tk.Tk()
main.title("Flux")
main.wm_iconbitmap('supporting/flux_logo.ico')
main.resizable(False, False)

# Set up menubar
menubar = tk.Menu(main)
helpmenu = tk.Menu(menubar, tearoff=0)
helpmenu.add_command(label="About", command=(lambda: MenuPagesTop.about_page(main, FLUXVERSION)))
helpmenu.add_command(label="Report bug / request feature", command=(lambda: MenuPagesTop.github_page(main)))
menubar.add_cascade(label="Help", menu=helpmenu)
main.config(menu=menubar)

# Create the basic frames
frameLogo = tk.Frame(main)
frameLogo.pack(side="left")
frameDropdown = tk.Frame(main)
frameDropdown.pack(side="right")

# Left hand frame: logo
# Display flux logo
imageLogo = tk.PhotoImage(file="supporting/flux_logo_large.gif")
labelLogo = tk.Label(frameLogo, image=imageLogo)
labelLogo.grid(row=0, column=0, padx=30, pady=30)

# Right hand frame: dropdown menu and info"
labelWelcome = tk.Label(frameDropdown, text="Welcome to Flux!", font='Arial 16')
labelWelcome.grid(row=1, column=0, padx=10, sticky="W")
labelDescription = tk.Label(frameDropdown, text="GUI for treating SECM data.")
labelDescription.grid(row=2, column=0, padx=10, sticky="W")
labelSpace = tk.Label(frameDropdown, text="")
labelSpace.grid(row=3, column=0, pady=10)

# Actual menu
labelSelect = tk.Label(frameDropdown, text="Select experiment type to start.")
labelSelect.grid(row=4, column=0, sticky="W", padx=10)

# Create a stringvar which will contain the eventual choice
tkvar = tk.StringVar(main)
tkvar.set('   ')  # set the default option
# Dictionary with options
choices = {'Cyclic Voltammogram', 'Chronoamperogram', 'Approach curve', 'Image'}
popupMenu = tk.OptionMenu(frameDropdown, tkvar, *choices)
popupMenu.configure(width=20)
popupMenu.grid(row=5, column=0, sticky="W", padx=10)

# Go button
buttonGo = tk.Button(frameDropdown, text="Go!", state="disabled", command=(lambda: open_window()))
buttonGo.grid(row=5, column=1, sticky="W", padx=10)

# Temporary label for indicating whether analysis is supported
labelSupport = tk.Label(frameDropdown, text="")
labelSupport.grid(row=6, column=0, sticky="W", padx=10)

# link function to change dropdown
tkvar.trace('w', change_dropdown)

main.mainloop()  # Run the main window's main loop
