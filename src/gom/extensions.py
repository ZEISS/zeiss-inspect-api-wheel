#
# extensions.py - Type related classes
#
# (C) 2024 Carl Zeiss GOM Metrology GmbH
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

import gom.__common__

import inspect
from abc import ABC, abstractmethod


class ScriptedElement (ABC, gom.__common__.Contribution):
    '''
    This class is used to defined a scripted element. A scripted element is a user defined
    element type where configuration and computation are happening entirely in a python script
    so user defined behavior and visualization can be implemented.

    Working with stages
    -------------------

    Each scripted element must be computed for one or more stages. In the case of a preview or
    for simple project setups, computation is usually done for a single stage only. In case of
    a recalc, computation for many stages is usually required. To support both cases and keep it
    simple for beginners, the scripted elements are using two computation functions:

    - 'compute ()':       Computes the result for one single stage only. If nothing else is implemented,
                          this function will be called for each stage one by one and return the computed
                          value for that stage only. The stage for which the computation is performed is
                          passed via the functions script context, but does usually not matter as all input
                          values are already associates with that single stage.
    - 'compute_stages (): Computes the results for many (all) stages at once. The value parameters are 
                         vectors of the same size always, one entry per stage. This is the case even if 
                         there is just one stage in the project. The result is expected to be a result 
                         vector of the same size as these stage vectors. The script context passed to that
                         function will contain a list of stages of equal size matching the values stage
                         ordering.

    So for a project with stages, it is usually sufficient to just implement 'compute ()'. For increased
    performance or parallelization, 'computeAll ()' can then be implemented as a second step.    

    Stage indexing
    --------------

    Stages are represented by an integer index. No item reference or other resolvable types like
    "gom.script.project[...].stages['Stage #1']" are used because it is assumed that reaching over stage borders into
    other stages data domain will lead to incorrect or missing dependencies. Instead, if vectorized data or data tensors
    are fetched, the stage sorting within that object will match that stages vector in the context. In the best case, the
    stage vector is just a consecutive range of numbers (0, 1, 2, 3, ...) which match the index in a staged tensor.
    Nevertheless, the vector can be number entirely different depending on active/inactive stages, stage sorting, ...

    @attention Usually, it is *not* possible to access arbitrary stages of other elements due to recalc restrictions !
    '''

    def __init__(self, name: str, element_type: str, category: str):
        '''
        Constructor

        @param name         Human readable element type name
        @param element_type Type of the generated element (point, line, ...)
        @param category     Contribution category
        '''
        super().__init__(name=name, category=category,
                         callables={
                             'dialog': self.dialog,
                             'compute_stages': self.compute_stages
                         },
                         properties={
                             'element_type': element_type
                         })

    @abstractmethod
    def dialog(self, context, **kwargs):
        pass

    @abstractmethod
    def compute(self, context, **kwargs):
        '''
        This function is called for a single stage value is to be computed. The input values from the
        associated dialog function are passed as 'kwargs' parameters - one value as one specific
        parameter named as the associated input widget.

        @param context Script context object containing execution related parameters. This includes
                       the stage this computation call refers to.
        @param kwargs  Placeholder for the later resolved input value parameters
        '''
        pass

    def compute_stages(self, context, **kwargs):
        '''
        This function is called to compute multiple stages of the scripted element. The expected result is 
        a vector of the same length as the number of stages.

        The function is calling the 'compute ()' function of the scripted element for each stage by default.
        For a more efficient implementation, it can be overwritten and bulk compute many stages at once.
        '''

        result = []

        #
        # The 'compute ()' function can have an arbitrary set of parameters, where each parameter must match the name of
        # a widget in the scripted elements dialog. Such, the values of each widgets in that dialog are passed through the
        # call stack but just a few of these are expected by the actual 'compute ()' function defined by its parameter set.
        # The remaining widget values are filtered here.
        #
        params = inspect.signature(self.compute).parameters

        has_args = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params.values())
        has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())

        if not (has_args or has_kwargs):
            kwargs = {k: v for k, v in kwargs.items() if k in params}

        for stage in context.stages:
            context.stage = stage
            result.append(self.compute(context, **kwargs))

        return result


class ScriptedActual (ScriptedElement):
    '''
    This class is used to define a scripted actual element.
    '''

    def __init__(self, name: str, element_type: str):
        '''
        Constructor

        @param name         Human readable element type name
        @param element_type Type of the generated element (point, line, ...)
        '''
        super().__init__(name=name, element_type=element_type, category='scriptedelement.actual')


class ScriptedCheck (ScriptedElement):
    '''
    This class is used to define a scripted check element.
    '''

    def __init__(self, name: str, element_type: str):
        '''
        Constructor

        @param name         Human readable element type name
        @param element_type Type of the generated element (point, line, ...)
        '''
        super().__init__(name=name, element_type=element_type, category='scriptedelement.check')
