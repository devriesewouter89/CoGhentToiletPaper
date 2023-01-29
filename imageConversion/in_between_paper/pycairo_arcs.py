import cairo
import math

from collections import namedtuple

# from https://gist.github.com/iluvcapra/ed9d659176a4a51cd930a7137cd46a4c


def warp_path(ctx, function):
    first = True

    for type, points in ctx.copy_path():
        if type == cairo.PATH_MOVE_TO:
            if first:
                ctx.new_path()
                first = False
            x, y = function(*points)
            ctx.move_to(x, y)

        elif type == cairo.PATH_LINE_TO:
            x, y = function(*points)
            ctx.line_to(x, y)

        elif type == cairo.PATH_CURVE_TO:
            x1, y1, x2, y2, x3, y3 = points
            x1, y1 = function(x1, y1)
            x2, y2 = function(x2, y2)
            x3, y3 = function(x3, y3)
            ctx.curve_to(x1, y1, x2, y2, x3, y3)

        elif type == cairo.PATH_CLOSE_PATH:
            ctx.close_path()


def make_arc_method(capture_radius, capture_angle):
    assert (capture_radius != 0)
    if capture_radius < 0.:
        capture_angle = capture_angle + math.pi

    def arc(x, y):
        r = -y
        theta = (x) / capture_radius
        xnew = r * math.cos(-theta - capture_angle)
        ynew = r * math.sin(theta + capture_angle)
        return xnew, ynew

    return arc


Sector = namedtuple('Sector', ['inside_radius', 'outside_radius', 'angle1', 'angle2', 'negative'])


def text_arc_dimensions(context, text, radius, angle):
    """
    Get dimensions of a text arc
    :param context  The cairo `context`
    :param text     The text
    :param radius   Radius of the baseline of the arc. If positive, text
          will ascend away from the origin. If negative, text will
          ascend towards the origin
    :param angle    The angle of the text origin
    :returns a Sector

    returns (baseline_radius, ascender_radius, left_angle, right_angle)
    """
    extents = context.text_extents(text)
    assert (radius != 0)
    width = extents.width / radius
    height = math.copysign(extents.height, radius)
    baseline_radius = abs(radius)

    negative = False
    outside = 0.
    inside = 0.
    th1 = 0.
    th2 = 0.

    if radius > 0.:
        outside = baseline_radius + extents.height
        inside = baseline_radius
        th1 = angle
        th2 = angle + width
    else:
        negative = True
        outside = baseline_radius
        inside = baseline_radius - extents.height
        th1 = angle + width
        th2 = angle

    return Sector(inside_radius=inside, outside_radius=outside, angle1=th1, angle2=th2, negative=negative)


def text_arc_path(context, x, y, text, radius, angle):
    """
    Creates a text path along an arc
    x and y : the position of the arc center
    radius : the radius of the arc. If positive, text will ascend away from the origin.
      If negative, text will ascend towards the origin

    angle : The angle of the text origin.

    """
    context.save()
    context.translate(x, y)

    arc_function = make_arc_method(capture_radius=radius,
                                   capture_angle=angle)

    context.new_path()
    context.move_to(0., -radius)
    context.text_path(text)
    warp_path(context, arc_function)
    context.restore()


def sector(context, x, y, sector):
    context.new_path()
    context.arc(x, y, sector.inside_radius, sector.angle1, sector.angle2)
    context.arc_negative(x, y, sector.outside_radius, sector.angle2, sector.angle1)
    context.close_path()