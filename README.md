# Flux
Flux is a Python-based GUI for treating scanning electrochemical microscopy (SECM) data; subapplications with specific functionality for images, approach curves, cyclic voltammograms, and chronoamperograms are available. Standard output files (.asc, .txt, .dat, .mat, .csv, .img) for a number of SECM instrument manufacturers are supported.

# Getting Started
Two options are available for running Flux
1) An executable file (no setup required) -- available from http://bioelectrochemistry.mcgill.ca/software.html
2) The underlying Python script (supports modification). 

To run the script, download the .py file and folder of supporting files. When Flux first opens, it will ask you to select a particular experiment, which will open a separate window with an application specialized for that experiment. To import, plot, and process your experimental data, take the following steps:
1) Base tab - Select File
2) Base tab - Import File
3) Base tab - Plot Data

Additional data treatment functionality (normalization of currents, slope correction, nonlinear curve fitting, etc.) is available on the Analytics tab. Customization of formatting (units, colormap, etc.) is availble on the Formatting tab. Whenever making a change to the appearance of the graph, the Plot Data button needs to be clicked again.

# Screenshots

Images:

<img src="https://github.com/stepheli/fluxproject/blob/master/screenshots/imageapp.PNG" width="400"> 

Approach curves:

<img src="https://github.com/stepheli/fluxproject/blob/master/screenshots/pacapp.PNG" width="400"> 

Cyclic voltammograms:

<img src="https://github.com/stepheli/fluxproject/blob/master/screenshots/cvapp.PNG" width="400"> 

Chronoamperograms:

<img src="https://github.com/stepheli/fluxproject/blob/master/screenshots/caapp.PNG" width="400">

# Known Issues
1) If Flux cannot find the supporting files, it will fail to start. Ensure the Supporting folder is in the same folder as the script.

2) Differences in the edge detection output have been observed depending on the scikit-image package version, due to updates in the Canny algorithm implementation. Furthermore, numpy/scikit-image incompatibilities have been observed for specific versions of each. A self-contained .exe with compatible versions of all required packages is available from : http://bioelectrochemistry.mcgill.ca/software.html. If working with the .py file directly, the package versions used for testing are listed below. All other combinations are used at your own risk.
- numpy v1.16.2
- pandas v0.24.1
- scipy v1.2.1
- scikit-image v0.14.2
- matplotlib v3.0.3
- pyqt5 v5.12

# Built With
[Pyinstaller] (https://www.pyinstaller.org/) Packaging of the .exe

# License
This project is licensed under the GPL-3.0 License -- see the LICENSE.MD file for details
