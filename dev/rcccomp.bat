@echo off
rem OSGEO4W variables
set OSGEO4W_ROOT=C:\PROGRAMS\OSGeo4W
rem location of QGIS Python
SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27
rem Redefine the PATH to point to only interesting folders
set PATH=%OSGEO4W_ROOT%\bin;%OSGEO4W_ROOT%\apps\msys\bin;%WINDIR%\system32;%WINDIR%;%WINDIR%\WBem;%OSGEO4W_ROOT%\apps\Python27\Scripts
rem set other variables needed for different programs
for %%f in (%OSGEO4W_ROOT%\etc\ini\*.bat) do call %%f
rem MSYS specific variables
set WD=.\bin\
set MSYSCON=sh.exe
set MSYSTEM=MINGW32

echo .                                                    .
echo . The qrc file can point to the resource in a folder .
echo . BUT the resource MUST also be present in the same  .
echo . folder this bat file resides.                      .
echo .                                                    .
@echo on

pyrcc4 -o resources_rc.py resources.qrc

pause
