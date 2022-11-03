#!/usr/bin/env python
import math
import os
import svglue
import drawSvg as draw


# todo: better to use https://github.com/cduck/drawSvg ? and just write svg text at certain locations
"""
tip: 

    click the element you want to template enter the XML editor (Edit -> XML Editor, or Ctrl+Shift+X for me) add (
    with plus button) a row in the attribute table, whose Name (1st column) is template-id, and whose Value (2nd 
    column) is your key text. 

    For text just make sure you do this on the tspan element not the text element that (for me) contains it, 
    and which inkscape focuses when you click on the text in the document. I had to manually click the tspan element in 
    the xml editor. from [link](https://github.com/mbr/svglue/issues/9) 
"""


def replace_text_in_svg(svg_path, text_old, year_old, text_new, year_new, output_path, max_len_text: int):
    # load the template from a file
    tpl = svglue.load(file=svg_path)

    # todo place \n\r in text if length exceeds some limit
    # if len(text_old) > max_len_text:
    #     temp = text_old.split()
    #     list_0 =
    #     temp_0 = ' '.join(str(e) for e in list )
    # replace some text based on id
    tpl.set_text('text1', text_old)
    tpl.set_text('text2', text_old)

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
    with open('{}.pdf'.format(output_path), 'wb') as out, open('{}.svg'.format(output_path), 'w') as svgout:
        svgout.write(src)
        cairosvg.svg2pdf(bytestring=src, write_to=out)


def create_svg(text_old, year_old, text_new, year_new, output_path, overlap_text, percentage_of_layers: float, max_len_text: int):
    """

    @param text_old:
    @param year_old:
    @param text_new:
    @param year_new:
    @param output_path:
    @param overlap_text:
    @param percentage_of_layers: we'll use the layer parameter to alter the diagonal line
    @param max_len_text:
    """
    width = 200
    height = 100
    d = draw.Drawing(width, height, origin='center', displayInline=False)

    # Draw a rectangle todo: only for readability and debugging!
    r = draw.Rectangle(-100, -50, width, height, fill='#bbbbbb')
    r.appendTitle("Our first rectangle")  # Add a tooltip
    d.append(r)

    # -----------------OLD TEXT -----------------------
    offset_x = 20
    offset_y = 10
    p = draw.Path(stroke_width=2, stroke='lime',
                  fill='black', fill_opacity=0.2)
    p.M(-width/2 + offset_x, -height/2 + offset_y)
    p.L(-width/2 + offset_x, height/2-offset_y)
    d.append(p)

    # Draw text
    d.append(draw.Text(text_old, 8, path=p, text_anchor='middle'))

    # -----------------NEW TEXT-----------------------
    p = draw.Path(stroke_width=2, stroke='lime',
                  fill='black', fill_opacity=0.2)
    p.M(width / 2 - offset_x, height/2 - offset_y)
    p.L(width / 2 - offset_x, -height/2 + offset_y)
    d.append(p)

    # Draw text
    d.append(draw.Text(text_new, 8, path=p, text_anchor='middle'))

    # --------------CENTER CIRCLE FIGURE--------------
    angle_offset = 20
    angle = percentage_of_layers * 2 * angle_offset - angle_offset # function to make diagonal "move" throughout time
    radius = 30

    d.append(draw.Arc(0, 0, radius, 180, -179, cw=True, stroke='black', stroke_width=1, fill='None'))
    p = draw.Path(stroke='black', stroke_width=2, fill='none')

    p.M(math.sin(angle * math.pi / 180.0) * radius, math.cos(angle * math.pi / 180.0) * radius) \
        .L((math.tan(angle * math.pi / 180.0) * height / 2.0), height / 2.0)
    d.append(p)
    p.M(-math.sin(angle * math.pi / 180.0) * radius, -math.cos(angle * math.pi / 180.0) * radius) \
        .L((-math.tan(angle * math.pi / 180.0) * height / 2.0), -height / 2.0)
    d.append(p)
    # text path
    p = draw.Path(stroke='none', stroke_width=2, fill='none')
    d.append(draw.Text(overlap_text, 8, path=p, text_anchor='middle'))
    p.M(0, -radius).L(0, radius)
    d.append(p)

    # place the years on the circle as well
    p = draw.Arc(0, 0, radius + 2, 270, 90, cw=True,
                 stroke='none', stroke_width=3, fill='none')
    d.append(draw.Text(year_old, 8, path=p, text_anchor='middle'))
    p = draw.Arc(0, 0, radius + 2, 90, 270, cw=True,
                 stroke='none', stroke_width=3, fill='none')
    d.append(draw.Text(year_new, 8, path=p, text_anchor='middle'))
    # -------------------------------------------------

    d.setPixelScale(2)  # Set number of pixels per geometry unit
    # d.setRenderSize(400,200)  # Alternative to setPixelScale
    d.saveSvg('example.svg')


if __name__ == '__main__':
    # replace_text_in_svg('template.svg', "vorige wc-rol", "2000", "volgende wc-rol", "2001", "test_output", 20)
    create_svg("vorige wc-rol", "2000", "volgende wc-rol", "2001", "test_output", ["wc-rol", "test", "3"], 0, 20)
