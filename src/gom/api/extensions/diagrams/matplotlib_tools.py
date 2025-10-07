#
# api/extensions/diagrams/__init__.py - gom.api infrastructure access classes
#
# (C) 2023 Carl Zeiss GOM Metrology GmbH
#
# Use of this source code and binary forms of it, without modification, is permitted provided that
# the following conditions are met:
#
# 1. Redistribution of this source code or binary forms of this with or without any modifications is
#    not allowed without specific prior written permission by GOM.
#
# As this source code is provided as glue logic for connecting the Python interpreter to the commands of
# the GOM software any modification to this sources will not make sense and would affect a suitable functioning
# and therefore shall be avoided, so consequently the redistribution of this source with or without any
# modification in source or binary form is not permitted as it would lead to malfunctions of GOM Software.
#
# 2. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or
#    promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

import gom
import io
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

#
# Configure matplotlib for SVG output only. Otherwise the 'qtagg' renderer will be used in the background
# which relies on a properly initialized graphics device
#
matplotlib.use('svg')

#
# The SVG backend of matplotlib uses a fixed dpi value, that we need to consider when setting up plots
#
SVG_FIXED_DPI = 72


def setup_plot(plt, view, adjust_dpi=False):
    '''
    This function creates a matplotlib figure matching the view setup of a scripted diagram rendering view

    It can be used to construct a drawing foundation for matplotlib outputs which will fit well into
    the application's view and reporting snapshots.

    @param plt  Matplotlib instance which should be setup 
    @param view View configuration
    @param adjust_dpi If 'True', automatically adjust the plot to be compatible with the fixed dpi of the SVG renderer, e.g., scaling the font size

    @return the created figure
    '''
    width = view['width']
    height = view['height']
    dpi = view['dpi']

    scale = 1
    if adjust_dpi:
        scale = SVG_FIXED_DPI / dpi
        dpi = SVG_FIXED_DPI
    #
    # The aspect ratio 2:1 is defined in the 'SVGDiagram.json' file as 'requested_height'
    #
    plt.rcParams['font.size'] = view['font']['size'] * scale
    return plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)


def create_svg(plt, view, close_plot=True, tight_export=True):
    '''
    Create SVG representation from the given matplotlib instance

    @param plt  Matplotlib instance
    @param view View configuration
    @param close_plot If 'True' 'plt.close()' will be called after creating the svg, otherwise the user needs to take care of this himself.
    @return Rendered matplotlib graph in SVG format
    '''
    out = io.StringIO()
    plt.tight_layout()
    plt.savefig(out, bbox_inches=('tight' if tight_export else None), format='svg', dpi=view['dpi'])
    text = out.getvalue()

    out.close()
    if close_plot:
        plt.close()

    return text


def get_overlay_coords(view, bbox, x, y, x_min, x_max, y_min, y_max):
    '''
    Convert an Array of axis coordinates to normed pixel coordinates for overlay creation
    Sets axis limits depending on the maximum values in x and y (if changed later, overlay can be inaccurate)

    @param view     view parameters from the plot function
    @param bbox     Bounding box of the current axis (plt.gca().get_position())
    @param x        Array of axis x-coordinates 
    @param y        Array of axis y-coordinates
    @param x_min    Minimum x-value on the axis
    @param x_max    Maximum x-value on the axis
    @param y_min    Minimum y-value on the axis
    @param y_max    Maximum y-value on the axis

    @return     Arrays x, y of normed pixel coordinates to be included in the element coords
    '''
    width = view['width']
    height = view['height']

    x = np.asarray(x)
    y = np.asarray(y)
    x_norm = np.zeros(len(x))
    y_norm = np.zeros(len(y))

    offset_x = bbox.x0 * width
    relative_width = bbox.x0 + (1 - bbox.x1)
    offset_y = bbox.y0 * height
    relative_height = bbox.y0 + (1 - bbox.y1)
    # Normalize data coordinates to [0,1]
    for i in range(len(x)):
        x_ntemp = ((x[i] - x_min) / (x_max - x_min))
        y_ntemp = ((y[i] - y_min) / (y_max - y_min))
        x_ptemp = x_ntemp * width * (1 - relative_width)
        y_ptemp = y_ntemp * height * (1 - relative_height)
        x_norm[i] = (x_ptemp + offset_x) / width
        y_norm[i] = (height - y_ptemp - offset_y) / height
    return x_norm, y_norm


def get_display_coords(axes, points, view):
    '''
    Calculate the relative display coordinates of a points list based on a given matplotlib Axes object

    @param axes The Axes object to base the transformation on
    @param points List of points plotted in the axes

    @return List of transformed points in the relative coordinates of the overall plot
            (each coordinate will be from the interval [0,1] if the original point within figure boundary)
    '''

    width = view['width']
    height = view['height']

    # Scale point by width and height and flip the y-Axis
    # (matplotlib coordinate system starts in lower-left corner, while javascript coordinates start at upper-left corner)
    def transform_raw(point):
        return [point[0] / width, 1 - point[1] / height]

    raw_display = axes.transData.transform(points)
    return np.apply_along_axis(transform_raw, 1, raw_display)
