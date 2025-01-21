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

#
# Configure matplotlib for SVG output only. Otherwise the 'qtagg' renderer will be used in the background
# which relies on a properly initialized graphics device
#
matplotlib.use('svg')


def setup_plot(plt, view):
    '''
    This function creates a matplotlib figure matching the view setup of a scripted diagram rendering view

    It can be used to construct a drawing foundation for matplotlib outputs which will fit well into
    the applications view and reporting snapshots.

    @param plt  Matplotlib instance which should be setup 
    @param view View configuration
    '''
    width = view['width']
    height = view['height']
    dpi = view['dpi']

    #
    # The aspect ratio 2:1 is defined in the 'SVGDiagram.json' file as 'requested_height'
    #
    plt.rcParams['font.size'] = view['font']['size']
    plt.figure(figsize=(width / dpi, height / dpi), dpi=dpi)


def create_svg(plt, view):
    '''
    Create SVG representation from the given matplotlib instance

    @param plt  Matplotlib instance
    @param view View configuration
    @return Rendered matplotlib graph in SVG format
    '''
    out = io.StringIO()
    plt.tight_layout()
    plt.savefig(out, bbox_inches='tight', format='svg', dpi=view['dpi'])
    text = out.getvalue()

    out.close()
    plt.close()

    return text
