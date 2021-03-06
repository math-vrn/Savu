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
.. module:: temp_loader
   :platform: Unix
   :synopsis: A class for loading standard tomography data in a variety of
    formats.

.. moduleauthor:: Nicola Wadeson <scientificsoftware@diamond.ac.uk>

"""

import h5py
import tempfile
import numpy as np

from savu.plugins.base_loader import BaseLoader
from savu.plugins.utils import register_plugin
from savu.data.data_structures.data_types.fabIO import FabIO


@register_plugin
class ImageLoader(BaseLoader):
    """
    Load any FabIO compatible formats (e.g. tiffs)

    :param angles: A python statement to be evaluated or a file. Default: None.
    :param frame_dim: Which dimension requires stitching? Default: 0.
    :param data_prefix: A file prefix for the data file. Default: None.
    :param dark_prefix: A file prefix for the dark field files. Default: None.
    :param flat_prefix: A file prefix for the flat field files. Default: None.
    """

    def __init__(self, name='ImageLoader'):
        super(ImageLoader, self).__init__(name)

    def setup(self):
        exp = self.exp
        data_obj = exp.create_data_object('in_data', 'tomo')

        rot = 0
        detY = 1
        detX = 2
        data_obj.set_axis_labels('rotation_angle.degrees',
                                 'detector_y.pixel',
                                 'detector_x.pixel')

        data_obj.add_pattern('PROJECTION', core_dir=(detX, detY),
                             slice_dir=(rot,))
        data_obj.add_pattern('SINOGRAM', core_dir=(detX, rot),
                             slice_dir=(detY,))

        path = exp.meta_data.get_meta_data("data_file")
        data_prefix = self.parameters['data_prefix']
        data_obj.data = FabIO(path, data_obj, [self.parameters['frame_dim']],
                              None, data_prefix)

        self.set_rotation_angles(data_obj)
        # read dark and flat images
        if self.parameters['dark_prefix'] is not None:
            dark = FabIO(path, data_obj, [self.parameters['frame_dim']], None,
                         self.parameters['dark_prefix'])
            shape = dark.get_shape()
            index = [slice(0, shape[i], 1) for i in range(len(shape))]
            data_obj.meta_data.set_meta_data('dark', dark[index].mean(0))
        else:
            data_obj.meta_data.set_meta_data(
                'dark', np.zeros(data_obj.data.image_shape))
        if self.parameters['flat_prefix'] is not None:
            flat = FabIO(path, data_obj, [self.parameters['frame_dim']],
                         None, self.parameters['flat_prefix'])
            shape = flat.get_shape()
            index = [slice(0, shape[i], 1) for i in range(len(shape))]
            data_obj.meta_data.set_meta_data('flat', flat[index].mean(0))
        else:
            data_obj.meta_data.set_meta_data(
                'flat', np.ones(data_obj.data.image_shape))

        # dummy file
        filename = path.split('/')[-1] + '.h5'
        data_obj.backing_file = \
            h5py.File(tempfile.mkdtemp() + '/' + filename, 'a')

        data_obj.set_shape(data_obj.data.get_shape())
        self.set_data_reduction_params(data_obj)

    def set_rotation_angles(self, data_obj):
        angles = self.parameters['angles']

        if angles is None:
            angles = np.linspace(0, 180, data_obj.data.get_shape()[0])
        else:
            try:
                exec("angles = " + angles)
            except:
                try:
                    angles = np.loadtxt(angles)
                except:
                    raise Exception('Cannot set angles in loader.')

        n_angles = len(angles)
        data_angles = data_obj.data.get_shape()[0]
        if data_angles != n_angles:
            raise Exception("The number of angles %s does not match the data "
                            "dimension length %s", n_angles, data_angles)
        data_obj.meta_data.set_meta_data("rotation_angle", angles)
