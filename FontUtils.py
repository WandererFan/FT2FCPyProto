#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''FontUtils.py - Collection of FreeType helper functions to extract font 
information.
'''
'''Equivalents to most of these functions might be available in FreeType, but 
are not implemented in FreeType-py. (??)'''

#$ Insert LEGALBUMF.txt
#$ Insert DEPEND.txt

import freetype

# SET DEBUG MODE
DEBUG = False

# 2d Geometry Routines
def _midPoint(p1, p2):
    '''_midPoint(p1, p2): Return the midPoint of line p1-p2 in 2D'''
# font coords are all ints (longs?). should this be int arithmetic or
# would that introduce too much error in vertex coords? TBD
    newx   = (p1[0] + p2[0])/2
    newy   = (p1[1] + p2[1])/2
    return((newx,newy))

# FT2 flags not in freetype-py 
FT_CURVE_TAG_ON    = 0b00000001
FT_CURVE_TAG_CONIC = 0b00000000
FT_CURVE_TAG_CUBIC = 0b00000010

# FT2 Helper Functions
# Private
def _isVertex(tag):
    '''_isVertex(FTTag): True if FTTag is on the outline contour'''
#    if tag & 0b0001 :
    if tag & FT_CURVE_TAG_ON:
        return(True)
    else:
        return(False)

def _isCubicControl(tag):
    '''_isCubicControl(FTTag): True if FTTag is off the outline contour and 
    contour is drawn with cubic Bezier (Type1 fonts)'''
    if tag & FT_CURVE_TAG_CUBIC: 
        return(True)
    else:
        return(False)

def _isConicControl(tag):
    '''_isConicControl(FTTag): True if FTTag is off the outline contour and 
    contour is drawn with conic(quadratic) Bezier (TrueType fonts)'''
    if _isVertex(tag) or _isCubicControl(tag):
        return(False)
    else:
        return(True)

def _showFontGlobals(FTFont):
    '''_showFontGlobals(FTFont): DEBUG routine to print global metrics for this 
    font '''
    print "Global Units per EM: ", FTFont.units_per_EM
    print "Global bbox: ", FTFont.bbox.xMax,", ",FTFont.bbox.xMin," : ", \
        FTFont.bbox.yMax,", ",FTFont.bbox.yMin
    print "Global ascender: ", FTFont.ascender
    print "Global descender: ", FTFont.descender
    print "Global height: ", FTFont.height
    print "Global max_advance_width: ", FTFont.max_advance_width
    print "Global max_advance_height: ", FTFont.max_advance_height
    print "Global underline_position: ", FTFont.underline_position
    print "Global underline_thickness: ", FTFont.underline_thickness
    print "Global has kerning: ", FTFont.has_kerning

# Public
def getUniformScale(FTFont, Height):               
    '''float = getUniformScale(FTFontHandle, FCHeight): Returns scale factor to
    map (0 - font height) onto (0 - Height).  Use when font is to be scaled 
    uniformly (same x,y).'''
    # face.height is space between consecutive baselines in font units
    Scale = float(float(Height)/FTFont.height)  
    return((Scale, Scale)) 

def initFreeType(FontPath, FontName):
    '''FThandle = initFreeType(FontPath, FontName): Wake up FreeType2 and 
    tell it which font file to use'''
    FTFont = freetype.Face(FontPath + FontName)
    FTFont.set_char_size( 48*64 )
    # size of bit map character in 1/64 of a point so this is 48 point type. 
    # Don't know if this scales outline, or just bitmap.  FT2 blows up if this
    # is not set to some non-zero value. Magic. 
    if DEBUG:
        print "Font: ", FontPath+FontName
        _showFontGlobals(FTFont)
    return(FTFont)

def getFTChar(FTFont, char):                   
    ''' getFTChar(FTFont, char): Returns glyph(char) outline and advance metric.'''
    if DEBUG:
       print "Getting: ", char
    flags = freetype.FT_LOAD_DEFAULT | freetype.FT_LOAD_NO_BITMAP
    FTFont.load_char(char, flags)
    GlyphDef = FTFont.glyph     
    GOutline = GlyphDef.outline                          
    Adv      = GlyphDef.advance.x            # horiz adv distance for this char 
    return GOutline, Adv

def unpackTTFContour(points, tags, CStart, CEnd):
    '''newpoints, newtags = unpackTTFContour(points, tags, CStart, CEnd): Go 
    through all the outline points in this contour and make a new list of points 
    that has no consecutive control points. 
    '''
    '''Assumption: only handling TTF so will never encounter Cubic Control point. 
    Assumption: point[0] is a Vertex. True for most TTF.'''
    if DEBUG:
        print "Unpacking: ", CStart, "-", CEnd
    UpkdXY = [ ]                                          
    UpkdTags = [ ]                                  
    for iPoint in range(CStart, CEnd+1):
        UpkdXY.append(points[iPoint])                   
        UpkdTags.append(tags[iPoint])
        if _isConicControl(tags[iPoint]):
            if (iPoint) < CEnd:            # if not the last point, look ahead 
                if not(_isVertex(tags[iPoint+1])) :
                    # next point is a consecutive control point, 
                    # so make a new vertex between them
                    newxy = _midPoint(points[iPoint], points[iPoint+1])
                    UpkdXY.append(newxy)
                    UpkdTags.append(FT_CURVE_TAG_ON)

    UpkdXY.append(points[CStart])       # close the contour with 1st Vertex
    UpkdTags.append(tags[CStart])  
    return UpkdXY, UpkdTags                 

def segmentTTFContour(CPoints,CTags):
    '''segmentlist = segmentTTFContour(CPoints,CTags): Breaks an unpacked contour
    into elementary segments. Look through all the points for line (V-V) or 
    Bezier curve (V-C-V) segments. Returns a list whose elements are 2 or 3 
    point lists.'''
    '''Assumption: List of points always starts with a vertex.'''
    '''Equivalent to FT Decompose?'''
    CSegs   = []
    nLines     = 0
    nCurves    = 0
    for iPoint in range(0,len(CPoints)-1):         # don't look for V's past last point
        if _isVertex(CTags[iPoint]):
            if _isVertex(CTags[iPoint+1]):
                # two consecutive Vertices (V-V) ---> line segment
                CSegs.append([CPoints[iPoint],CPoints[iPoint+1]])
                nLines += 1 
            else:
                # not a V-V, must be V-C
                if iPoint+2 >= len(CPoints):
                    # trying to look past end of points list
                    # points list doesn't end with V-V or V-C-V, must be error!
                    FreeCad.PrintError(
                     "*** Error: character outline points list is ill formed - 1. ", 
                     iPoint)
                elif _isVertex(CTags[iPoint+2]):
                    # have V-C-V ---> B curve segment
                    CSegs.append(
                                   [CPoints[iPoint],CPoints[iPoint+1],
                                   CPoints[iPoint+2]]) 
                    nCurves += 1
                else:
                    # not V-V, not V-C-V, must be error!
                    FreeCAD.PrintError(
                     "*** Error: character outline points list is ill formed - 2. ", 
                     iPoint) 
    return(CSegs)

def getTTFCharContours(FTFont, char, KChar):
    ''' getTTFCharContours(FTFont, char): Returns a list of all the elementary  
    segments in all the contours of char's outline, + spacing metrics.'''
    ''' return list in form: CharCons[0] = [seg00,seg01,...], CharCons[1] = 
    [seg10,seg11,...]'''

    # get the glyph outline info for this char from TTF file
    GOutline, Adv = getFTChar(FTFont, char)
    GPoints       = GOutline.points               # packed vertex representation
    GTags         = GOutline.tags                 # on/off curve indicators
    GCEnds        = GOutline.contours             # each char has 1 or more contours                
    if DEBUG:
        print "Raw Font Outline Dump for: ", char
        print "Advance: ", Adv
        for xy in GPoints:
            print xy[0], ", ", xy[1]

    Kerning = FTFont.get_kerning(KChar,char,freetype.FT_KERNING_DEFAULT)
    if DEBUG:
        print "Kerning"
        print "Prev: ", KChar," Char: ", char 
        print "Kerning Value: ", Kerning.x, " : ", Kerning.y

    CharCons = []                        # contours/segs for this char
    CStart = 0                           # index of 1st point in contour
    for iCon in range(0,len(GCEnds)):
        CEnd = GCEnds[iCon]
        UpkdXY, UpkdTags = unpackTTFContour(GPoints, GTags, CStart, CEnd)
        CSegs = segmentTTFContour(UpkdXY, UpkdTags)
        CharCons.append(CSegs)
        CStart = CEnd+1
    return(CharCons, Adv, Kerning)

### End FontUtils.py
