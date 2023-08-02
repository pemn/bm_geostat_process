:: full open source workflow for generating a geostatistics block model
:: License Apache 2.0
:: https://github.com/pemn/bm_geostat_process
@echo off
setlocal enabledelayedexpansion
:: # graphical interface
if "%~1" equ "" (
    if exist _gui.py (
        if not defined WINPYDIRBASE for /d %%i in (%appdata%\WPy64*) do set WINPYDIRBASE=%%i
        if defined WINPYDIRBASE call "!WINPYDIRBASE!\scripts\env.bat"
        python -m _gui %0
    ) else (
        echo usage: %~nx0 lito_mesh#mesh*vtk db_header*csv db_survey*csv db_assay*csv variables#variable:db_assay output_grid*vtk output_reserves*csv
        timeout 60
    )
    goto :EOF
)
:: # variable setup
set argv=%*
set env0=""
for /f "tokens=1 delims==" %%i in ('set') do set env0=!env0! %%i
for /f "usebackq delims=, tokens=1,*" %%i in (`powershell -c "$v = -split '%argv:"=%'; $k = (-split (select-string %0 -pattern '^\s+echo usage:') | select -skip 4 ) -replace '\W.+',''; foreach ($i in 0..($k.Count-1)) { '{0},{1}' -f $k[$i],$v[$i] }"`) do set %%i=%%j
powershell -c "$env0 = -split '%env0%'; get-childitem env: | ? Name -notin $env0"

:: # main code

:: ## hardcoded parameters
set grid_size=50
set lito=lito
set density=density
set pid=%random%
set tmp_csv=%~n0.%pid%.csv
set tmp_vtk=%~n0.%pid%.vtk

:: ## database

:: ### desurvey holes to samples
python db_desurvey_straight.py "%db_header%" "" "" "" "" "%db_survey%" "" "" "" "%db_assay%" "" "" "%tmp_csv%" 0 0

:: ### placeholder for database post process

:: ## grid creation

:: ### flag lito solids
python vtk_flag_regions.py "%grid_size%" "%lito_mesh%" %lito% flag3d "%tmp_vtk%" 0

:: ### multivariate estimation using either krigging or linear regression
python db_linear_model.py "%tmp_vtk%" "" "%tmp_csv%" "" "" "" "%variables%" rn "" %grid_size% full "%tmp_vtk%" 0

:: ## estimation postprocess

:: ### remove everything before the last "_" on lito
python vtk_evaluate_array.py "%tmp_vtk%" "lito = np.vectorize(lambda _: _.rpartition('_')[2])(lito)"

:: ### calculate density from lito
python vtk_evaluate_array.py "%tmp_vtk%" "%density% = np.choose(((lito == 'AA') * 1) + ((lito == 'BB') * 2) + ((lito == 'CC') * 3) + ((lito == 'DD') * 4), (np.nan, 1, 2, 3, 4))"

:: ### cleanup
move /y "%tmp_vtk%" "%output_grid%"
if exist %tmp_csv% del %tmp_csv%

:: ## checks and statistics

:: ## reports

:: ### grid details
python db_info.py "%output_grid%" 0

:: ### variable statistics
python bm_fivenum_weight.py "%output_grid%" "" %lito% "" "%density%;%variables%" "" 0

:: ### reserves estimation
python vtk_reserves.py "%output_grid%" "%lito%,,;volume,sum;volume=mass,sum,density" "" "" "" "%output_reserves%" 0

if exist "%output_reserves%" type "%output_reserves%" 
