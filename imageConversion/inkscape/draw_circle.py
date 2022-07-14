#!/usr/bin/env python
# coding=utf-8
import inkex
from inkex import Circle


class DrawCircle (inkex.EffectExtension):
    def effect(self):
        parent = self.svg.get_current_layer()
        style = {'stroke': '#000000', 'stroke-width': 1, 'fill': '#FF0000'}
        circle_attribs = {'style': str(inkex.Style(style)),
                          inkex.addNS('label', 'inkscape'): "mycircle",
                          'cx': '100', 'cy': '100',
                          'r': '100'}
        parent.add(Circle(**circle_attribs))


if __name__ == '__main__':
    DrawCircle().run()
