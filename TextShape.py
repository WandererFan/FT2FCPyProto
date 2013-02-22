#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''TextShape.py - Turns a text string into Shapes or Wires of a given height.
Generated Compound Shape is suitable for extruding or pocketing.
'''
'''Uses FreeType2 <www.freetype.org> and freetype-py <code.google.com/p/freetype-py/> to extract glyph vectors from TrueTypeFonts.  Also requires FontUtils.py FT2 helper functions>
'''

#ToDo: Working Plane - this version only makes shapes on XY plane.

#$ Insert LEGALBUMF.txt
#$ Insert DEPEND.txt

import freetype 

import FreeCAD
import Part
import Draft
import OpenSCAD2Dgeom

import FontUtils

# SET DEBUG MODE
DEBUG = False

#### Function Defs
# 2D Geometry Functions
# Outines are translated and scaled in 2D using these functions.
# They probably already exist somewhere in FreeCAD 
def _translatePoint(Point,TVector):
    '''xypoint = _translatePoint(xypoint,TVector): Move a 2D point by TVector.'''
    NewPoint = (Point[0] + TVector[0], Point[1] + TVector[1])
    return(NewPoint)

def _translatePoints(Points, TVector):
    '''xypointslist = _translatePoints(xypointslist, TVector): Move all the 
    points in the list (segment) by TVector.'''
    NewSeg = []
    for point in Points:
        NewPoint = _translatePoint(point, TVector)
        NewSeg.append(NewPoint)
    return(NewSeg)

def _scalePoint(Point, Scale):
    '''_scalePoint(xypoint, Scale): Make a 2D point's vector longer or 
    shorter.'''
    NewPoint = (Point[0]*Scale[0], Point[1]*Scale[1])
    return(NewPoint)

def _scalePoints(Points, Scale):
    '''newpoints = _scalePoints(xypointslist, Scale): Make the all the points' 
    vectors longer or shorter.'''
    NewPoints = []
    for point in Points:
        NewPoint = _scalePoint(point,Scale)
        NewPoints.append(NewPoint)
    return(NewPoints)

# FC Helper Functions
def _toVector(Point):
    '''_toVector(xypoint): Converts a 2D (x,y) point into a FreeCAD Vector 
    object (x,y,z). Z value is set to zero.'''
    NewVector = FreeCAD.Vector(Point[0],Point[1],0)
    return(NewVector)

def _toVectors(Points):
    '''_toVector(xypointslist): Converts a list of 2D (x,y) points into
    FreeCAD Vector objects (x,y,z). Z values are all set to zero.'''
    NewVectorList = []
    for point in Points:
        NewVector = _toVector(point)
        NewVectorList.append(NewVector)
    return(NewVectorList)

def _FCLineSegment(Points):
    '''_FCLineSegment(xypointslist): Make a Part.Line Geo obj from these xypoints'''
    LPoints = _toVectors(Points)
    l = Part.Line(LPoints[0],LPoints[1])
    return(l)

def _FCCurveSegment(Points):
    '''_FCCurveSegment(xypointslist): Make a Part.BezierCurve Geo obj from these 
    xypoints'''
    CPoints = _toVectors(Points)
    c = Part.BezierCurve()
    c.setPoles(CPoints)
    return(c)

# Text Shape class def
class TextShape():
    '''TextShape(FontPath,FontFile,String,Height,Track): Turns a string into 
    Wires or a Compound Shape'''
    def __init__(self, FPath='./',FName='Arial.ttf', String=None, 
                 Height=10, Track=0):
        self.FTFont = FontUtils.initFreeType(FPath, FName)
        self.String = String
        self.Height = Height                  # FC units
        self.Tracking = Track                 # FC units
        self.Scale = FontUtils.getUniformScale(self.FTFont, self.Height) 
# attributes we may need later
#        self.FType = (FName.split('.')[-1])).upper()
#        self.Position = (0,0,0)
#        self.Plane = (0,0,1)
#        self.Shape = None
        if DEBUG:
            print "TextShape Parms"
            print "Font Path: ", FPath
            print "Font Name: ", FName
            print "String: ", String
            print "Height: ", Height
            print "Track: ", Track
            print "Scale: ", self.Scale
#            print "Font Type: ", FType

    def _makeCharWires(self, CharCons, PenPos):
        '''_makeCharWires(CharCons, PenPos): Returns the Wires that describe this
        char translated to PenPos.  '''
        CharWires = []
        for Contour in CharCons:
            CGeos = []                    # segment geometries for this contour
            for Segment in Contour:
                ScaleSeg = _scalePoints(Segment, self.Scale)       # Fontdef->FC xy
                TransSeg = _translatePoints(ScaleSeg, (PenPos,0))  # move along baseline
                if len(ScaleSeg) == 2:
                    FCGeoObj = _FCLineSegment(TransSeg)
                else:
                    FCGeoObj = _FCCurveSegment(TransSeg)
                CGeos.append(FCGeoObj)
            s = Part.Shape(CGeos)
            CWire = Part.Wire(s.Edges)
            CharWires.append(CWire)
        return(CharWires)
  
    def toWires(self):
        '''toWires(self): Creates a collection of Part.Wires outlining the text
        string. Returns a list where each entry corresponds to 1 character.  
        Each list entry is a list of Wires describing 1 of the character's
        Contours'''
        PenPos = 0                            # offset along baseline
        KChar = chr(0)                        # kerning. missing glyph convention
        Chars = []
        for char in self.String:
            # get unpacked and segmented contour outlines and positioning metrics
            # for this char
            CharCons,Adv,Kern = FontUtils.getTTFCharContours(
                                                       self.FTFont, 
                                                       char, 
                                                       KChar)
            PenPos += Kern.x * self.Scale[0]        # only horiz strings for now
            CharWires = self._makeCharWires(CharCons, PenPos)
            if CharWires:
                Chars.append(CharWires)
            PenPos += (Adv * self.Scale[0]) + self.Tracking
            KChar = char
        return(Chars)

    def toShape(self):
        '''toShape(): Turn the chars in self.String into Faces and merge 
        overlapping faces (cuts). Returns a Compound Shape where each Shape 
        represents a char (or a piece of a char if char contains islands 
        (ex: i,j,:,...).'''
        SSChars = []
        CharWires = self.toWires()
        for char in CharWires:
            CharFaces = []
            for CWire in char:
                f = Part.Face(CWire)
                if f:
                    CharFaces.append(f)
            # whitespace (ex: ' ') has no faces. This breaks OpenSCAD2Dgeom...
            if CharFaces:
                s = OpenSCAD2Dgeom.Overlappingfaces(CharFaces).makeshape()
                SSChars.append(s)
        StringShape = Part.Compound(SSChars)
        return(StringShape)

# Tester
if __name__ == '__main__':
    print('TextShape Started')

    # test strings 
    # if string contains funky characters, it has to be declared as Unicode
    String = u'éçÄçA_ñØ'

    Height  = 500.0                        # desired string height FCunits
    StringPosition  = (200,200)            # location for string display in FCxy

    FontPath = '/usr/share/fonts/truetype/msttcorefonts/'
    FontName = 'Arial.ttf'

    # Try it
    myTextShape = TextShape(FontPath,FontName,String,Height)

    # toShape test
    myDocObj1 = App.ActiveDocument.addObject("Part::Feature","TextShape")
    myDocObj1.Shape = myTextShape.toShape()
    pos = FreeCAD.Vector(StringPosition[0],StringPosition[1],0)
    myDocObj1.Placement.Base = pos
    
    # toWires test
    pos = FreeCAD.Vector(3*StringPosition[0],3*StringPosition[1],0)
    myTextWires = myTextShape.toWires()
    for char in myTextWires:
        for contour in char:
            contour.Placement.Base = pos
            Part.show(contour)

    print ('TextShape Ended')

## end of TextShape.py
