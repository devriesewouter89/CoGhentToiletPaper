#!/usr/bin/env python

import svglue
"""
tip: 

    click the element you want to template enter the XML editor (Edit -> XML Editor, or Ctrl+Shift+X for me) add (
    with plus button) a row in the attribute table, whose Name (1st column) is template-id, and whose Value (2nd 
    column) is your key text. 

    For text just make sure you do this on the tspan element not the text element that (for me) contains it, 
    and which inkscape focuses when you click on the text in the document. I had to manually click the tspan element in 
    the xml editor. from [link](https://github.com/mbr/svglue/issues/9) 
"""

# load the template from a file
tpl = svglue.load(file='template.svg')

# replace some text based on id
tpl.set_text('temp', u'This was replaced.')

# replace the pink box with 'hello.png'. if you do not specify the mimetype,
# # the image will get linked instead of embedded
# tpl.set_image('pink-box', file='hello.png', mimetype='image/png')
#
# # svgs are merged into the svg document (i.e. always embedded)
# tpl.set_svg('yellow-box', file='Ghostscript_Tiger.svg')

# to render the template, cast it to a string. this also allows passing it
# as a parameter to set_svg() of another template
src = tpl.__str__().decode()

# write out the result as an SVG image and render it to pdf using cairosvg
import cairosvg
with open('output.pdf', 'wb') as out, open('output.svg', 'w') as svgout:
    svgout.write(src)
    cairosvg.svg2pdf(bytestring=src, write_to=out)