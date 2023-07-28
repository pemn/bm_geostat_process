## 📌 Description
full open source workflow for generating a geostatistics block model  
this script integrates multiple generic tools and modules in a single graphical desktop application  
the target audience is academic use by geostatistic professionals or industrial proof of concepts projects  
its not suited for production use  
## 📸 Screenshot
![screenshot1](https://github.com/pemn/assets/blob/main/bm_geostat_process1.png?raw=true)
## 🧩 Implementation
The main implementation is a windows batch script that calls the tools for each step.  
It can be easily ported to other platforms since the tools themselves inherity the portability of Python.  
## 📦 Installation
In case you dont have any python distribution already, the recomended distribution is [Winpython](https://winpython.github.io/) 3.11+.  
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
## 📝 Parameters
name|optional|description
---|---|------
||❎||
||☑️||
## 📓 Notes
## 📚 Examples
## 🙋 Support
Any question or problem contact:
 - paulo.ernesto
## 💎 License
Apache 2.0
Copyright ![vale_logo_only](https://github.com/pemn/assets/blob/main/vale_logo_only_r.svg?raw=true) Vale 2023
