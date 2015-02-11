# Copyright 2014 Diamond Light Source Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. module:: ExampleMedianFilter
   :platform: Unix
   :synopsis: A plugin to filter each frame with a median filter

.. moduleauthor:: Mark Basham <scientificsoftware@diamond.ac.uk>

"""
import logging

from savu.plugins.filter import Filter
from savu.plugins.cpu_plugin import CpuPlugin

from savu.data import structures as st

import scipy.signal.signaltools as sig


class ExampleMedianFilter(Filter, CpuPlugin):
    """
    A plugin to filter each frame with a median filter The class name needs to
    be the CammelCase equivalent of the '_' separated filename, so for example
    this file needs to be called
    'example_median_filter.py'
    """

    def __init__(self):
        """
        This is where the class is designed, and we inherit from 2 classes, the
        first is the Filter class, which deals with splitting the job up for
        us, and provides some simple methods which we need to overload. The
        second is the CpuPlugin class which tells the framework that the
        processing that you are doing here runs on 1 cpu.
        """
        logging.debug("initialising Example Median Filter")
        logging.debug("Calling super to make sure that all superclases are " +
                      " initialised")
        super(ExampleMedianFilter,
              self).__init__("ExampleMedianFilter")

    def populate_default_parameters(self):
        """
        All plugins have the populate_default_patamters method, in this you
        need to add to the self.parameters dictionary any parameters which you
        wish the end user to ultimately be able to change, in this case we will
        let them define the size of the kernel we will use for out 3D median
        filter. We initialise this with a good default value, in this case a
        tuple of (3, 3, 3) If you wish to change the direction that the filter
        travels across the data, then you need to adjust the
        self.parameters['slice_direction'] = 0 
        entry to be a different value,
        i.e. 1 for sinogram direction.
        """
        logging.debug("Populating parameters from superclasses, must be done!")
        super(ExampleMedianFilter, self).populate_default_parameters()
        logging.debug("Populating Example Median Filter default parameters")
        self.parameters['kernel_size'] = (3, 3, 3)

    def get_filter_padding(self):
        """
        Plugins which extend the Filter class have a get_filter_padding call
        which Specifies the number of slices which get passed to the
        filter_frame method.  if this is zero, a 1 x n x m dataset will be
        passed, but if this is 5, then an 11 x n x m dataset will get passed
        for each slice Wrapping is provided at edge cases, so that filter_frame
        does not need to consider this.
        """
        logging.debug("Getting the filter width of Example Median Filter")
        padding = (self.parameters['kernel_size'][0] - 1) / 2
        return {st.CD_PROJECTION:padding}

    def filter_frame(self, data):
        """
        The second method we need to implement from the Filter class and the
        part of the code that actually does all the work. the input here 'data'
        will contain the 3D block of data to process, and we need to return the
        data for the single frame in the middle of this. In this case we use
        the scipy median filter with the 'kernmel_size' parameter, and return
        the same size data as you had originally.
        """
        logging.debug("Data frame recieved for processing of shape %s",
                      str(data.shape))
        result = sig.medfilt(data, self.parameters['kernel_size'])
        return result
