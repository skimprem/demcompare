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
# Force protected-access to test protected functions
# pylint:disable=protected-access
"""
This module contains functions to test all the methods in
dataset_tools module.
- _interpolate_geoid is tested with test_get_geoid_offset
"""

# Standard imports
import os

# Third party imports
import numpy as np
import pytest

# Demcompare imports
from demcompare import dataset_tools, dem_tools
from demcompare.initialization import read_config_file

# Tests helpers
from .helpers import demcompare_path, demcompare_test_data_path


@pytest.mark.unit_tests
def test_reproject_dataset():
    """
    Test the reproject_dataset function
    Loads the DEMS present in "strm_test_data" and "gironde_test_data"
    test root data directory and reprojects one
    onto another to test the obtained
    reprojected DEMs.
    """
    # Generate the "reproject_on_dataset" with the
    # following data, transform and nodata
    # and "strm_test_data" DSM's georef
    data = np.ones((1000, 1000))
    trans = np.array(
        [
            4.00000000e01,
            8.33333333e-04,
            0.00000000e00,
            4.00000000e01,
            0.00000000e00,
            -8.33333333e-04,
        ]
    )
    nodata = -33

    # Get "strm_test_data" test
    # root data directory absolute path
    test_data_path = demcompare_test_data_path("strm_test_data")
    # Load "gironde_test_data" demcompare
    # config from input/test_config.json
    test_cfg_path = os.path.join(test_data_path, "input/test_config.json")
    cfg = read_config_file(test_cfg_path)
    reproject_on_dataset = dem_tools.create_dem(
        data=data,
        transform=trans,
        input_img=cfg["input_dem_to_align"]["path"],
        no_data=nodata,
    )

    # Generate the "dataset_to_be_reprojected" with
    # the following data, transform and nodata
    # and "gironde_test_data" DSM's georef
    data = np.ones((1000, 1000))
    trans = np.array([600000, 50, 0, 600000, 0, 50])
    nodata = -32768

    # Get "gironde_test_data" test
    # root data directory absolute path
    test_data_path = demcompare_test_data_path("gironde_test_data")
    # Load "gironde_test_data" demcompare
    # config from input/test_config.json
    test_cfg_path = os.path.join(test_data_path, "input/test_config.json")
    cfg = read_config_file(test_cfg_path)

    dataset_to_be_reprojected = dem_tools.create_dem(
        data=data,
        transform=trans,
        input_img=cfg["input_dem_to_align"]["path"],
        no_data=nodata,
    )

    # Reproject the dataset_to_be_reprojected on
    # reproject_on_dataset
    output_reprojected_dataset = dataset_tools.reproject_dataset(
        dataset_to_be_reprojected, reproject_on_dataset
    )
    # Test that the output dataset now has the
    # transform of reproject_on_dataset
    np.testing.assert_allclose(
        reproject_on_dataset.georef_transform,
        output_reprojected_dataset.georef_transform,
        rtol=1e-02,
    )
    # Test that the output dataset now has the
    # georef of reproject_on_dataset
    assert (
        reproject_on_dataset.attrs["crs"]
        == output_reprojected_dataset.attrs["crs"]
    )
    # Test that the output dataset still has
    # its original no_data value
    np.testing.assert_allclose(
        dataset_to_be_reprojected.attrs["no_data"],
        output_reprojected_dataset.attrs["no_data"],
        rtol=1e-02,
    )


def test_get_geoid_offset():
    """
    Test the _get_geoid_offset function
    Loads the DEMS present in "strm_test_data" test root data
    directory and projects it on the geoid to test
    the obtained dataset's geoid offset values.
    """
    # Get "strm_test_data" test root data directory absolute path
    test_data_path = demcompare_test_data_path("strm_test_data")
    # Load "strm_test_data" demcompare config from input/test_config.json
    test_cfg_path = os.path.join(test_data_path, "input/test_config.json")
    cfg = read_config_file(test_cfg_path)
    # Geoid path
    geoid_path = demcompare_path("geoid/egm96_15.gtx")

    # Define data
    data = np.ones((2, 2))

    # Define transformation --------------------
    trans = np.array(
        [
            4.00000000e01,
            8.33333333e-04,
            0.00000000e00,
            4.00000000e01,
            0.00000000e00,
            -8.33333333e-04,
        ]
    )
    nodata = -32768
    # Create dataset from the strm_test_data
    # DSM with the defined data, bounds,
    # transform and nodata values
    dataset = dem_tools.create_dem(
        data=data,
        transform=trans,
        input_img=cfg["input_dem_to_align"]["path"],
        no_data=nodata,
    )

    # Define data coordinates
    gt_data_coords = np.array(
        [
            [40.0, 40.0],
            [40.00083333, 40.0],
            [40.0, 39.99916667],
            [40.00083333, 39.99916667],
        ]
    )

    # Get interpolated geoid values
    gt_interp_geoid = dataset_tools._interpolate_geoid(
        geoid_path, gt_data_coords, interpol_method="linear"
    )
    gt_arr_offset = np.reshape(gt_interp_geoid, dataset["image"].data.shape)

    # Get offset values
    output_arr_offset = dataset_tools._get_geoid_offset(dataset, geoid_path)

    # Test that the output_arr_offset is the same as ground_truth
    np.testing.assert_allclose(gt_arr_offset, output_arr_offset, rtol=1e-04)

    # Define transformation that will compute the data coordinates
    # outside of the geoid scope --------------------
    trans = np.array(
        [
            182.0,
            8.33333333e-04,
            0.00000000e00,
            91,
            0.00000000e00,
            -8.33333333e-04,
        ]
    )
    nodata = -32768
    # Create dataset from the gironde_test_data
    # DSM with the defined data, bounds,
    # transform and nodata values
    dataset = dem_tools.create_dem(
        data=data,
        transform=trans,
        input_img=cfg["input_dem_to_align"]["path"],
        no_data=nodata,
    )

    # Test that an error is raised
    with pytest.raises(ValueError):
        # Get geoid values
        dataset_tools._get_geoid_offset(dataset, geoid_path)
