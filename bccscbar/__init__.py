# -*- coding: utf-8 -*-
"""
 ***************************************************************************
                            Colour Scale Bar
           A QGIS plugin to create a colour scale bar image file
      for a 1-band raster. Input is either a QML file having a colormap
      or a colour table file as created by the plugin:
      "1-band raster colour table".
                           -------------------
    copyright            : (C) 2011-2015 by BC Consulting
    email                : info at bc-consult dot com
 ***************************************************************************
 ***************************************************************************
 MODIFICATION 2015-05-09
 By: BC COnsulting
 Contact: see above
 
 Description:
 Internationalisation and re-compilation of dialog, in response to users 
 reporting that the plugin does nothing on their machines.
 ...........................................................................
 
 MODIFICATION 2014-10-06
 By: BC COnsulting
 Contact: see above
 
 Description:
 Compatibility with QGIS V2.x
  - Removed all QString() occurrences!
  - Compatible with QMLs from QGIS versions 1.x and 2.x
 ...........................................................................

 MODIFICATION 2012-03-07
 By: Thomas Wahlmüller
 Contact: thomas dot wahlmueller at gmx dot net
 
 Description:
 Plugin is extended to support INTERPOLATION and EXACT styles. Annotate 
 extrema option is ignored when interpolated. At least two ticks (equals
 extrema in style) are displayed. EXACT style uses same visualisation as
 DISCRETE styles.
 
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
