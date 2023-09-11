#!/usr/bin/env python
# coding: utf8
#
# Copyright (c) 2022 Centre National d'Etudes Spatiales (CNES).
#
# This file is part of demcompare
# (see https://github.com/CNES/demcompare).
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
#
"""
Mainly contains the DemRepresentationTemplate class.
"""
# Standard imports
from abc import ABCMeta, abstractmethod
from typing import Dict

# Third party imports
import xarray as xr


class DemRepresentationTemplate(
    metaclass=ABCMeta
):  # pylint:disable=too-few-public-methods
    """
    DEM representation class
    """

    # Default DEM representation type
    DEFAULT_TYPE = "dem"

    def __init__(
        self, parameters: Dict = None
    ):  # pylint:disable = unused-argument
        """
        Initialization of a DEM representation object

        :param parameters: optional input parameters
        :type parameters: str
        :return: None
        """

        # DEM representation type
        self.type = self.DEFAULT_TYPE

    @abstractmethod
    def compute_and_save_image_plots(
        self,
        dem: xr.Dataset,
        plot_path: str = None,
        fig_title: str = None,
        colorbar_title: str = None,
        cmap: str = "terrain",
    ) -> xr.Dataset:
        """
        DEM representation method
        """
