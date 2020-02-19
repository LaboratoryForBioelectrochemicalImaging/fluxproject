import tkinter as tk
import webbrowser

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
    """This is the parent class for all of the menus in flux. It contains an about page, and a page with links to the
    project github."""
    def __init__(self, master):
        pass

    @staticmethod
    def about_page(main, version):
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

    @staticmethod
    def open_issue():
        try:
            webbrowser.open_new("https://github.com/LaboratoryForBioelectrochemicalImaging/fluxproject/issues")
        except:
            pass

    @staticmethod
    def open_github():
        try:
            webbrowser.open_new("https://github.com/LaboratoryForBioelectrochemicalImaging/fluxproject")
        except:
            pass

    @staticmethod
    def github_page(main):
        """This method displays information about the project's github page, enabling users to quickly navigate to
        resources for reporting bugs, requesting features, or forking the repository."""
        window_github = tk.Toplevel(main)
        window_github.title('Flux')  # window title
        window_github.wm_iconbitmap('supporting/flux_logo.ico')  # window icon

        frame_github = tk.Frame(window_github)
        frame_github.configure(background="white", height=main.winfo_rootx())
        frame_github.pack(side="top")

        # Create text widget with scrollbar to contain large amounts of text

        heading_issue = tk.Label(frame_github, text="Bug report / feature request", borderwidth=0, pady=20, background="white", font='Arial 16')
        text_issues = tk.Text(frame_github, height=3, width=80, borderwidth=0, background="white", font='Arial 10')
        text_issues.insert("end", "If you think you have found a bug or would like to request a feature, please report it by opening an issue on our github page: \nhttps://github.com/LaboratoryForBioelectrochemicalImaging/fluxproject/issues")
        issue_button = tk.Button(frame_github, text="Open issues page in browser", pady=5, command=MenuPagesTop.open_issue)
        text_issues.config(padx=20, pady=10, wrap="word")
        heading_contribute = tk.Label(frame_github, text="Add to Flux", borderwidth=0, pady=20, background="white", font='Arial 16')
        text_contribute = tk.Text(frame_github, height=3, width=80, borderwidth=0, background="white", font='Arial 10')
        text_contribute.insert("end", "If you would like to modify flux to better fit your purposes, feel free to check out our github page: \nhttps://github.com/LaboratoryForBioelectrochemicalImaging/fluxproject")
        text_contribute.config(padx=20, pady=10, wrap="word")
        add_button = tk.Button(frame_github, text="Open flux github in browser", pady=5, command=MenuPagesTop.open_github)

        heading_issue.pack(side=tk.TOP)
        text_issues.pack(side=tk.TOP)
        issue_button.pack(side=tk.TOP)
        heading_contribute.pack(side=tk.TOP)
        text_contribute.pack(side=tk.TOP)
        add_button.pack(side=tk.TOP)

        window_github.mainloop()
