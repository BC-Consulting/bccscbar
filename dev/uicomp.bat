@set OSGEO4W_ROOT=C:\PROGRAMS\OSGeo4W
@set PATH=%OSGEO4W_ROOT%\bin;%OSGEO4W_ROOT%\apps\msys\bin;%WINDIR%\system32;%WINDIR%;%WINDIR%\WBem;%OSGEO4W_ROOT%\apps\Python27\Scripts
@set QT_PLUGIN_PATH=%OSGEO4W_ROOT%\apps\qt4\plugins
@SET PYTHONHOME=%OSGEO4W_ROOT%\apps\Python27

@if exist ui_dialogScaleBar.py del ui_dialogScaleBar.py
call pyuic4 uiDLG.ui >ui_dialogScaleBar.py
