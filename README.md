## 📌 Description
full open source workflow for generating a geostatistics block model  
this script integrates multiple generic tools and modules in a single graphical desktop application  
the target audience is academic use by geostatistic professionals or industrial proof of concepts projects  
its not suited for production use  
## 📸 Screenshot
![screenshot1](https://github.com/pemn/assets/blob/main/bm_geostat_process1.png?raw=true)
## 🧩 Implementation
The main implementation is a windows batch script that calls secondary processes for each step.  
It can be adapted to run in other platforms since the provided tools inherit the portability of Python.  
This geostatistics estimation process consists of the following steps:
 1. Data and parameter input
 2. Hole desurvey (runlength)
 3. Sample database postprocess
 4. Grid creation
 5. Flag litho solids
 6. Multivariate grade estimation
 7. Estimation Postprocess
 8. QA checks
 9. Reserve Report
## 📦 Installation
In case a python distribution is not already available, the recomended distribution is [Winpython](https://winpython.github.io/) 3.11+.  
Download the installer from the link above.  
Extract into this windows special folder:  
`%APPDATA%`  
The correct path to the python executable should be similar to this example:  
`C:\Users\user\AppData\Roaming\WPy64-31131\python-3.11.3.amd64\python.exe`  
Download this entire repository as zip and extract to a valid folder.  
Windows blocks executables in protected folders (and subfolders) such as:
 - Desktop
 - Downloads
 - Documents
 - OneDrive Synced folders

Also, its not recomended to use the winpython install folder to save this script.  
So you may need to create a new valid folder directly in the C: drive. Ex.:  
`c:\scripts\geostat`
## 🎬 Run
Double click the main script on Windows Explorer:  
`bm_geostat_process.bat`  
The graphical interface should appear.  
Optionally, it can be called from the command line. A proper command line can be generated by using the menu `File ➔ Copy command line` on the graphical interface.
## 📝 Parameters
name|optional|description
---|---|------
lito_mesh|❎|zero or more vtk format solid meshes defining the lithology volumes
db_header|❎|header of hole database in csv format (x,y,z)
db_survey|❎|survey of hole database in csv format (azimuth, dip)
db_assay|❎|assay of hole database in csv format (from, to)
variables|❎|select which fields will be estimated as grades
regression_engine||the estimation can be adapted to use different engines
||scikit|open source scikit linear regression
||pykrige|open source pykrige native python krigging
||isatis_isapy|proprietary native python krigging from Geovariances
||vulcan_djbmest|proprietary command line krigging from Maptek
output_grid|❎|path to save the block model in vtk format
output_reserves|☑️|path to save the reserves report in csv format
output_heatmap|☑️|path to save the a heatmap chart of the result in pdf format
## 📓 Notes
## 📚 Examples
### output 3d grid
![screenshot2](https://github.com/pemn/assets/blob/main/bm_geostat_process2.png?raw=true)
### output reserves report
![screenshot3](https://github.com/pemn/assets/blob/main/bm_geostat_process3.png?raw=true)
### output heatmap chart
![screenshot4](https://github.com/pemn/assets/blob/main/bm_geostat_process4.png?raw=true)  
![screenshot5](https://github.com/pemn/assets/blob/main/bm_geostat_process5.png?raw=true)
## 🧰 Tools
 - bm_geostat_process.bat: main script
 - bm_fivenum_weight.py: descriptive statistics
 - bm_pk_krig3d.py: krigging regressor
 - db_pk_krig3d.py: helper script for kirring regressor
 - db_assay_runlength.py: helper script for sample compositing
 - db_create_from_to.py: helper script for sample composition
 - db_desurvey_straight.py: sample compositing from collar,survey,assay
 - db_info.py: reports generic info about a structured data file
 - db_linear_model.py: linear regressor
 - db_pandas_evaluate.py: run generic calculations on structured data
 - db_voxel_view.py: create heatmap chart from 3d grids
 - vtk_evaluate_array.py: run generic calculations on vtk format files
 - vtk_flag_regions.py: create or flag a grid using solids
 - vtk_mine.py: reserve depletion calculation
 - vtk_reserves.py: reserves report
## 🙋 Support
Any question or problem contact:
 - paulo.ernesto
## 💎 License
Apache 2.0  
Copyright ![vale_logo_only](https://github.com/pemn/assets/blob/main/vale_logo_only_r.svg?raw=true) Vale 2023
