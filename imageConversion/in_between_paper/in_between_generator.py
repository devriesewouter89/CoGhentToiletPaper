#!/usr/bin/env python
import os

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


def replace_text_in_svg(svg_path, text_1, text_2, output_path):
    # load the template from a file
    tpl = svglue.load(file=svg_path)

    # replace some text based on id
    tpl.set_text('text1', text_1)
    tpl.set_text('text2', text_2)

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
    with open('{}.pdf'.format(output_path), 'wb') as out, open('.svg'.format(output_path), 'w') as svgout:
        svgout.write(src)
        cairosvg.svg2pdf(bytestring=src, write_to=out)


if __name__ == '__main__':
    replace_text_in_svg('template.svg', "vorige wc-rol", "volgende wc-rol", "test_output")
