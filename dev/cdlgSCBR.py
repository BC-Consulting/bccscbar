# -*- coding: utf-8 -*-
#
# Colour Scale Bar (c) BC Consulting 2011
#
#  modified by Thomas Wahlmüller (c) 2012 2012-03-07
#  contact: thomas dot wahlmueller at gmx dot net
#  Added support for INTERPOLATED and EXACT styles. Annotate extrema
#  is ignored when interpolated. At least two ticks (extrema) are
#  displayed. EXACT style uses same visualisation as discrete.
#  - Modified CreateScBar: support of linear and exact styles
#  - Additional Imports: math, numpy, sys
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
import os
import string
import sys
import math
import numpy as np

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from qgis.core import *
from qgis.gui import *

import info
import utils as uu

from ui_dialogScaleBar import Ui_Dialog
#
#===============================================================================
#
class cdlgSCBR(QDialog,Ui_Dialog):

    def __init__(self, iface, parent=None):
        """
        Sets up dialog for colour scale bar
        """
        super(cdlgSCBR, self).__init__(iface.mainWindow())
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setupUi(self)
        self.iface = iface
        self.canvas = self.iface.mapCanvas()
        self.fil = ''                    # the qml or colour table file (input)
        self.UseCurrentRaster = False    # flag to tell we are using the current raster
        self.goout = False               # flag to control execution flow
        #
        for i in range(7,25):
            self.cbFSize.addItem(str(i))
        self.cbFSize.setCurrentIndex(7)
        #
        dd = QgsApplication.qgisUserDbFilePath()
        self.userPluginPath = QFileInfo(dd).path() + "/python/plugins/bccscbar/"
        #
        #-----------------------------------------------------------------------
        # Set up the UI comms
        QObject.connect(self.btnOut, SIGNAL("clicked()"), self.SelDir)
        QObject.connect(self.btnCreate, SIGNAL("clicked()"), self.CreateSCBar)
        QObject.connect(self.btnExit, SIGNAL("clicked()"), self.reject)
        QObject.connect(self.btnInfo, SIGNAL("clicked()"), self.helpme)
        QObject.connect(self.btnEntry, SIGNAL("clicked()"), self.GetTableFile)
        QObject.connect(self.radAspect1, SIGNAL("clicked()"), self.SetBox1)
        QObject.connect(self.radAspect2, SIGNAL("clicked()"), self.SetBox2)
        QObject.connect(self.radUseCurrent, SIGNAL("clicked()"), self.SetCurRaster)
        #
        # Get saved path to last image
        self.settings = QSettings()
        self.myPath   = str(self.settings.value("/bccBar/pathIM"))
        self.tbPath   = str(self.settings.value("/bccBar/pathTB"))
#-------------------------------------------------------------------------------

    def CreateSCBar(self):
        """ Create the colour scale bar image file """
        #Do some checks before we go
        if self.txtDecimal.text() == '': self.txtDecimal.setText('4')
        myData = uu.storeVar()
        myData.txtDeci    = self.txtDecimal.text()
        myData.bEnforce   = self.ckEnforce.isChecked()
        myData.scTitle    = self.txtTitle.text()
        myData.scUnits    = self.txtUnits.text()
        myData.scFontSize = self.cbFSize.currentText()
        myData.bV         = self.radAspect1.isChecked()
        myData.bH         = self.radAspect2.isChecked()
        myData.bAuto      = self.radTick1.isChecked()
        myData.nbTicks    = self.txtNbTicks.text()
        myData.boxW       = self.txtW.text()
        myData.boxH       = self.txtH.text()
        myData.doExtrema  = self.ckExtrema.isChecked()
        myData.mini       = self.txtMinimum.text()
        #
        if self.fil == '':
            QMessageBox.critical(self,info.MSG_BOX_TITLE,
                     "You have to first select a file!")
            return
        if not myData.bH and not myData.bV:
            QMessageBox.critical(self,info.MSG_BOX_TITLE,
                     "Please select either a vertical or horizontal scale bar!")
            return
        if not myData.bAuto and str(myData.nbTicks) == '':
            QMessageBox.critical(self,info.MSG_BOX_TITLE,
                     "Please give the number of ticks needed!")
            return
        #Now do the hard work here
        #
        # Suck the file into memory and extract the colour palette
        # mode: 0=discrete, 1=linear, 2=exact
        [res, arColo, arV, nMode] = uu.ReadTableFile(self.fil)
        if not res:
            QMessageBox.critical(self,info.MSG_BOX_TITLE,str(arColo))
            return
        #
        #
        #DISCRETE mode
        if nMode == 0:
            #
            #Create and save colour scale
            if myData.bV:
                Vscale = uu.scalebarVerticalDiscreteAnnotation(res, arColo, arV, myData, self.fil, self.myPath)
                LcolFile = Vscale.retrieveFile()
            elif myData.bH:
                Hscale = uu.scalebarHorizontalDiscreteAnnotation(res, arColo, arV, myData, self.fil, self.myPath)
                LcolFile = Hscale.retrieveFile()
            else:
                return
        #
        #LINEAR mode
        elif nMode == 1:
            # Number of Colours to Interpolate if less colors than newColors/2
            nNewColors = 200
            if res < 2:
                #Cannot interpolate colors if less than two colors specified
                QMessageBox.critical(self, info.MSG_BOX_TITLE,"At least 2 colors need to be specifed in color file if using linear interpolation!")
                return
            if res <= (nNewColors/2):
                #Also do not interpolated if more than half of newColors Colors available
                #Possible Optimization:
                #  --> Calculate Number of Output Colors based on box size, number of colors in file,...
                #  --> Setting Number of Output Colors in user interface
                #
                #Calculate colors interpolated between two existing colors
                interpol = int(math.ceil(nNewColors / res))
                if interpol < 1: interpol = 1
                #Initialize new color and value array
                arColoInterpol = np.zeros((3,res + interpol*(res-1)),int)
                arValInterpol  = np.zeros(res + interpol*(res-1),np.float32)
                arColoInterpol[0,0] = arColo[0,0]
                arColoInterpol[1,0] = arColo[1,0]
                arColoInterpol[2,0] = arColo[2,0]
                arValInterpol[0] = arV[0]
                #Counting of interpolated colors and values
                z = 1
                #Interpolate colors and values
                for j in range(res-1):
                    for i in range(1,interpol+1,1):
                        arColoInterpol[0,z] = arColo[0,j] + int(round(i*(arColo[0,j+1]-arColo[0,j])/(interpol+1)))
                        arColoInterpol[1,z] = arColo[1,j] + int(round(i*(arColo[1,j+1]-arColo[1,j])/(interpol+1)))
                        arColoInterpol[2,z] = arColo[2,j] + int(round(i*(arColo[2,j+1]-arColo[2,j])/(interpol+1)))
                        arValInterpol[z] = arV[j] + round(i*(arV[j+1] - arV[j])/(interpol+1))
                        z = z + 1
                    arColoInterpol[0,z] = arColo[0,j+1]
                    arColoInterpol[1,z] = arColo[1,j+1]
                    arColoInterpol[2,z] = arColo[2,j+1]
                    arValInterpol[z] = arV[j+1]
                    z = z + 1
                #
                #Create and save colour scale
                if myData.bV:
                    Vscale = uu.scalebarVerticalInterpolatedAnnotation(z-1, arColoInterpol, arValInterpol, myData, self.fil, self.myPath)
                    LcolFile = Vscale.retrieveFile()
                elif myData.bH:
                    Hscale = uu.scalebarHorizontalInterpolatedAnnotation(z-1, arColoInterpol, arValInterpol, myData, self.fil, self.myPath)
                    LcolFile = Hscale.retrieveFile()
                else:
                    return
            else:
                #Create and save colour scale without interpolating
                #because there are enough elements in file
                if myData.bV:
                    Vscale = uu.scalebarVerticalInterpolatedAnnotation(res, arColo, arV, myData, self.fil, self.myPath)
                    LcolFile = Vscale.retrieveFile()
                elif myData.bH:
                    Hscale = uu.scalebarHorizontalInterpolatedAnnotation(res, arColo, arV, myData, self.fil, self.myPath)
                    LcolFile = Hscale.retrieveFile()
                else:
                    return
        #
        #EXACT mode
        else:
            #Create and save colour scale
            if myData.bV:
                Vscale = uu.scalebarVerticalExactAnnotation(res, arColo, arV, myData, self.fil, self.myPath)
                LcolFile = Vscale.retrieveFile()
            elif myData.bH:
                Hscale = uu.scalebarHorizontalExactAnnotation(res, arColo, arV, myData, self.fil, self.myPath)
                LcolFile = Hscale.retrieveFile()
            else:
                return
        #
        if str(LcolFile) != '': QMessageBox.information(self, \
                                 info.MSG_BOX_TITLE, \
                                 "Colour scale bar created in:\n"+str(LcolFile))
        else: QMessageBox.critical(self,info.MSG_BOX_TITLE, \
                                 "ERROR: cannot create, save colour scale bar!")
#-------------------------------------------------------------------------------

    def GetTableFile(self):
        """ get the file name of the colour table to act on """
        #
        # Delete temp qml file (if it exist)
        try:
            if self.UseCurrentRaster and self.fil != '':
                os.remove(self.fil)
        except:
            pass
        #
        # Deselect use current raster
        self.goout = True
        self.radUseCurrent.setChecked(False)
        self.goout = False
        self.UseCurrentRaster = False
        self.fil = ''
        #
        # Ask user for the qml or colour table file
        self.fil = QFileDialog.getOpenFileName(self,
                            "Open a colour table or QML file", self.tbPath,
                            "Colour table files (*.txt *.qml);;All files (*.*)")
        #
        if str(self.fil) != "":
            # Set provided file as source
            self.SetTableFile(self.fil)
        else:
            # Reset to default
            self.btnEntry.setText('Click to select a colour table (*.txt) or a QGIS properties file (*.qml)')

#-------------------------------------------------------------------------------

    def SetCurRaster(self):
        """ Flag to use selected raster """
        #
        # Do not re-enter while in the routine
        if self.goout: return
        self.goout=True
        #
        # Delete temp qml file (if it exist)
        try:
            if self.UseCurrentRaster and self.fil != '':
                os.remove(self.fil)
                self.UseCurrentRaster = False
        except:
            pass
        #
        if self.radUseCurrent.isChecked():
            #Check that the current layer is a one-band raster
            [flg, theLayer] = uu.checkOneBandLayer(self.iface)
            if flg:
                # Yes: try to save a temp qml file
                [flg, theQML] = uu.saveQML(self.iface, theLayer)
                if flg:
                    # Success
                    self.SetTableFile(theQML)
                    self.fil = theQML
                else:
                    # cannot create temp file: complain to the user
                    QMessageBox.critical(self,info.MSG_BOX_TITLE, "Cannot use current raster! Load a QML or colour table.")
                self.UseCurrentRaster = flg
            else:
                # No: complain to the user
                QMessageBox.critical(self,info.MSG_BOX_TITLE, theLayer)
                self.UseCurrentRaster = False
                self.radUseCurrent.setChecked(False)
        else:
            self.UseCurrentRaster = False
        #
        if not self.UseCurrentRaster:
            self.btnEntry.setText('Click to select a colour table (*.txt) or a QGIS properties file (*.qml)')
            self.fil = ''
        self.goout = False
#-------------------------------------------------------------------------------

    def SetTableFile(self, theFile):
        """ save the file name of the colour table to act on """
        #
        self.btnEntry.setText(str(theFile))
        (self.tbPath, d) = os.path.split(str(theFile))
        try:
           self.settings.setValue("bccBar/pathTB", "")
        finally:
           if self.tbPath:
               self.settings.setValue("bccBar/pathTB", self.tbPath)
#-------------------------------------------------------------------------------

    def SelDir(self):
        """ Select the output folder """
        #
        selFLD = QFileDialog.getExistingDirectory(self,
                                                  "Select output folder",
                                                  self.myPath)
        self.myPath = str(selFLD)
        try:
           self.settings.setValue("bccBar/pathIM", "")
        finally:
           if self.myPath:
               self.settings.setValue("bccBar/pathIM", self.myPath)
#-------------------------------------------------------------------------------

    def SetBox1(self):
        """ Set the default box size, if none is given """
        #
        if self.txtW.text() == '': self.txtW.setText('20')
        if self.txtH.text() == '': self.txtH.setText('1')
#-------------------------------------------------------------------------------

    def SetBox2(self):
        """ Set the default box size, if none is given """
        #
        if self.txtW.text() == '': self.txtW.setText('1')
        if self.txtH.text() == '': self.txtH.setText('20')
#-------------------------------------------------------------------------------

    def helpme(self):
        """ Display a help message about how to use the plugin"""
        #
        QMessageBox.about(self,info.MSG_BOX_TITLE,info.Usage())
#-------------------------------------------------------------------------------

    def reject(self):
        """ Exit plugin """
        #
        # Delete temp file if it exists
        try:
            if self.UseCurrentRaster:
                os.remove(self.fil)
        except:
            pass
        #
        # Get out of plugin
        super(cdlgSCBR, self).reject()
#
#===============================================================================