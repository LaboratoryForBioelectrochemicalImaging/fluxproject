import tkinter as tk

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


class MenuPagesTop:
    def __init__(self, master):
        pass

    @staticmethod
    def AboutPage( version, main):
        windowAbout = tk.Toplevel(main)
        windowAbout.title('Flux')
        windowAbout.wm_iconbitmap('supporting/flux_logo.ico')  # window icon

        frameLogo = tk.Frame(windowAbout)
        frameLogo.pack(side="left")
        frameAbout = tk.Frame(windowAbout)
        frameAbout.pack(side="right")

        labelAbout = tk.Label(frameLogo, text=version, font=45)
        labelAbout.grid(row=0, column=0, sticky="W" + "N", pady=10, padx=30)
        labelDes = tk.Label(frameLogo, text="GUI for treating SECM data\n Licensed under GNU GPL v3")
        labelDes.grid(row=1, column=0, sticky="W" + "N", padx=30)

        imageLogo = tk.PhotoImage(file="supporting/flux_logo_large.gif")
        labelLogo = tk.Label(frameLogo, image=imageLogo)
        labelLogo.grid(row=2, column=0, padx=30, pady=30)

        frameMission = tk.Frame(windowAbout)
        frameMission.pack(side="top")
        # Create text widget with scrollbar to contain large amounts of text
        scrollbarGuide = tk.Scrollbar(frameMission)
        scrollbarGuide.pack(side="right", fill="y")

        textGuide = tk.Text(frameMission, height=25, width=55, yscrollcommand=scrollbarGuide.set, borderwidth=0,
                            font='Arial 10')

        # Import external files/images which contain the contents of the page
        try:
            with open('supporting/text_mission.txt', 'r') as fh:
                for line in fh:
                    textBlockGuide = fh.readline()
                    textGuide.insert("end", textBlockGuide)
                    textGuide.insert("end", "\n")
            fh.close()

        except:
            print("Error importing help text.")

        textGuide.config(padx=20, pady=20, wrap="word")
        textGuide.pack()
        scrollbarGuide.config(command=textGuide.yview)

        windowAbout.mainloop()
