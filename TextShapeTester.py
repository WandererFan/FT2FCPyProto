#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''TextShapeTester.py - Test driver for TextShape
'''
'''Dependencies - TextShape.py, FontUtils.py, FreeType2, freetype-py'''

import FreeCAD
import Part
import TextShape 

print('TextShapeTester Started')

# test strings 
# if string contains funky characters, it has to be declared as Unicode
#String = 'Wide WMA_'
#String = 'Big'
#String = 'ecAnO'
#String = u'éçÄñØ'
#String = 'abcdefghijklmnopqrstuvwxyz0123456789'
#String = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
#String = 'Big Daddy'
#String = 'AVWAIXA.V'
String = 'FreeCAD'

Height  = 1000                         # desired string height FCunits
StringPosition  = (200,200)            # location for string display in FCxy
Track = 0                              # intercharacter spacing

#FontPath = '/usr/share/fonts/truetype/msttcorefonts/' 
#FontName = 'Times_New_Roman_Italic.ttf')
FontPath = '/usr/share/fonts/truetype/msttcorefonts/'
FontName = 'Arial.ttf'
#FontPath = '/usr/share/fonts/truetype/msttcorefonts/' 
#FontName = 'ariali.ttf')                            #symlink to ttf
#FontPath = '/usr/share/fonts/truetype/' 
#FontName = 'Peterbuilt.ttf')                        # overlapping script font
#FontPath = '/usr/share/fonts/truetype/' 
#FontName = dyspepsia.ttf')                          # overlapping script font

# Try it
myTextShape = TextShape.TextShape(FontPath,FontName,String,Height,Track)

# toShape test
myDocObj1 = App.ActiveDocument.addObject("Part::Feature","TextShape")
myDocObj1.Shape = myTextShape.toShape()
pos = FreeCAD.Vector(StringPosition[0],StringPosition[1],0)
myDocObj1.Placement.Base = pos
    
# toWires test
StringPosition  = (-800,-800)                 # move the wires so we can see them
pos = FreeCAD.Vector(StringPosition[0],StringPosition[1],0)
myTextWires = myTextShape.toWires()
for char in myTextWires:
    for contour in char:
        contour.Placement.Base = pos
        Part.show(contour)

print ('TextShapeTester Ended')

## end of TextShapeTester.py
