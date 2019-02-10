# -*- coding: utf-8 -*-
#
# Colour Scale Bar (c) BC Consulting 2011 - (c) GeoProc 2019
#
#  modified by Thomas Wahlmüller (c) 2012-03-07
#  contact: thomas dot wahlmueller at gmx dot net
#  Added support for INTERPOLATED and EXACT styles. Annotate extrema
#  is ignored when interpolated. At least two ticks (extrema) are
#  displayed. EXACT style uses same visualisation as discrete.
#  + Added two functions scalebarVertical, scalebarHorizontal
#    better display of Interpolated colors.
#    Functions are based on scV, scH and could also be used with discrete and exact styles.
#    Ignores Annoted extrema option. Extrema have allways a tick (at least 2 ticks are in the scalebar).
#  + Modified ReadTableFile, GetFromTBL, GetFromQML to support linear and exact styles
#    Returns mode: 0=discrete style, 1=linear interpolated style, 2=exact style
#  + Added import info to generate warning, if only one tick is checked
#    may be exported to check in user interface
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
import tempfile
#import sys
#import string
import math
import numpy as np
import info

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *

from qgis.core import *
import qgis.utils
#
#===============================================================================
#    Utilities functions
#
class storeVar():
    def __init__(self):
        """ Stores needed to construct a colour scale bar.
            This info comes from either the QGIS dialog box
            or the standalone app.
        """
        self.txtDeci    = 4
        self.bEnforce   = False
        self.scTitle    = ''
        self.scUnits    = ''
        self.scFontSize = 14
        self.bH         = False
        self.bV         = False
        self.bAuto      = True
        self.nbTicks    = -1
        self.boxW       = 0
        self.boxH       = 0
        self.doExtrema  = False
        self.mini       = ' '

    def __str__(self):
        """ Return the string representation of storeVar """
        return  "txtDeci    : "+str(self.txtDeci   )+"\n" \
                "bEnforce   : "+str(self.bEnforce  )+"\n" \
                "scTitle    : "+str(self.scTitle   )+"\n" \
                "scUnits    : "+str(self.scUnits   )+"\n" \
                "scFontSize : "+str(self.scFontSize)+"\n" \
                "bH         : "+str(self.bH        )+"\n" \
                "bV         : "+str(self.bV        )+"\n" \
                "bAuto      : "+str(self.bAuto     )+"\n" \
                "nbTicks    : "+str(self.nbTicks   )+"\n" \
                "boxW       : "+str(self.boxW      )+"\n" \
                "boxH       : "+str(self.boxH      )+"\n" \
                "doExtrema  : "+str(self.doExtrema )+"\n" \
                "mini       : "+str(self.mini      )+"\n"
#
#===============================================================================
#
def GetL(d, n, bEnforce):
    """
    Format a number

    d       : number to format
    n       : number of decimal places
    bEnforce: True will force the number of decimals to be 'n', adding 0s if
              necessary
    """
    if int(n) == 0:
        L = str(int(round(float(d))))
    else:
        L = ("%.*f" % (int(n),float(d)))
        if not bEnforce: L = L.rstrip("0")
    if L[-1] == ".": L = L[:-1]
    return " " + L                                                              #V0.2.1 added " "
#
#===============================================================================
#
class scalebarVerticalDiscreteAnnotation(QWidget):
    def __init__(self, nC, arColo, arV, md, fileIN, outPTH, parent=None):
        """
        Create and save a vertical scale bar

        nC:       number of colours in array arColo()
        arColo(): R, G, B values
        arV():    real life value
        md:       all info from dialog box
        fileIN:   image file to save to (PNG format)

        We use a trick in here because Qt's painter cannot display text outside
        of a paintEvent() event!
        We thus create a dummy widget and call its paintEnvent() function on
        creation!
        """
        super(scalebarVerticalDiscreteAnnotation, self).__init__(parent)
        self.nC     = nC
        self.arColo = arColo
        self.arV    = arV
        self.md     = md
        self.fileIN = fileIN
        self.myPath = outPTH
        [b, self.LcolFile] = self.paintEvent()
        if not b: self.LcolFile = ""

    def retrieveFile(self):
        return self.LcolFile

    def paintEvent(self, event=None):
        nC       = int(self.nC)
        arColo   = self.arColo
        arV      = self.arV
        md       = self.md
        offset   = int(md.boxH)
        fileIN   = str(self.fileIN)
        myPTH    = str(self.myPath)
        LcolFile = ""
        #
        # We start by finding the minimum dimension of the final scale bar
        # in order to do that we create a dummy painting device and
        # compute the total height and width of all elements to be put in
        # the scale bar: title, unit, ticks annotations & colour boxes.
        #
        hi = 0    #height of block enclosing title + unit lines
        wi = 0    #width of block enclosing title + unit lines
        wl = 0    # max number of chars of ticks annotations
        wt = 0    # width of the longest ticks annotation
        jt = 0    # height of a tick annotation, also bottom margin
        ht = 0    # total Height of the image
        pw = 0    # total Width of the image
        LT = ''
        LU = ''
        #
        myIMG = QImage(500,2000,QImage.Format_RGB32)
        myIMG.fill(0)
        #
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        myBrush = QBrush()
        myBrush.setColor(QColor("white"))
        myP.setBackground(myBrush)
        myP.setBrush(QColor("black"))
        myP.setPen(QColor("black"))
        #
        # set text properties for ticks annotations (user defined)
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        myP.setFont(myFNT)
        fm = QFontMetricsF(myFNT)
#        hh = fm.height()
        #
        if str(md.scTitle) != "":
            # title properties (fixed by plugin)
            LT = str(md.scTitle)
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
            wi = fm.boundingRect(str(LT)).width()
            if LT.find("\n") >= 0:
                # multilines title
                hi = hi * (LT.count("\n")+1)
                #split LT on \n and compute max width of components
                L = LT.split("\n")
                wi = 0
                for q in L:
                    wi = max(wi, fm.boundingRect(str(q)).width())
        else:
            LT = ""
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
		#
        L = None
        if str(md.scUnits) != "":
            # unit properties (fixed by plugin)
            LU = str(md.scUnits)
            if LU.find("\n") >= 0:
                L = LU.split()
                LU = L[0]
            LU = LU.strip()
            if LU !='' and LU[0] != "(":
                #Put unit between () if not already done
                LU = "(" + LU + ")"
            #
            if LU != '':
                myFNT.setPointSize(int(md.scFontSize))
                myFNT.setBold( False )
                myP.setFont(myFNT)
                fm = QFontMetricsF(myFNT)
                hi += fm.boundingRect(str(LU)).height() + 12
                wi = max(fm.boundingRect(str(LU)).width(), wi)
        #
        #Define necessary space to plot the scale bar with its ticks and title
        #maximum tick value length in pixels
        for i in range(nC):
            L = GetL(arV[i], md.txtDeci, md.bEnforce)
            if wl < len(L): wl = len(L)
        #
        # width of the longest annotation
        wt = fm.boundingRect(str("0" * wl)).width()
        #
#        vmini = ""
        if bool(md.doExtrema):
            if str(md.mini).isdigit():
                vmin = GetL(md.mini, md.txtDeci, md.bEnforce)
            else:
                vmin = str(md.mini)
            i = fm.boundingRect(str(vmin)).width()
            if i > wt: wt = i
        #
            v = GetL(arV[nC-1], md.txtDeci, md.bEnforce)
            i = fm.boundingRect(str(v)).width()
            if i > wt: wt = i
        #
        # Height of a tick annotation
        jt = fm.boundingRect("Qq").height()
        #
        # Remove dummy painter
        myFNT=''
        myP.end()
        myIMG = ''
        #
        #------------------------- Start painting now --------------------------
        #
        # Total Height of the image
        jt /= 2
        ht = int(md.boxH) * (nC +1) + jt + hi
        if bool(md.doExtrema): ht += jt
        #
        # total width of image
        wa = int(md.boxW) + 12 + wt  # width of box + tick + annotation
        pw = max(wi, wa) +1
        #
        if wi > wa:  goff = float(wi - wa) / 2.0
        else:        goff = 1.0
        #
        # Create a new QImage of the correct size and draw the scale bar on it
        myIMG = QImage(pw,ht,QImage.Format_RGB32)
        mc = QColor(255,255,255)
        myIMG.fill(mc.rgb())
        # create a new QPainter for the QImage
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        # set text properties
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        fm = QFontMetricsF(myFNT)
        myP.setFont(myFNT)
        myP.setRenderHint(QPainter.TextAntialiasing)
        # Colour bar
        for i in range(nC):
            colo = QColor(arColo[0, i], arColo[1, i], arColo[2, i])
            myP.setBrush(colo)
            myP.setPen(colo)
            h = ht - int(md.boxH) * i - jt
            myP.drawRect(pw-goff, h - int(md.boxH), -int(md.boxW), int(md.boxH))
        colo = QColor(0,0,0,255)
        myP.setBrush(QColor(0,0,0,0))
        myP.setPen(colo)
        # bounding rectangle
        y0 = ht - float(md.boxH)*(nC-1) -jt -offset
        myP.drawRect(pw-goff, y0, -int(md.boxW)-1, int(md.boxH)*nC)
        #
        # Tick annotations
        #
        # The first (lowest) data value of the colour table is not the minimum
        # value in the dataset. It is the upper value of the first class. This
        # means that the lowest value in the dataset is not known and must be
        # given by the user. This also means that the first value in the colour
        # table must be displayed on top of the first (bottom) colour block.
        #
        if bool(md.bAuto):
            # Automatic
            j = (int(md.boxH) * nC) / jt
            if j == 0: j = 1
            else:      j = int(round(nC / j)) + 1
        else:
            # User provides the number of ticks to use
            j = nC / (int(md.nbTicks)-1)
            if j == 0: j = 1
        #
        L0 = " " * wl
        bTop = True
        mPtF  = QPointF()
        for i in range(0,nC,j):
            i0    = ht - int(md.boxH) * i - jt
            v     = GetL(arV[i], md.txtDeci, md.bEnforce)
            y     = i0 + fm.height() / 2.0 - offset
            y1    = i0 - offset
            xx    = pw - int(md.boxW) -goff
            if int(round(y1-0.5)) < y0: break
            if i == (nC-1): bTop = False
            #
            text  = (L0 + str(v))[-wl:]
            nRect = fm.boundingRect(str(text))
            rectf = QRectF(nRect)
            mPtF.setX(float(pw - int(md.boxW) -12 -goff))
            mPtF.setY(float(y))
            rectf.moveBottomRight(mPtF)
            myP.drawText(rectf, Qt.AlignRight, str(text))       # annotation
            myP.drawLine(xx -2, y1, xx -9, y1)                      # tick
        #
        if bool(md.doExtrema):
            xx = pw - int(md.boxW) -goff
            #bottom extremum
            if str(vmin).strip() != "":
                text  = str(GetL(vmin, md.txtDeci, md.bEnforce))
                nRect = fm.boundingRect(text)
                rectf = QRectF(nRect)
                mPtF.setX(float(pw -int(md.boxW) - 12))
                y  = ht - jt
                mPtF.setY(float(y + fm.height() / 2.0))
                rectf.moveBottomRight(mPtF)
                myP.drawText(rectf, Qt.AlignRight, text)
                myP.drawLine(xx -2, y, xx -9, y)
            #
            if bTop:
                #top extremum
                v     = GetL(arV[nC-1], md.txtDeci, md.bEnforce)
                text  = (L0 + str(v))[-wl:]
                nRect = fm.boundingRect(str(text))
                rectf = QRectF(nRect)
                mPtF.setX(float(pw -int(md.boxW) - 12))
                mPtF.setY(float(y0 + fm.height() / 2.0))
                rectf.moveBottomRight(mPtF)
                myP.drawText(rectf, Qt.AlignRight, str(text))
                myP.drawLine(xx -2, y0, xx -9, y0)
        #
        #Title
        h  = 0
        fm = None
        if LT != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LT)
            nRect = fm.boundingRect(str(text))
            if text.find("\n") >= 0:
                nRect.setHeight(nRect.height() * (text.count("\n")+1))
            rectf = QRectF(nRect)
            ww    = nRect.width()
            h     = nRect.height()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(h))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, str(text))
        #Units
        fm = None
        if LU != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LU)
            nRect = fm.boundingRect(str(text))
            rectf = QRectF(nRect)
            ww    = nRect.width()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(hi - 12))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, str(text))
        #
        # Finally save image
        if myPTH != "":
            (theDir, theFile) = os.path.split(fileIN)
            leFile = os.path.join(myPTH, theFile)
        else:
            leFile = fileIN
        (theFile,theExt) = os.path.splitext(leFile)
        LcolFile = theFile + "_Vscalebar.png"
        myIMG.save(LcolFile)
        myFNT=''
        myP.end()
        myIMG = ''
        #
        return [True, LcolFile]
#
#===============================================================================
#
class scalebarHorizontalDiscreteAnnotation(QWidget):
    def __init__(self, nC, arColo, arV, md, fileIN, outPTH, parent=None):
        """
        Create and save a horizontal scale bar

        nC:       number of colours in array arColo()
        arColo(): R, G, B values
        arV():    real life value
        md:       all info from dialog box
        fileIN:   image file to save to (PNG format)

        We use a trick in here because Qt's painter cannot display text outside
        of a paintEvent() envent!
        We thus create a dummy widget and call its paintEnvent() function on
        creation!
        """
        super(scalebarHorizontalDiscreteAnnotation, self).__init__(parent)
        self.nC     = nC
        self.arColo = arColo
        self.arV    = arV
        self.md     = md
        self.fileIN = fileIN
        self.myPath = outPTH
        [b, self.LcolFile] = self.paintEvent()
        if not b: self.LcolFile = ""

    def retrieveFile(self):
        return self.LcolFile

    def paintEvent(self, event=None):
        LcolFile = ""
        #
        nC       = int(self.nC)
        arColo   = self.arColo
        arV      = self.arV
        md       = self.md
        offset   = int(md.boxW)
        fileIN   = str(self.fileIN)
        myPTH    = str(self.myPath)
        LcolFile = ""
        LT       = ''
        LU       = ''
        vmin     = ''
        #
        # We start by finding the minimum dimension of the final scale bar
        # in order to do that we create a dummy painting device and
        # compute the total height and width of all elements to be put in
        # the scale bar: title, unit, ticks annotations & colour boxes.
        #
        hi = 0    #height of block enclosing title + unit lines
        wi = 0    #width of block enclosing title + unit lines
        wl = 0    # max number of chars of ticks annotations
        wt = 0    # width of the longest ticks annotation
        jt = 0    # height of a tick annotation
        ht = 0    # total Height of the image
        pw = 0    # total Width of the image
        #
        myIMG = QImage(500,2000,QImage.Format_RGB32)
        myIMG.fill(0)
        #
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        myBrush = QBrush()
        myBrush.setColor(QColor("white"))
        myP.setBackground(myBrush)
        myP.setBrush(QColor("black"))
        myP.setPen(QColor("black"))
        #
        # set text properties for ticks annotations (user defined)
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        myP.setFont(myFNT)
        fm = QFontMetricsF(myFNT)
#        hh = fm.height()
        #
        if str(md.scTitle) != "":
            # title properties (fixed by plugin)
            LT = str(md.scTitle)
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
            wi = fm.boundingRect(str(LT)).width()
            if LT.find("\n") >= 0:
                # multilines title
                hi = hi * (LT.count("\n")+1)
                #split LT on \n and compute max width of components
                L = LT.split("\n")
                for q in L:
                    wi = max(wi, fm.boundingRect(str(q)).width())
        else:
            LT = ""
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
        #
        L = None
        if str(md.scUnits) != "":
            # unit properties (fixed by plugin)
            LU = str(md.scUnits)
            if LU.find("\n") >= 0:
                L = LU.split()
                LU = L[0]
            LU = LU.strip()
            if LU !='' and LU[0] != "(":
                #Put unit between () if not already done
                LU = "(" + LU + ")"
            #
            if LU != '':
                myFNT.setPointSize(int(md.scFontSize))
                myFNT.setBold( False )
                myP.setFont(myFNT)
                fm = QFontMetricsF(myFNT)
                hi += fm.boundingRect(str(LU)).height() + 12
                wi = max(fm.boundingRect(str(LU)).width(), wi)
        wi += fm.boundingRect("WW").width()
        wun = fm.boundingRect("0").width()
        #
        #Define necessary space to plot the scale bar with its ticks and title
        #maximum tick value length in pixels
        for i in range(nC):
            L = str(GetL(arV[i], md.txtDeci, md.bEnforce))
            if wl < len(L): wl = len(L)
        #
        # width of the longest annotation
        wt = fm.boundingRect(str("0" * wl)).width()
        #
#        vmini = ""
        if bool(md.doExtrema):
            if str(md.mini).isdigit():
                vmin = GetL(md.mini, md.txtDeci, md.bEnforce)
            else:
                vmin = str(md.mini)
            i = fm.boundingRect(str(vmin)).width()
            if i > wt: wt = i
        #
            v = GetL(arV[nC-2], md.txtDeci, md.bEnforce)
            i = fm.boundingRect(str(v)).width()
            if i > wt: wt = i
        wt += 4  # need 2 blank pixels on each side
        #
        # Height of a tick annotation
        jt = fm.boundingRect("Qq").height()
        #
        # Remove dummy painter
        myFNT=''
        myP.end()
        myIMG = ''
        #
        #------------------------- Start painting now --------------------------
        #
        #Total Height of the image
        ht = int(md.boxH) + jt + hi + 13  # tick height = 9 space = 4
        #Total width of image
        wa = float(wt + int(md.boxW) * nC)  # width of the colour box
        pw = max(wi, wa) +wun +1            # total width of the plot
        x0 = 0.0                            # left coordinate of the colour box
        #
        if bool(md.doExtrema):
            # extrema are plotted 'outside' the colour box
            #        |========================|
            #        |                        |
            # minvalue                        maxvalue
            #
            if (wi < wa+wt): pw += wt
            x0 = float(wt) + float(wun) / 2.0
        else:
            pw -= wt / 2.0
            x0 = float(wt + wun) / 2.0
        #
        #goff: centre box relative to title
        if wi > wa: goff = float(wi - wa) / 2.0        # title wider than box
        else:                                          # box wider than title
            if bool(md.doExtrema):
                goff = 0.0
            else:
                goff = -float(pw - (int(md.boxW)*nC)) / 2.0
        x0 += goff
        #
        # Create a new QImage of the correct size and draw the scale bar on it
        myIMG = QImage( pw, ht, QImage.Format_RGB32 )
        mc = QColor( 255, 255, 255 )
        myIMG.fill( mc.rgb() )
        # create a new QPainter for the QImage
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        # set text properties
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        fm = QFontMetricsF(myFNT)
        myP.setFont(myFNT)
        myP.setRenderHint(QPainter.TextAntialiasing)
        # Colour bar
        y0 = ht - int(md.boxH) - jt - 13
        for i in range(nC):
            colo = QColor(arColo[0, i], arColo[1, i], arColo[2, i])
            myP.setBrush(colo)
            myP.setPen(colo)
            x = x0 + int(md.boxW) * i
            myP.drawRect(x, y0, int(md.boxW) , int(md.boxH))
        colo = QColor(0,0,0,255)
        myP.setBrush(QColor(0,0,0,0))
        myP.setPen(colo)
        # bounding rectangle
        myP.drawRect(x0, y0, int(md.boxW)*nC, int(md.boxH))
        mPtF  = QPointF()
        #
        # Tick annotations
        #
        # The first (lowest) data value of the colour table is not the minimum
        # value in the dataset. It is the upper value of the first class. This
        # means that the lowest value in the dataset is not known and must be
        # given by the user. This also means that the first value in the colour
        # table must be displayed at the right of the first (left) colour block.
        #
        # need to find the number of colours a full tick annotation represents
        if wt < int(md.boxW):
            nnn = 1
        else:
            nnn = int(wt / int(md.boxW)) + 1
        # first tick
        if bool(md.doExtrema) and str(vmin).strip() != "": i0 = nnn
        else:                                              i0 = 0
        #
        if md.bAuto:
            # Automatic
            if wt < int(md.boxW): j = 1
            else:
                 j = int(round(float(md.boxW)*(nC-i0) / wt))
                 if j == 0: j = 1
                 else: j = (nC-i0) / j
        else:
            # User provides the number of ticks to use
            j = int(round(float(nC-i0) / (float(md.nbTicks)-1)))
            if j == 0: j = 1
        #
#        L0   = " " * wl
        bTop = True
        y    = y0 + int(md.boxH)
        yoff = 13.0 + fm.boundingRect("0").height() / 2.0
        xx0  = x0 + offset
        #
        for i in range(i0,nC-1,j):
            v  = str(GetL(arV[i], md.txtDeci, md.bEnforce))
            x  = xx0 + int(md.boxW) * i
            if i == (nC-2): bTop = False
            #
            text  = str(v)
            nRect = fm.boundingRect(text)
            rectf = QRectF(nRect)
            mPtF.setX(float(x))
            mPtF.setY(float(y + yoff))
            rectf.moveCenter(mPtF)
            myP.drawText(rectf, Qt.AlignRight, text)       # annotation
            myP.drawLine(x, y, x, y+9)                     # tick
        #
        if (x + float(wt/2.0) + 5) < (xx0 + int(md.boxW) * (nC-1) - float(wt/2.0)):
            v  = str(GetL(arV[nC-2], md.txtDeci, md.bEnforce))
            x  = xx0 + int(md.boxW) * (nC-1) -2
            bTop = False
            #
            text  = str(v)
            nRect = fm.boundingRect(text)
            rectf = QRectF(nRect)
            mPtF.setX(float(x))
            mPtF.setY(float(y + yoff))
            rectf.moveCenter(mPtF)
            myP.drawText(rectf, Qt.AlignRight, text)       # annotation
            myP.drawLine(x, y, x, y+9)                     # tick
        #
        if bool(md.doExtrema):
            yoff = 13 + fm.boundingRect("0").height()
            #bottom extremum
            if str(vmin).strip() != "":
                text  = str(GetL(vmin, md.txtDeci, md.bEnforce))
                nRect = fm.boundingRect(text)
                rectf = QRectF(nRect)
                mPtF.setX(float(x0))
                mPtF.setY(float(y + yoff))
                rectf.moveBottomRight(mPtF)
                myP.drawText(rectf, Qt.AlignRight, text)
                myP.drawLine(x0, y, x0, y+9)
            #
            if bTop:
                #top extremum
                text  = str(GetL(arV[nC-2], md.txtDeci, md.bEnforce))
                nRect = fm.boundingRect(text)
                rectf = QRectF(nRect)
                x = x0 + int(md.boxW)*nC
                mPtF.setX(float(x))
                mPtF.setY(float(y + yoff))
                rectf.moveBottomLeft(mPtF)
                myP.drawText(rectf, Qt.AlignRight, text)
                myP.drawLine(x, y, x, y+9)
        #
        #Title
        h  = 0
        fm = None
        if LT != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LT)
            nRect = fm.boundingRect(str(text))
            if text.find("\n") >= 0:
                nRect.setHeight(nRect.height() * (text.count("\n")+1))
            rectf = QRectF(nRect)
            ww    = nRect.width()
            h     = nRect.height()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(h))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, str(text))
        #Units
        fm = None
        if LU != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LU)
            nRect = fm.boundingRect(text)
            rectf = QRectF(nRect)
            ww    = nRect.width()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(hi-12))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, text)
        #
        # Finally save image
        if myPTH != "":
            (theDir, theFile) = os.path.split(fileIN)
            leFile = os.path.join(myPTH, theFile)
        else:
            leFile = fileIN
        (theFile,theExt) = os.path.splitext(leFile)
        LcolFile = theFile + "_Hscalebar.png"
        myIMG.save(LcolFile)
        myFNT=''
        myP.end()
        myIMG = ''
        #
        return [True, LcolFile]
#
#===============================================================================
#
class scalebarVerticalInterpolatedAnnotation(QWidget):
    def __init__(self, nC, arColo, arV, md, fileIN, outPTH, parent=None):
        """
        Create and save a vertical scale bar

        nC:       number of colours in array arColo()
        arColo(): R, G, B values
        arV():    real life value
        md:       all info from dialog box
        fileIN:   image file to save to (PNG format)

        We use a trick in here because Qt's painter cannot display text outside
        of a paintEvent() event!
        We thus create a dummy widget and call its paintEnvent() function on
        creation!
        """
        super(scalebarVerticalInterpolatedAnnotation, self).__init__(parent)
        self.nC     = nC
        self.arColo = arColo
        self.arV    = arV
        self.md     = md
        self.fileIN = fileIN
        self.myPath = outPTH
        [b, self.LcolFile] = self.paintEvent()
        if not b: self.LcolFile = ""

    def retrieveFile(self):
        return self.LcolFile

    def paintEvent(self, event=None):
        nC       = int(self.nC)
        arColo   = self.arColo
        arV      = self.arV
        md       = self.md
        offset   = int(md.boxH)
        fileIN   = str(self.fileIN)
        myPTH    = str(self.myPath)
        LcolFile = ""

        #
        # We start by finding the minimum dimension of the final scale bar
        # in order to do that we create a dummy painting device and
        # compute the total height and width of all elements to be put in
        # the scale bar: title, unit, ticks annotations & colour boxes.
        #
        hi = 0    #height of block enclosing title + unit lines
        wi = 0    #width of block enclosing title + unit lines
        wl = 0    # max number of chars of ticks annotations
        wt = 0    # width of the longest ticks annotation
        jt = 0    # height of a tick annotation, also bottom margin
        ht = 0    # total Height of the image
        pw = 0    # total Width of the image
        LT = ''
        LU = ''
        #
        myIMG = QImage(500,2000,QImage.Format_RGB32)
        myIMG.fill(0)
        #
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        myBrush = QBrush()
        myBrush.setColor(QColor("white"))
        myP.setBackground(myBrush)
        myP.setBrush(QColor("black"))
        myP.setPen(QColor("black"))
        #
        # set text properties for ticks annotations (user defined)
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        myP.setFont(myFNT)
        fm = QFontMetricsF(myFNT)
#        hh = fm.height()
        #
        if str(md.scTitle) != "":
            # title properties (fixed by plugin)
            LT = str(md.scTitle)
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
            wi = fm.boundingRect(str(LT)).width()
            if LT.find("\n") >= 0:
                # multilines title
                hi = hi * (LT.count("\n")+1)
                #split LT on \n and compute max width of components
                L = LT.split("\n")
                wi = 0
                for q in L:
                    wi = max(wi, fm.boundingRect(str(q)).width())
        else:
            LT = ""
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
        #
        L = None
        if str(md.scUnits) != "":
            # unit properties (fixed by plugin)
            LU = str(md.scUnits)
            if LU.find("\n") >= 0:
                L = LU.split()
                LU = L[0]
            LU = LU.strip()
            if LU !='' and LU[0] != "(":
                #Put unit between () if not already done
                LU = "(" + LU + ")"
            #
            if LU != '':
                myFNT.setPointSize(int(md.scFontSize))
                myFNT.setBold( False )
                myP.setFont(myFNT)
                fm = QFontMetricsF(myFNT)
                hi += fm.boundingRect(str(LU)).height() + 12
                wi = max(fm.boundingRect(str(LU)).width(), wi)
        #
        #Define necessary space to plot the scale bar with its ticks and title
        #maximum tick value length in pixels
        for i in range(nC):
            L = GetL(arV[i], md.txtDeci, md.bEnforce)
            if wl < len(L): wl = len(L)
        #
        # width of the longest annotation
        wt = fm.boundingRect(str("0" * wl)).width()
        #
        #
        # Height of a tick annotation
        jt = fm.boundingRect("Qq").height()
        #
        # Remove dummy painter
        myFNT=''
        myP.end()
        myIMG = ''
        #
        #------------------------- Start painting now --------------------------
        #
        # Total Height of the image
        jt /= 2
        ht = int(md.boxH) * (nC +1) + jt + hi
        #
        # total width of image
        wa = int(md.boxW) + 12 + wt  # width of box + tick + annotation
        pw = max(wi, wa) +1
        #
        if wi > wa:  goff = float(wi - wa) / 2.0
        else:        goff = 1.0
        #
        # Create a new QImage of the correct size and draw the scale bar on it
        myIMG = QImage(pw,ht,QImage.Format_RGB32)
        mc = QColor(255,255,255)
        myIMG.fill(mc.rgb())
        # create a new QPainter for the QImage
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        # set text properties
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        fm = QFontMetricsF(myFNT)
        myP.setFont(myFNT)
        myP.setRenderHint(QPainter.TextAntialiasing)
        # Colour bar
        for i in range(nC):
            colo = QColor(arColo[0, i], arColo[1, i], arColo[2, i])
            myP.setBrush(colo)
            myP.setPen(colo)
            h = ht - int(md.boxH) * i - jt
            myP.drawRect(pw-goff, h - int(md.boxH), -int(md.boxW), int(md.boxH))
        colo = QColor(0,0,0,255)
        myP.setBrush(QColor(0,0,0,0))
        myP.setPen(colo)
        # bounding rectangle
        y0 = ht - float(md.boxH)*(nC-1) -jt -offset
        myP.drawRect(pw-goff, y0, -int(md.boxW)-1, int(md.boxH)*nC)
        #
        # Tick annotations
        #
        # The first (lowest) data value of the colour table is not the minimum
        # value in the dataset. It is the upper value of the first class. This
        # means that the lowest value in the dataset is not known and must be
        # given by the user. This also means that the first value in the colour
        # table must be displayed on top of the first (bottom) colour block.
        #
        #
        # EXTREMA are allways annotated, Annotate extrema has no effects
        #
        if nC < 2:
            return [FALSE,"At least two colors need to be specified in file to annotate interpolated color bar!"]
        if md.bAuto:
            #Automatic Tick estimation: Vertical Scalebar --> Height
            if jt < int(md.boxH): nTicks=nC
            else:
                nTicks = int(round(float(md.boxH)*nC / jt))
                if nTicks <= 1:
                    nTicks = 2
        else:
            nTicks = int(md.nbTicks)
            #Do not generate more ticks than colors!
            if nTicks > nC: nTicks = nC
        #At least two ticks are needed to interpret linear data
        if nTicks <= 1:
            nTicks = 2
            QMessageBox.information(self, \
                                 info.MSG_BOX_TITLE, \
                                 "Less than two ticks is not possible! Changed number of ticks to 2!")
        #
        #
        #Calculate Step Width
        nStepWidth = float(nC) / float(nTicks-1)
        #
        L0 = " " * wl
        mPtF = QPointF()
        #
        for i in range(nTicks):
            if i == nTicks-1 or math.ceil(i*nStepWidth) >=nC:
                v  = str(GetL(arV[nC], md.txtDeci, md.bEnforce))
                i0    = ht - int(md.boxH) * nC - jt
            else:
                v  = str(GetL(arV[int(round(i*nStepWidth))], md.txtDeci, md.bEnforce))
                i0    = ht - int(md.boxH) * int(round(i*nStepWidth)) - jt
            #
            y     = i0 + fm.height() / 2.0
            y1    = i0
            xx    = pw - int(md.boxW) -goff
            #
            text  = (L0 + str(v))[-wl:]
            nRect = fm.boundingRect(str(text))
            rectf = QRectF(nRect)
            mPtF.setX(float(pw - int(md.boxW) -12 -goff))
            mPtF.setY(float(y))
            rectf.moveBottomRight(mPtF)
            myP.drawText(rectf, Qt.AlignRight, str(text))       # annotation
            myP.drawLine(xx -2, y1, xx -9, y1)                      # tick
            if math.ceil(i*nStepWidth) >=nC: break
        #
        #Title
        h  = 0
        fm = None
        if LT != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LT)
            nRect = fm.boundingRect(str(text))
            if text.find("\n") >= 0:
                nRect.setHeight(nRect.height() * (text.count("\n")+1))
            rectf = QRectF(nRect)
            ww    = nRect.width()
            h     = nRect.height()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(h))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, str(text))
        #Units
        fm = None
        if LU != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LU)
            nRect = fm.boundingRect(text)
            rectf = QRectF(nRect)
            ww    = nRect.width()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(hi - 12))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, text)
        #
        # Finally save image
        if myPTH != "":
            (theDir, theFile) = os.path.split(fileIN)
            leFile = os.path.join(myPTH, theFile)
        else:
            leFile = fileIN
        (theFile,theExt) = os.path.splitext(leFile)
        LcolFile = theFile + "_Vscalebar.png"
        myIMG.save(LcolFile)
        myFNT=''
        myP.end()
        myIMG = ''
        #
        return [True, LcolFile]
#
#===============================================================================
#
class scalebarHorizontalInterpolatedAnnotation(QWidget):
    def __init__(self, nC, arColo, arV, md, fileIN, outPTH, parent=None):
        """
        Create and save a horizontal scale bar

        nC:       number of colours in array arColo()
        arColo(): R, G, B values
        arV():    real life value
        md:       all info from dialog box
        fileIN:   image file to save to (PNG format)

        We use a trick in here because Qt's painter cannot display text outside
        of a paintEvent() envent!
        We thus create a dummy widget and call its paintEnvent() function on
        creation!
        """
        super(scalebarHorizontalInterpolatedAnnotation, self).__init__(parent)
        self.nC     = nC
        self.arColo = arColo
        self.arV    = arV
        self.md     = md
        self.fileIN = fileIN
        self.myPath = outPTH
        [b, self.LcolFile] = self.paintEvent()
        if not b: self.LcolFile = ""

    def retrieveFile(self):
        return self.LcolFile

    def paintEvent(self, event=None):
        LcolFile = ""
        #
        nC       = int(self.nC)
        arColo   = self.arColo
        arV      = self.arV
        md       = self.md
        offset   = 0
        fileIN   = str(self.fileIN)
        myPTH    = str(self.myPath)
        LcolFile = ""
        LT = ''
        LU = ''
        vmin     = ''
        #
        # We start by finding the minimum dimension of the final scale bar
        # in order to do that we create a dummy painting device and
        # compute the total height and width of all elements to be put in
        # the scale bar: title, unit, ticks annotations & colour boxes.
        #
        hi = 0    #height of block enclosing title + unit lines
        wi = 0    #width of block enclosing title + unit lines
        wl = 0    # max number of chars of ticks annotations
        wt = 0    # width of the longest ticks annotation
        jt = 0    # height of a tick annotation
        ht = 0    # total Height of the image
        pw = 0    # total Width of the image
        #
        myIMG = QImage(500,2000,QImage.Format_RGB32)
        myIMG.fill(0)
        #
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        myBrush = QBrush()
        myBrush.setColor(QColor("white"))
        myP.setBackground(myBrush)
        myP.setBrush(QColor("black"))
        myP.setPen(QColor("black"))
        #
        # set text properties for ticks annotations (user defined)
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        myP.setFont(myFNT)
        fm = QFontMetricsF(myFNT)
#        hh = fm.height()
        #
        if str(md.scTitle) != "":
            # title properties (fixed by plugin)
            LT = str(md.scTitle)
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
            wi = fm.boundingRect(str(LT)).width()
            if LT.find("\n") >= 0:
                # multilines title
                hi = hi * (LT.count("\n")+1)
                #split LT on \n and compute max width of components
                L = LT.split("\n")
                wi = 0
                for q in L:
                    wi = max(wi, fm.boundingRect(str(q)).width())
        else:
            LT = ""
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
        #
        L = None
        if str(md.scUnits) != "":
            # unit properties (fixed by plugin)
            LU = str(md.scUnits)
            if LU.find("\n") >= 0:
                L = LU.split()
                LU = L[0]
            LU = LU.strip()
            if LU !='' and LU[0] != "(":
                #Put unit between () if not already done
                LU = "(" + LU + ")"
            #
            if LU != '':
                myFNT.setPointSize(int(md.scFontSize))
                myFNT.setBold( False )
                myP.setFont(myFNT)
                fm = QFontMetricsF(myFNT)
                hi += fm.boundingRect(str(LU)).height() + 12
                wi = max(fm.boundingRect(str(LU)).width(), wi)
        wi += fm.boundingRect("WW").width()
        wun = fm.boundingRect(" -0").width()
        #
        #Define necessary space to plot the scale bar with its ticks and title
        #maximum tick value length in pixels
        for i in range(nC):
            L = str(GetL(arV[i], md.txtDeci, md.bEnforce))
            if wl < len(L): wl = len(L)
        #
        # width of the longest annotation
        wt = fm.boundingRect(str("0" * wl)).width()
        #
        #
        # Height of a tick annotation
        jt = fm.boundingRect(str("Qq")).height()
        #
        # Remove dummy painter
        myFNT=''
        myP.end()
        myIMG = ''
        #
        #------------------------- Start painting now --------------------------
        #
        #Total Height of the image
        ht = int(md.boxH) + jt + hi + 13  # tick height = 9 space = 4
        #Total width of image
        wa = float(wt + int(md.boxW) * nC)
        pw = max(wi, wa) +wun +1
        #
        pw -= wt / 2.0
        x0 = float(wt + wun) / 2.0
        #
        #goff: centre box relative to title
        if wi > wa:  goff = float(wi - wa) / 2.0
        else:        goff = -float(pw-(wun*1.2) - (int(md.boxW)*nC)) / 2.0
        x0 += goff
        #
        # Create a new QImage of the correct size and draw the scale bar on it
        myIMG = QImage(pw,ht,QImage.Format_RGB32)
        mc = QColor(255,255,255)
        myIMG.fill(mc.rgb())
        # create a new QPainter for the QImage
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        # set text properties
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        fm = QFontMetricsF(myFNT)
        myP.setFont(myFNT)
        myP.setRenderHint(QPainter.TextAntialiasing)
        # Colour bar
        y0 = ht - int(md.boxH) - jt - 13
        for i in range(nC):
            colo = QColor(arColo[0, i], arColo[1, i], arColo[2, i])
            myP.setBrush(colo)
            myP.setPen(colo)
            x = x0 + int(md.boxW) * i
            myP.drawRect(x, y0, int(md.boxW) , int(md.boxH))
        colo = QColor(0,0,0,255)
        myP.setBrush(QColor(0,0,0,0))
        myP.setPen(colo)
        # bounding rectangle
        myP.drawRect(x0, y0, int(md.boxW)*nC, int(md.boxH))
        mPtF  = QPointF()
        #
        # Tick annotations
        #
        # The first (lowest) data value of the colour table is not the minimum
        # value in the dataset. It is the upper value of the first class. This
        # means that the lowest value in the dataset is not known and must be
        # given by the user. This also means that the first value in the colour
        # table must be displayed at the right of the first (left) colour block.
        #
        # EXTREMA are allways annotated, Annotate extrema has no effects
        #
        if nC < 2:
            return [FALSE,"At least two colors need to be specified in file to annotate interpolated color bar!"]
        if md.bAuto:
            #Automatic Tick estimation: Horizontal Scalebar --> Width
            if wt < int(md.boxW): nTicks=nC
            else:
                nTicks = int(round(float(md.boxW)*nC / wt))
                if nTicks < 2: nTicks = 2
        else:
            nTicks = int(md.nbTicks)
            if nTicks > nC: nTicks = nC
        #At least two ticks are needed to interpret linear data
        if nTicks <= 1:
            nTicks = 2
            QMessageBox.information(self, \
                                 info.MSG_BOX_TITLE, \
                                 "Less than two ticks is not possible! Changed number of ticks to 2!")
        #
        #
        #Calculate Step Width
        nStepWidth = float(nC) / float(nTicks-1)
        #
        L0 = " " * wl
        y  = y0 + int(md.boxH)
        yoff = 13.0 + fm.boundingRect("0").height() / 2.0
        #
        for i in range(nTicks):
            if i == nTicks-1 or math.ceil(i*nStepWidth)>=nC:
                v  = str(GetL(arV[nC], md.txtDeci, md.bEnforce))
                x  = x0 + offset + int(md.boxW) * nC
            else:
                v  = str(GetL(arV[int(round(i*nStepWidth))], md.txtDeci, md.bEnforce))
                x  = x0 + offset + int(md.boxW) * round(i*nStepWidth)
            #
            text  = str(v)
            nRect = fm.boundingRect(text)
            rectf = QRectF(nRect)
            mPtF.setX(float(x))
            mPtF.setY(float(y + yoff))
            rectf.moveCenter(mPtF)
            myP.drawText(rectf, Qt.AlignRight, text)       # annotation
            myP.drawLine(x, y, x, y+9)                     # tick
            if math.ceil(i*nStepWidth)>=nC: break
        #
        #Title
        h  = 0
        fm = None
        if LT != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LT)
            nRect = fm.boundingRect(str(text))
            if text.find("\n") >= 0:
                nRect.setHeight(nRect.height() * (text.count("\n")+1))
            rectf = QRectF(nRect)
            ww    = nRect.width()
            h     = nRect.height()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(h))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, str(text))
        #Units
        fm = None
        if LU != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LU)
            nRect = fm.boundingRect(text)
            rectf = QRectF(nRect)
            ww    = nRect.width()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(hi-12))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, text)
        #
        # Finally save image
        if myPTH != "":
            (theDir, theFile) = os.path.split(fileIN)
            leFile = os.path.join(myPTH, theFile)
        else:
            leFile = fileIN
        (theFile,theExt) = os.path.splitext(leFile)
        LcolFile = theFile + "_Hscalebar.png"
        myIMG.save(LcolFile)
        myFNT=''
        myP.end()
        myIMG = ''
        #
        return [True, LcolFile]
#
#===============================================================================
#
class scalebarVerticalExactAnnotation(QWidget):
    def __init__(self, nC, arColo, arV, md, fileIN, outPTH, parent=None):
        """
        Create and save a vertical scale bar

        nC:       number of colours in array arColo()
        arColo(): R, G, B values
        arV():    real life value
        md:       all info from dialog box
        fileIN:   image file to save to (PNG format)

        We use a trick in here because Qt's painter cannot display text outside
        of a paintEvent() event!
        We thus create a dummy widget and call its paintEnvent() function on
        creation!
        """
        super(scalebarVerticalExactAnnotation, self).__init__(parent)
        self.nC     = nC
        self.arColo = arColo
        self.arV    = arV
        self.md     = md
        self.fileIN = fileIN
        self.myPath = outPTH
        [b, self.LcolFile] = self.paintEvent()
        if not b: self.LcolFile = ""

    def retrieveFile(self):
        return self.LcolFile

    def paintEvent(self, event=None):
        nC       = int(self.nC)
        arColo   = self.arColo
        arV      = self.arV
        md       = self.md
        offset   = int(md.boxH)
        fileIN   = str(self.fileIN)
        myPTH    = str(self.myPath)
        LcolFile = ""
        #
        #Box height will be checked against tick height in exact mode
        nBoxHeight = int(md.boxH)
        #
        #
        # We start by finding the minimum dimension of the final scale bar
        # in order to do that we create a dummy painting device and
        # compute the total height and width of all elements to be put in
        # the scale bar: title, unit, ticks annotations & colour boxes.
        #
        hi = 0    #height of block enclosing title + unit lines
        wi = 0    #width of block enclosing title + unit lines
        wl = 0    # max number of chars of ticks annotations
        wt = 0    # width of the longest ticks annotation
        jt = 0    # height of a tick annotation, also bottom margin
        ht = 0    # total Height of the image
        pw = 0    # total Width of the image
        LT = ''
        LU = ''
        #
        myIMG = QImage(500,2000,QImage.Format_RGB32)
        myIMG.fill(0)
        #
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        myBrush = QBrush()
        myBrush.setColor(QColor("white"))
        myP.setBackground(myBrush)
        myP.setBrush(QColor("black"))
        myP.setPen(QColor("black"))
        #
        # set text properties for ticks annotations (user defined)
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        myP.setFont(myFNT)
        fm = QFontMetricsF(myFNT)
#        hh = fm.height()
        #
        if str(md.scTitle) != "":
            # title properties (fixed by plugin)
            LT = str(md.scTitle)
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
            wi = fm.boundingRect(str(LT)).width()
            if LT.find("\n") >= 0:
                # multilines title
                hi = hi * (LT.count("\n")+1)
                #split LT on \n and compute max width of components
                L = LT.split("\n")
                wi = 0
                for q in L:
                    wi = max(wi, fm.boundingRect(str(q)).width())
        else:
            LT = ""
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
        #
        L = None
        if str(md.scUnits) != "":
            # unit properties (fixed by plugin)
            LU = str(md.scUnits)
            if LU.find("\n") >= 0:
                L = LU.split()
                LU = L[0]
            LU = LU.strip()
            if LU !='' and LU[0] != "(":
                #Put unit between () if not already done
                LU = "(" + LU + ")"
            #
            if LU != '':
                myFNT.setPointSize(int(md.scFontSize))
                myFNT.setBold( False )
                myP.setFont(myFNT)
                fm = QFontMetricsF(myFNT)
                hi += fm.boundingRect(str(LU)).height() + 12
                wi = max(fm.boundingRect(str(LU)).width(), wi)
        #
        #Define necessary space to plot the scale bar with its ticks and title
        #maximum tick value length in pixels
        for i in range(nC):
            L = GetL(arV[i], md.txtDeci, md.bEnforce)
            if wl < len(L): wl = len(L)
        #
        # width of the longest annotation
        wt = fm.boundingRect(str("0" * wl)).width()
        #
        #
        # Height of a tick annotation
        jt = fm.boundingRect("Qq").height()
        #
        # Box height is set to tick height if annotation is biger
        if jt > nBoxHeight: nBoxHeight = jt
        #
        # Remove dummy painter
        myFNT=''
        myP.end()
        myIMG = ''
        #
        #------------------------- Start painting now --------------------------
        #
        # Total Height of the image
        jt /= 2
        ht = nBoxHeight * (nC +1) + jt + hi
        #
        # total width of image
        wa = int(md.boxW) + 12 + wt  # width of box + tick + annotation
        pw = max(wi, wa) +1
        #
        if wi > wa:  goff = float(wi - wa) / 2.0
        else:        goff = 1.0
        #
        # Create a new QImage of the correct size and draw the scale bar on it
        myIMG = QImage(pw,ht,QImage.Format_RGB32)
        mc = QColor(255,255,255)
        myIMG.fill(mc.rgb())
        # create a new QPainter for the QImage
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        # set text properties
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        fm = QFontMetricsF(myFNT)
        myP.setFont(myFNT)
        myP.setRenderHint(QPainter.TextAntialiasing)
        # Colour bar
        for i in range(nC):
            colo = QColor(arColo[0, i], arColo[1, i], arColo[2, i])
            border = QColor(0,0,0,255)
            myP.setBrush(colo)
            myP.setPen(border)
            h = ht - nBoxHeight * i - jt
            myP.drawRect(pw-goff, h - nBoxHeight, -int(md.boxW), nBoxHeight)
        colo = QColor(0,0,0,255)
        myP.setBrush(QColor(0,0,0,0))
        myP.setPen(colo)
        # bounding rectangle
        y0 = ht - nBoxHeight*(nC-1) -jt - nBoxHeight
        myP.drawRect(pw-goff, y0, -int(md.boxW)-1, nBoxHeight*nC)
        #
        # Tick annotations
        #
        # The first (lowest) data value of the colour table is not the minimum
        # value in the dataset. It is the upper value of the first class. This
        # means that the lowest value in the dataset is not known and must be
        # given by the user. This also means that the first value in the colour
        # table must be displayed on top of the first (bottom) colour block.
        #
        #
        # Exact mode: ticks are the same as number of colors in Auto mode
        #
        #
        if md.bAuto:
            nTicks = nC
        else:
            #Also in manual mode ticks are same as colors
            nTicks = nc
        #
        L0 = " " * wl
        mPtF = QPointF()
        #
        for i in range(nTicks):
            v  = str(GetL(arV[i], md.txtDeci, md.bEnforce))
            i0    = ht - nBoxHeight * i - jt - int(nBoxHeight/2)
            #
            y     = i0 + fm.height() / 2.0
            y1    = i0
            xx    = pw - int(md.boxW) -goff
            #
            text  = (L0 + str(v))[-wl:]
            nRect = fm.boundingRect(str(text))
            rectf = QRectF(nRect)
            mPtF.setX(float(pw - int(md.boxW) -12 -goff))
            mPtF.setY(float(y))
            rectf.moveBottomRight(mPtF)
            myP.drawText(rectf, Qt.AlignRight, str(text))       # annotation
            myP.drawLine(xx -2, y1, xx -9, y1)                  # tick
        #
        #Title
        h  = 0
        fm = None
        if LT != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LT)
            nRect = fm.boundingRect(str(text))
            if text.find("\n") >= 0:
                nRect.setHeight(nRect.height() * (text.count("\n")+1))
            rectf = QRectF(nRect)
            ww    = nRect.width()
            h     = nRect.height()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(h))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, str(text))
        #Units
        fm = None
        if LU != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LU)
            nRect = fm.boundingRect(text)
            rectf = QRectF(nRect)
            ww    = nRect.width()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(hi - 12))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, text)
        #
        # Finally save image
        if myPTH != "":
            (theDir, theFile) = os.path.split(fileIN)
            leFile = os.path.join(myPTH, theFile)
        else:
            leFile = fileIN
        (theFile,theExt) = os.path.splitext(leFile)
        LcolFile = theFile + "_Vscalebar.png"
        myIMG.save(LcolFile)
        myFNT=''
        myP.end()
        myIMG = ''
        #
        return [True, LcolFile]
#
#===============================================================================
#
class scalebarHorizontalExactAnnotation(QWidget):
    def __init__(self, nC, arColo, arV, md, fileIN, outPTH, parent=None):
        """
        Create and save a horizontal scale bar

        nC:       number of colours in array arColo()
        arColo(): R, G, B values
        arV():    real life value
        md:       all info from dialog box
        fileIN:   image file to save to (PNG format)

        We use a trick in here because Qt's painter cannot display text outside
        of a paintEvent() envent!
        We thus create a dummy widget and call its paintEnvent() function on
        creation!
        """
        super(scalebarHorizontalExactAnnotation, self).__init__(parent)
        self.nC     = nC
        self.arColo = arColo
        self.arV    = arV
        self.md     = md
        self.fileIN = fileIN
        self.myPath = outPTH
        [b, self.LcolFile] = self.paintEvent()
        if not b: self.LcolFile = ""

    def retrieveFile(self):
        return self.LcolFile

    def paintEvent(self, event=None):
        LcolFile = ""
        #
        nC       = int(self.nC)
        arColo   = self.arColo
        arV      = self.arV
        md       = self.md
        offset   = 0
        fileIN   = str(self.fileIN)
        myPTH    = str(self.myPath)
        LcolFile = ""
        LT = ''
        LU = ''
        vmin     = ''
        #
        #Box Width will be checked against longest tick width in exact mode
        nBoxWidth = int(md.boxW)
        #
        # We start by finding the minimum dimension of the final scale bar
        # in order to do that we create a dummy painting device and
        # compute the total height and width of all elements to be put in
        # the scale bar: title, unit, ticks annotations & colour boxes.
        #
        hi = 0    #height of block enclosing title + unit lines
        wi = 0    #width of block enclosing title + unit lines
        wl = 0    # max number of chars of ticks annotations
        wt = 0    # width of the longest ticks annotation
        jt = 0    # height of a tick annotation
        ht = 0    # total Height of the image
        pw = 0    # total Width of the image
        #
        myIMG = QImage(500,2000,QImage.Format_RGB32)
        myIMG.fill(0)
        #
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        myBrush = QBrush()
        myBrush.setColor(QColor("white"))
        myP.setBackground(myBrush)
        myP.setBrush(QColor("black"))
        myP.setPen(QColor("black"))
        #
        # set text properties for ticks annotations (user defined)
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        myP.setFont(myFNT)
        fm = QFontMetricsF(myFNT)
#        hh = fm.height()
        #
        if str(md.scTitle) != "":
            # title properties (fixed by plugin)
            LT = str(md.scTitle)
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
            wi = fm.boundingRect(str(LT)).width()
            if LT.find("\n") >= 0:
                # multilines title
                hi = hi * (LT.count("\n")+1)
                #split LT on \n and compute max width of components
                L = LT.split("\n")
                wi = 0
                for q in L:
                    wi = max(wi, fm.boundingRect(str(q)).width())
        else:
            LT = ""
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            myP.setFont(myFNT)
            fm = QFontMetricsF(myFNT)
            hi = fm.height()
        #
        L = None
        if str(md.scUnits) != "":
            # unit properties (fixed by plugin)
            LU = str(md.scUnits)
            if LU.find("\n") >= 0:
                L = LU.split()
                LU = L[0]
            LU = LU.strip()
            if LU !='' and LU[0] != "(":
                #Put unit between () if not already done
                LU = "(" + LU + ")"
            #
            if LU != '':
                myFNT.setPointSize(int(md.scFontSize))
                myFNT.setBold( False )
                myP.setFont(myFNT)
                fm = QFontMetricsF(myFNT)
                hi += fm.boundingRect(str(LU)).height() + 12
                wi = max(fm.boundingRect(str(LU)).width(), wi)
        wi += fm.boundingRect("WW").width()
        wun = fm.boundingRect("0").width()
        #
        #Define necessary space to plot the scale bar with its ticks and title
        #maximum tick value length in pixels
        for i in range(nC):
            L = str(GetL(arV[i], md.txtDeci, md.bEnforce))
            if wl < len(L): wl = len(L)
        #
        # width of the longest annotation
        wt = fm.boundingRect(str("0" * wl)).width()
        #
        if nBoxWidth < wt: nBoxWidth = wt
        #
        # Height of a tick annotation
        jt = fm.boundingRect("Qq").height()
        #
        # Remove dummy painter
        myFNT=''
        myP.end()
        myIMG = ''
        #
        #------------------------- Start painting now --------------------------
        #
        #Total Height of the image
        ht = int(md.boxH) + jt + hi + 13  # tick height = 9 space = 4
        #Total width of image
        wa = float(wt + nBoxWidth * nC)
        pw = max(wi, wa) +wun +1
        #
        pw -= wt / 2.0
        x0 = float(wt + wun) / 2.0
        #
        #goff: centre box relative to title
        if wi > wa:  goff = float(wi - wa) / 2.0
        else:        goff = -float(pw - (nBoxWidth*nC)) / 2.0
        x0 += goff
        #
        # Create a new QImage of the correct size and draw the scale bar on it
        myIMG = QImage(pw,ht,QImage.Format_RGB32)
        mc = QColor(255,255,255)
        myIMG.fill(mc.rgb())
        # create a new QPainter for the QImage
        myP = QPainter()
        if not myP.begin( myIMG ):
            myIMG = ''
            return [False, ""]
        #
        # set text properties
        myFNT = QFont()
        myFNT.setFamily("arial")
        myFNT.setPointSize(int(md.scFontSize))
        myFNT.setBold( False )
        fm = QFontMetricsF(myFNT)
        myP.setFont(myFNT)
        myP.setRenderHint(QPainter.TextAntialiasing)
        # Colour bar
        y0 = ht - int(md.boxH) - jt - 13
        for i in range(nC):
            colo = QColor(arColo[0, i], arColo[1, i], arColo[2, i])
            border = QColor(0,0,0,255)
            myP.setBrush(colo)
            myP.setPen(border)
            x = x0 + nBoxWidth * i
            myP.drawRect(x, y0, nBoxWidth , int(md.boxH))
        colo = QColor(0,0,0,255)
        myP.setBrush(QColor(0,0,0,0))
        myP.setPen(colo)
        # bounding rectangle
        myP.drawRect(x0, y0, nBoxWidth*nC, int(md.boxH))
        mPtF  = QPointF()
        #
        # Tick annotations
        #
        # The first (lowest) data value of the colour table is not the minimum
        # value in the dataset. It is the upper value of the first class. This
        # means that the lowest value in the dataset is not known and must be
        # given by the user. This also means that the first value in the colour
        # table must be displayed at the right of the first (left) colour block.
        #
        # Exact mode: ticks are the same as number of colors in Auto mode
        #
        if md.bAuto:
            nTicks = nC
        else:
            #Also in manual mode ticks are same as colors
            nTicks = nc
        #
        #
        L0 = " " * wl
        y  = y0 + int(md.boxH)
        yoff = 13.0 + fm.boundingRect("0").height() / 2.0
        #
        for i in range(nTicks):
            v  = str(GetL(arV[i], md.txtDeci, md.bEnforce))
            x  = x0 + offset + nBoxWidth * i + int(nBoxWidth/2)
            #
            text  = str(v)
            nRect = fm.boundingRect(text)
            rectf = QRectF(nRect)
            mPtF.setX(float(x))
            mPtF.setY(float(y + yoff))
            rectf.moveCenter(mPtF)
            myP.drawText(rectf, Qt.AlignRight, text)       # annotation
            myP.drawLine(x, y, x, y+9)                     # tick
        #
        #Title
        h  = 0
        fm = None
        if LT != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize)+3)
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LT)
            nRect = fm.boundingRect(str(text))
            if text.find("\n") >= 0:
                nRect.setHeight(nRect.height() * (text.count("\n")+1))
            rectf = QRectF(nRect)
            ww    = nRect.width()
            h     = nRect.height()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(h))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, str(text))
        #Units
        fm = None
        if LU != '':
            myFNT = QFont()
            myFNT.setFamily("arial")
            myFNT.setPointSize(int(md.scFontSize))
            myFNT.setBold( True )
            fm = QFontMetricsF(myFNT)
            myP.setFont(myFNT)
            text  = str(LU)
            nRect = fm.boundingRect(text)
            rectf = QRectF(nRect)
            ww    = nRect.width()
            mPtF.setX(float(pw - ww) / 2.0)
            mPtF.setY(float(hi-12))
            rectf.moveBottomLeft(mPtF)
            myP.drawText(rectf, Qt.AlignCenter, text)
        #
        # Finally save image
        if myPTH != "":
            (theDir, theFile) = os.path.split(fileIN)
            leFile = os.path.join(myPTH, theFile)
        else:
            leFile = fileIN
        (theFile,theExt) = os.path.splitext(leFile)
        LcolFile = theFile + "_Hscalebar.png"
        myIMG.save(LcolFile)
        myFNT=''
        myP.end()
        myIMG = ''
        #
        return [True, LcolFile]
#
#===============================================================================
#
def ReadTableFile(tblFile):
    """
    Read the input file and extract all its colour table info.
    The input file is a colour table file and can be either a 1-band raster
    colour table file (*.txt) created witht the 1-band raster colour table
    plugin or a QGIS QML file containing a custom colour ramp having a DISCRETE,
    INTERPOLATED or EXACT algorithm.
    """
    #
    sc = open(tblFile,'r')
    arAll = sc.readlines()
    sc.close()
    #
    #Check that we have the correct file
    n = 0
    for a in arAll:
        n += 1
        if a.strip() == "<customColorRamp>": break
        if a.find("<colorrampshader colorRampType=") >= 0:
           n = -n
           break
    #
    if n >= len(arAll):
        #Not a QML, is it a colour table file?
        if arAll[0].find("INTERPOLATION:DISCRETE") >= 0:
            return GetFromTBL(arAll,0)
        elif arAll[0].find("INTERPOLATION:INTERPOLATED") >= 0:
            return GetFromTBL(arAll,1)
        elif arAll[0].find("INTERPOLATION:EXACT") >= 0:
            return GetFromTBL(arAll,2)
        else:
            #Not even, abort
            return [False, "ERROR: Wrong input file \
                   (must be a colour table or a custom QML file)!", "",9]
    else:
        if n < 0:
           # QML from version 2.x
           return GetFromQMLv2(n, arAll)
        else:
           # QML from version 1.x
           return GetFromQML(n-1, arAll)
#
#===============================================================================
#
def GetFromTBL(ar, nMode):
    """From a colour table file (1-band raster colour table file: .txt)"""
    #Read colour values
    arColo = np.zeros((3, len(ar)), int)
    arV = np.zeros(len(ar), np.float32)
    nC = 0
    #
    for a in ar:
        if a.find(",") >= 0:
            #value,r,g,b,alpha
            #-0.65480690,1,1,1,255,
            br = a.split(",")
            arColo[0, nC] = int(br[1])   #red
            arColo[1, nC] = int(br[2])   #green
            arColo[2, nC] = int(br[3])   #blue
            arV[nC] = float(br[0])       #value
            nC += 1
    #
    return [nC, arColo, arV, nMode]
#
#===============================================================================
#
def GetFromQML(n0, ar):
    """ From a QGIS V1.x QML file """
    n = n0 + 1
    if ar[n].strip() == "<colorRampType>DISCRETE</colorRampType>":
        nMode = 0
    elif ar[n].strip() == "<colorRampType>INTERPOLATED</colorRampType>":
        nMode = 1
    elif ar[n].strip() == "<colorRampType>EXACT</colorRampType>":
        nMode = 2
    else:
         return [False, "ERROR: Wrong input file (2)!", "", -1]
    #
    #Read colour values
    arColo = np.zeros((3, len(ar) -n), int)
    arV = np.zeros(len(ar) -n, np.float32)
    n += 1
    nC = 0
    i = 0
    #
    delQML = '"'
    for a in ar:
        i += 1
        a = a.strip()+ '               '
        if a[0:15] == "<colorRampEntry":
            j00 = a.find("red=") + 5
            j10 = a.find(delQML,j00)
            j01 = a.find("blue=") + 6
            j11 = a.find(delQML,j01)
            j02 = a.find("green=") + 7
            j12 = a.find(delQML,j02)
            j03 = a.find("value=") + 7
            j13 = a.find(delQML,j03)
            try:
                arColo[0, nC] = int(a[j00:j10])  #red
                arColo[1, nC] = int(a[j02:j12])  #green
                arColo[2, nC] = int(a[j01:j11])  #blue
                arV[nC] = float(a[j03:j13])
            except ValueError:
                delQML = "'"
                j00 = a.find("red=") + 5
                j10 = a.find(delQML,j00)
                j01 = a.find("blue=") + 6
                j11 = a.find(delQML,j01)
                j02 = a.find("green=") + 7
                j12 = a.find(delQML,j02)
                j03 = a.find("value=") + 7
                j13 = a.find(delQML,j03)
                arColo[0, nC] = int(a[j00:j10])  #red
                arColo[1, nC] = int(a[j02:j12])  #green
                arColo[2, nC] = int(a[j01:j11])  #blue
                arV[nC] = float(a[j03:j13])
            except:
                #unhandled error
                return [False, "ERROR: Wrong input file (3)!", "", -1]
            nC += 1
        elif i>n:
            break
    #
    return [nC, arColo, arV, nMode]
#
#===============================================================================
#
def GetFromQMLv2(n0n, ar):
    """ From a QGIS V2.x QML file """
    # <item alpha="255" value="-205.453" label="-205.453000" color="#2b83ba"/>
    n0 = (-n0n) -1
    n = n0
    if ar[n].find("DISCRETE") >= 0:
        nMode = 0
    elif ar[n].find("INTERPOLATED") >= 0:
        nMode = 1
    elif ar[n].find("EXACT") >= 0:
        nMode = 2
    else:
         return [False, "ERROR: Wrong input file (2)!/n"+ar[n], "", -1]
    #
    #Read colour values
    arColo = np.zeros((3, len(ar) -n), int)
    arV = np.zeros(len(ar) -n, np.float32)
    nC = 0
    i = 0
    #
    delQML = '"'
    for a in ar:
        i += 1
        a = a.strip()+ '               '
        if a[0:5] == "<item" and i > n0:
            j00 = a.find("color=") + 8
            j10 = a.find(delQML,j00)
            j03 = a.find("value=") + 7
            j13 = a.find(delQML,j03)
            try:
                arColo[0, nC] = int(a[j00:j00+2],16)    #red
                arColo[1, nC] = int(a[j00+2:j00+4],16)  #green
                arColo[2, nC] = int(a[j00+4:j10],16)  #blue
                arV[nC] = float(a[j03:j13])
            except ValueError:
                delQML = "'"
                j00 = a.find("color=") + 8
                j10 = a.find(delQML,j00)
                j03 = a.find("value=") + 7
                j13 = a.find(delQML,j03)
                arColo[0, nC] = int(a[j00:j00+2],16)    #red
                arColo[1, nC] = int(a[j00+2:j00+4],16)  #green
                arColo[2, nC] = int(a[j00+4:j10],16)    #blue
                arV[nC] = float(a[j03:j13])
            except:
                #unhandled error
                return [False, "ERROR: Wrong input file (3)!", "", -1]
            nC += 1
    #
    return [nC, arColo, arV, nMode]
#
#===============================================================================
#
def checkOneBandLayer(iface):
    theLayer = iface.activeLayer()
    if theLayer is None or theLayer.type() != QgsMapLayer.RasterLayer:
        msg="No Raster Layer Selected!\n"+\
            "You must select a raster layer."
        return [False, msg]

    elif theLayer.rasterType() > 0:
        msg="Raster must be one-band!\n"+\
            "You must select a correct raster layer."
        return [False, msg]
    else:
        return [True, theLayer]
#
#===============================================================================
#
def saveQML(iface, theLayer):
    """  Save the layer style to a qml file  """
    #
    tmpDir = tempfile.gettempdir()
    theFile = theLayer.name() + ".qml"
    tempname = os.path.join(tmpDir, theFile)
    if theLayer.saveNamedStyle( tempname ):
        return [True, tempname]
    else:
        return [False, ""]
#
#===============================================================================
