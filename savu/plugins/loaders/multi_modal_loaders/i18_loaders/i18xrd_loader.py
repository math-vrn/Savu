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
.. module:: I18stxm_loader
   :platform: Unix
   :synopsis: A class for loading I18's stxm data

.. moduleauthor:: Aaron Parsons <scientificsoftware@diamond.ac.uk>

"""

from savu.plugins.loaders.multi_modal_loaders.base_i18_multi_modal_loader \
    import BaseI18MultiModalLoader

from savu.data.data_structures.data_types.fabIO import FabIO
from savu.plugins.utils import register_plugin
import h5py
import tempfile
import logging
import math
import os
import savu.test.test_utils as tu


@register_plugin
class I18xrdLoader(BaseI18MultiModalLoader):
    """
    A class to load tomography data from an NXstxm file
    :param data_path: Path to the folder containing the \
        data. Default: 'Savu/test_data/data/image_test/tiffs'.
    :param calibration_path: path to the calibration \
        file. Default: "Savu/test_data/data/LaB6_calibration_output.nxs".
    """

    def __init__(self, name='I18xrdLoader'):
        super(I18xrdLoader, self).__init__(name)

    def setup(self):
        """
         Define the input nexus file

        :param path: The full path of the NeXus file to load.
        :type path: str
        """
        data_obj = self.multi_modal_setup('xrd')
        
        scan_pattern = self.parameters['scan_pattern']
        frame_dim = range(len(scan_pattern))
        shape = []
        
        for pattern in self.parameters['scan_pattern']:
            if pattern == 'rotation':
                pattern = 'rotation_angle'
            shape.append(len(data_obj.meta_data.get_meta_data(pattern)))

        path = self.get_path('data_path')#self.parameters['data_path']
        
        data_obj.data = FabIO(path, data_obj, frame_dim, shape=tuple(shape))

        # dummy file
        filename = path.split('/')[-1] + '.h5'
        data_obj.backing_file = \
            h5py.File(tempfile.mkdtemp() + '/' + filename, 'a')

        data_obj.set_shape(data_obj.data.get_shape())

        self.set_motors(data_obj, 'xrd')
        self.add_patterns_based_on_acquisition(data_obj, 'xrd')
        self.set_data_reduction_params(data_obj)
        calibrationfile = h5py.File(self.get_path('calibration_path'), 'r')
        # lets just make this all in meters and convert for pyfai in the base integrator
        try:
            logging.debug('testing the version of the calibration file')
            det_str = 'entry1/instrument/detector'
            mData = data_obj.meta_data
            xpix = calibrationfile[det_str + '/detector_module/fast_pixel_direction'].value*1e-3 # in metres
            mData.set_meta_data("x_pixel_size",xpix)
            
            mData.set_meta_data("beam_center_x",
                    calibrationfile[det_str + '/beam_center_x'].value*1e-3) #in metres 
            mData.set_meta_data("beam_center_y",
                            calibrationfile[det_str + '/beam_center_y'].value*1e-3) # in metres
            mData.set_meta_data("distance",
                            calibrationfile[det_str + '/distance'].value*1e-3) # in metres
            mData.set_meta_data("incident_wavelength",
                            calibrationfile['/entry1/calibration_sample/beam'
                                            '/incident_wavelength'].value*1e-10) # in metres
            mData.set_meta_data("yaw", -calibrationfile[det_str + '/transformations/euler_b'].value)# in degrees
            mData.set_meta_data("roll",calibrationfile[det_str + '/transformations/euler_c'].value-180.0)# in degrees
            logging.debug('.... its the version in DAWN 2.0')
        except KeyError:
            try:
                det_str = 'entry/instrument/detector'
                mData = data_obj.meta_data
                xpix = calibrationfile[det_str + '/x_pixel_size'].value * 1e-3
                mData.set_meta_data("x_pixel_size", xpix) # in metres
                mData.set_meta_data("beam_center_x",
                        calibrationfile[det_str + '/beam_center_x'].value*xpix)# in metres
                mData.set_meta_data("beam_center_y",
                                calibrationfile[det_str + '/beam_center_y'].value*xpix) # in metres
                mData.set_meta_data("distance",
                                calibrationfile[det_str + '/distance'].value*1e-3) # in metres
                mData.set_meta_data("incident_wavelength",
                                calibrationfile['/entry/calibration_sample/beam'
                                                '/incident_wavelength'].value*1e-10)# in metres
                orien = calibrationfile[det_str + '/detector_orientation'][...].reshape((3, 3))
                yaw = math.degrees(-math.atan2(orien[2, 0], orien[2, 2]))# in degrees
                roll = math.degrees(-math.atan2(orien[0, 1], orien[1, 1]))# in degrees
                
                mData.set_meta_data("yaw", -yaw)
                mData.set_meta_data("roll", roll)
                logging.debug('.... its the legacy version pre-DAWN 2.0')
            except KeyError:
                logging.warn("We don't know what type of calibration file this is")

        self.set_data_reduction_params(data_obj)
        calibrationfile.close()

    def get_path(self,field):
        path = self.parameters[field]
        if path.split(os.sep)[0] == 'Savu':
            path = tu.get_test_data_path(path.split('/test_data/data')[1])
        return path

