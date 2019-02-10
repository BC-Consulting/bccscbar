# -*- coding: utf-8 -*-
"""
 ***************************************************************************
                            Colour Scale Bar
           A QGIS plugin to create a colour scale bar image file
      for a 1-band raster. Input is either a QML file having a colormap
      or a colour table file as created by the plugin:
      "1-band raster colour table".
                           -------------------
    copyright            : (C) 2011-2015 by BC Consulting - (C) 2019 GeoProc
    email                : info at geoproc dot com
 ***************************************************************************
 ***************************************************************************
 HISTORY: see metadata.txt
 
 ***************************************************************************
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 3 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************

 ***************************************************************************
 *                                                                         *
 *        bccscbar is distributed in the hope that it will be useful,      *
 *      but WITHOUT ANY WARRANTY; without even the implied warranty of     *
 *       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the      *
 *                GNU General Public License for more details.             *
 *                                                                         *
 ***************************************************************************
"""
def classFactory(iface):
    # load Plugin class from file bcccoltbl.py
    from .bccscbar import bccScBar
    return bccScBar(iface)
#
#===============================================================================
