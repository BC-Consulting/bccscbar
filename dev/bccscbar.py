# -*- coding: utf-8 -*-
#
# Colour Scale Bar (c) BC Consulting 2011 - (c) GeoProc 2019
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
#  little essential things needed for the smooth running of the code...
#
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

import os
import string

from qgis.core import *
from qgis.gui import *

from cdlgSCBR import cdlgSCBR

import info as uu
import resources
#
#===============================================================================
#
class bccScBar():

    def __init__(self, iface):
        # save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = QFileInfo(QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/bccscbar"
        # initialize locale
        localePath = ""

        if QGis.QGIS_VERSION_INT < 10900:
           locale = QSettings().value("locale/userLocale").toString()[0:2]
        else:
           locale = QSettings().value("locale/userLocale")[0:2]


        if QFileInfo(self.plugin_dir).exists():
            localePath = self.plugin_dir + "/i18n/bccscbar_" + locale + ".qm"

        if QFileInfo(localePath).exists():
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        # create action that will start plugin configuration
        self.action=QAction(QIcon(uu.icon), \
                            uu.MSG_BOX_TITLE, self.iface.mainWindow())
        self.action.setWhatsThis(uu.Sinfo)
        self.action.setStatusTip(uu.Sinfo)
        QObject.connect(self.action, SIGNAL("triggered()"), self.cdlgTBLcr)
        # add toolbar button and menu item
        if hasattr(self.iface, "addPluginToRasterMenu"):
            # new menu available so add both actions into PluginName submenu
            # under Raster menu
            self.iface.addPluginToRasterMenu( uu.inMenu, self.action )
            # and add Run button to the Raster panel
            self.iface.addRasterToolBarIcon( self.action )
        else:
            # oops... old QGIS without additional menus. Place plugin under
            # Plugins menu as usual
            self.iface.addPluginToMenu( uu.inMenu, self.action )
            # and add Run button to the Plugins panel
            self.iface.addToolBarIcon( self.action )

    def unload(self):
        # remove the plugin menu item and icon
        if hasattr(self.iface, "addPluginToRasterMenu"):
            # new menu used, remove submenus from main Raster menu
            self.iface.removePluginRasterMenu( uu.inMenu, self.action )
            # also remove button from Raster toolbar
            self.iface.removeRasterToolBarIcon( self.action )
        else:
            # Plugins menu used, remove submenu and toolbar button
            self.iface.removePluginMenu( uu.inMenu, self.action )
            self.iface.removeToolBarIcon( self.action )

    def cdlgTBLcr(self):
        """ Create and display the dialog to do the colour scale bar """
        dialog = cdlgSCBR(self.iface)
        dialog.show()
        result = dialog.exec_()
        if result:
            pass
