@echo off
setlocal enabledelayedexpansion
echo * %*
if "%~1" equ "" (
    if exist _gui.py (
        if not defined WINPYDIRBASE for /d %%i in (%appdata%\WPy64*) do set WINPYDIRBASE=%%i
        if defined WINPYDIRBASE call "!WINPYDIRBASE!\scripts\env.bat"
        python -m _gui %0
    ) else (
        echo usage: %~nx0 db_header*csv db_survey*csv db_assay*csv lito_mesh#mesh*vtk output_grid*vtk output_reserves*csv
        timeout 60
    )
    goto :EOF
)
:: main code

:: hardcoded parameters
set grid_size=50
set lito=lito
set variables="GRADE1;GRADE2;GRADE3"

:: user parameters
set db_header=%1
set db_survey=%2
set db_assay=%3
set lito_mesh=%4
set output_grid=%5
set output_reserves=%6
set pid=%random%
set tmp1=%~n0.%pid%.csv
set tmp2=%~n0.%pid%.vtk

:: desurvey holes to samples
python db_desurvey_straight.py "%db_header%" "" "" "" "" "%db_survey%" "" "" "" "%db_assay%" "" "" %tmp1% 0 0

:: flag lito solids
python vtk_flag_regions.py "%grid_size%" "%lito_mesh%" %lito% flag3d %tmp2% 0

:: multivariate estimation using either krigging or linear regression
python db_linear_model.py "%tmp2%" "" "%tmp1%" "" "" "" "%variables%" rn "" %grid_size% full %output% 0

:: show grid details
python db_info.py "%output%" 0

:: placeholder for checks

:: placeholder for reserves estimation
python vtk_reserves.py "%output%" "%lito%,,;volume,sum" "" "" "" "%reserves%" 0

if exist %tmp1% del %tmp1%
if exist %tmp2% del %tmp2%

echo finished
