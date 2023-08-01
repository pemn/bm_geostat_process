@echo off
setlocal enabledelayedexpansion
echo * %*
if "%~1" equ "" (
    if exist _gui.py (
        if not defined WINPYDIRBASE for /d %%i in (%appdata%\WPy64*) do set WINPYDIRBASE=%%i
        if defined WINPYDIRBASE call "!WINPYDIRBASE!\scripts\env.bat"
        python -m _gui %0
    ) else (
        echo usage: %~nx0 db_header*csv db_survey*csv db_assay*csv variables#variable:db_assay lito_mesh#mesh*vtk output_grid*vtk output_reserves*csv
        timeout 60
    )
    goto :EOF
)
:: main code

:: hardcoded parameters
set grid_size=50
set lito=lito

:: user parameters
set db_header=%1
set db_survey=%2
set db_assay=%3
set variables=%4
set lito_mesh=%5
set output_grid=%6
set output_reserves=%7
set pid=%random%
set tmp_csv=%~n0.%pid%.csv
set tmp_vtk=%~n0.%pid%.vtk

:: # database

:: ## desurvey holes to samples
python db_desurvey_straight.py "%db_header%" "" "" "" "" "%db_survey%" "" "" "" "%db_assay%" "" "" "%tmp_csv%" 0 0

:: ## placeholder for database post process

:: # grid creation

:: ## flag lito solids
python vtk_flag_regions.py "%grid_size%" "%lito_mesh%" %lito% flag3d "%tmp_vtk%" 0

:: ## multivariate estimation using either krigging or linear regression
python db_linear_model.py "%tmp_vtk%" "" "%tmp_csv%" "" "" "" "%variables%" rn "" %grid_size% full "%tmp_vtk%" 0

:: # estimation postprocess

:: ## remove everything before the last "_" on lito
python vtk_evaluate_array.py "%tmp_vtk%" "lito = np.vectorize(lambda _: _.rpartition('_')[2])(lito)"

:: ## calculate density from lito
python vtk_evaluate_array.py "%tmp_vtk%" "density = np.choose(((lito == 'BB') * 1) + ((lito == 'CC') * 2), (1, 2, 3))"

:: ## cleanup
move /y "%tmp_vtk%" "%output_grid%"
if exist %tmp_csv% del %tmp_csv%

:: # checks

:: # reports

:: ## grid details
python db_info.py "%output_grid%" 0

:: ## reserves estimation
python vtk_reserves.py "%output_grid%" "%lito%,,;volume,sum" "" "" "" "%output_reserves%" 0

echo finished
