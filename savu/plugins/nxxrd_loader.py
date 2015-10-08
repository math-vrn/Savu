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
.. module:: tomography_loader
   :platform: Unix
   :synopsis: A class for loading tomography data using the standard loaders
   library.

.. moduleauthor:: Nicola Wadeson <scientificsoftware@diamond.ac.uk>

"""
import os
import logging
import h5py

from savu.core.utils import logmethod
from savu.plugins.base_multi_modal_loader import BaseMultiModalLoader
from savu.test import test_utils as tu
from savu.plugins.utils import register_plugin


@register_plugin
class NxxrdLoader(BaseMultiModalLoader):
    """
    A class to load tomography data from an NXxrd file

    :param calibration_path: path to the calibration file. Default: "../../test_data/LaB6_calibration_output.nxs"
    """

    def __init__(self, name='NxxrdLoader'):
        super(NxxrdLoader, self).__init__(name)

    @logmethod
    def setup(self):
        data_str = '/instrument/detector/data'
        data_obj, xrd_entry = self.multi_modal_setup('NXxrd', data_str)
        mono_energy = data_obj.backing_file[
            xrd_entry.name + '/instrument/monochromator/energy']
        self.exp.meta_data.set_meta_data("mono_energy", mono_energy)

        self.set_motors(data_obj, xrd_entry, 'xrd')
        self.add_patterns_based_on_acquisition(data_obj, 'xrd')

        slicedir = range(len(data_obj.data.shape)-2)
        data_obj.add_pattern("DIFFRACTION", core_dir=(-2, -1),
                             slice_dir=slicedir)

        # now to load the calibration file
        if os.exists(self.parameters['calibration_path']):
            logging.info("Using the calibration file in the working directory")
            calibration_path = self.parameters['calibration_path']
        elif os.exists(tu.get_test_data_path(
                self.parameters['calibration_path'])):
            logging.info("Using the calibration path in the test directory")
            calibration_path = tu.get_test_data_path(
                self.parameters['calibration_path'])
        else:
            logging.info("No calibration file found!")
        calibrationfile = h5py.File(calibration_path, 'r')

        mData = data_obj.meta_data
        det_str = 'entry/instrument/detector'
        mData.set_meta_data("beam_center_x",
                            calibrationfile[det_str + '/beam_center_x'])
        mData.set_meta_data("beam_center_y",
                            calibrationfile[det_str + '/beam_center_y'])
        mData.set_meta_data("distance",
                            calibrationfile[det_str + '/distance'])
        mData.set_meta_data("incident_wavelength",
                            calibrationfile['/entry/calibration_sample/beam'
                                            '/incident_wavelength'])
        mData.set_meta_data("x_pixel_size",
                            calibrationfile[det_str + '/x_pixel_size'])
        mData.set_meta_data("detector_orientation",
                            calibrationfile[det_str + '/detector_orientation'])