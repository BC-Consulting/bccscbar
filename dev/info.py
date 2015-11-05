﻿# -*- coding: utf-8 -*-
#
# Colour Scale Bar (c) BC Consulting 2011
#
#  modified by Thomas Wahlmüller (c) 2012 2012-03-07
#  contact: thomas dot wahlmueller at gmx dot net
#  Added support for INTERPOLATED and EXACT styles. Annotate extrema
#  is ignored when interpolated. At least two ticks (extrema) are
#  displayed. EXACT style uses same visualisation as discrete.
#
#    This file is part of "bccscbar"
#
#    bccscbar is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    bccscbar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with bccscbar.  If not, see <http://www.gnu.org/licenses/>.
#
#===============================================================================
#
import platform
from PyQt4.QtCore import *

currVersion   = u'0.10.0'
currDate      = u'05 November 2015'
MSG_BOX_TITLE = u"Colour Scale Bar"
inMenu        = u"Raster Colours"
icon          = u":/plugins/bccscbar/res/img/bccscbar.png"
Author        = u"BC Consulting - info at bc-consult dot com; Thomas Wahlmüller - thomas dot wahlmueller at gmx dot net"
Sinfo         = u"Generates a colour scale bar image file"
Linfo =(u"This plugin creates a colour scale bar image file (png) for a coloured"
        " 1-band raster. Use the created colour scale bar as legend in print composer.")
#
#===============================================================================
#
def Usage():
    """ Return usage and info message about the plugin """
    #
    L = """<center><b>Colour Scale Bar</b><br />
        <i>by BC-Consulting</i><br />
        Version: %s<br />
        %s<br />&nbsp;<br />
        Distributed under the <a href="http://www.gnu.org/licenses/">GPL</a>
        licence<br />&nbsp;<br />
        ---   How to use this app   ---<br/ ></center>
        <ol>
        <li>Select a QGIS .qml file containing a saved colour palette
             OR select a colour palette file (as generated by '1-band
             raster colour table' OR use the currently selected
             one-band raster layer from the Layers panel.<br>
             The colour palette can be of type: DISCRETE, 
             INTERPOLATED or EXACT.</li>

        <li>Fill in the relevant info:<br />
             At minimum you have to define the aspect of the final colour scale
             bar: either vertical or horizontal.</li>

        <li>Click 'Create' to create the colour scale bar image file. The file
             is located in the same folder as the input file.</li>

        <li>Open your favorite image viewer and point it to the file returned by
             the plugin.</li>

        <li>Tweak the parameters and run again until the time you are satisfied
             with your colour scale bar.</li>

        <li>Use the created colour scale bar as legend in print composer.</li>
        </ol>
        <br />&nbsp;<br />
        <b>NOTES</b>
        <ul>
           <li><b><font color="red">Results are not guaranteed. You will
           perhaps need to tweak the parameters in order to get acceptable
           results!</font><b></li>
           <li>The title can contains more than one line. Separate each line
               with '\\n'.</li>
           <li>The units text can only be one line. An extra lines are ignored.
               </li>
           <li>The table files do not contain information about the minimum
               value. If needed, you will have to enter it in the 'Minimum'
               textbox.</li>
           <li>The 'enforce'checkbox is to force the decimal places to be that
               number, padding with trailing 0s if necessary.</li>
           <li>The resolution of the colour scale bar image is 72 dpi.</li>
        </ul>
        <p>For more info please see
           <a href="http://www.bc-consult.com/free/bccscbar.html">here</a>.</p>
        <p>To report a bug go to the 
           <a href="http://hub.qgis.org/projects/bccscbar">bug tracker</a>.</p>
        <hr>
        <p align="center"><a href="http://www.bc-consult.com/">
        BC-Consulting</a><br />
        <i>Python %s - Qt %s - PyQt %s on %s</i></p>
        """ % (str(currVersion), str(currDate), platform.python_version(), \
        QT_VERSION_STR, PYQT_VERSION_STR, platform.system())
    #
    return L
#
#===============================================================================