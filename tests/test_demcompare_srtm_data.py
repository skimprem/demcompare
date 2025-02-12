#!/usr/bin/env python
# coding: utf8
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
# pylint:disable=duplicate-code

"""
This module contains functions to test Demcompare end2end with
the "srtm_test_data" test root data
"""

# Standard imports
import os
from tempfile import TemporaryDirectory

# Third party imports
import numpy as np
import pytest

# Demcompare imports
import demcompare
from demcompare.helpers_init import read_config_file, save_config_file

# Tests helpers
from .helpers import (
    TEST_TOL,
    assert_same_images,
    demcompare_test_data_path,
    read_csv_file,
    temporary_dir,
)


@pytest.mark.end2end_tests
@pytest.mark.functional_tests
def test_demcompare_srtm_test_data():
    """
    Demcompare with strm_test_data main end2end test.
    Input data:
    - Input dems and configuration present in the
      "strm_test_data/input" test data directory
    Validation data:
    - Output data present in the
      "strm_test_data/ref_output" test data directory
    Validation process:
    - Reads the input configuration file
    - Runs demcompare on a temporary directory
    - Checks that the output files are the same as ground truth
    - Checked files: test_config.json, coregistration_results.json,
      dem_for_stats.tif, coreg_SEC.tif,
      reproj_coreg_REF.tif, reproj_coreg_SEC.tif,
      classif_layer/stats_results.csv,
      classif_layer/stats_results_intersection.csv,
      classif_layer/stats_results_exclusion.csv,
      classif_layer/ref_rectified_support_map.tif,
      classif_layer/sec_rectified_support_map.tif
    """
    # Get "srtm_test_data" test root data directory absolute path
    test_data_path = demcompare_test_data_path("srtm_test_data")

    # Load "srtm_test_data" demcompare config from input/test_config.json
    test_cfg_path = os.path.join(test_data_path, "input/test_config.json")
    test_cfg = read_config_file(test_cfg_path)

    # Get "srtm_test_data" demcompare reference output path for
    test_ref_output_path = os.path.join(test_data_path, "ref_output")

    # Create temporary directory for test output
    with TemporaryDirectory(dir=temporary_dir()) as tmp_dir_:
        # Modify test's output dir in configuration to tmp test dir
        test_cfg["output_dir"] = tmp_dir_
        # Manually set the saving of internal dems to True
        test_cfg["coregistration"]["save_optional_outputs"] = True

        # Set a new test_config tmp file path
        tmp_cfg_file = os.path.join(tmp_dir_, "test_config.json")

        # Save the new configuration inside the tmp dir
        save_config_file(tmp_cfg_file, test_cfg)

        # Run demcompare with "srtm_test_data"
        # configuration (and replace conf file)
        demcompare.run(tmp_cfg_file)

        # TEST JSON CONFIGURATION
        # Check initial config "test_config.json"
        cfg_file = "test_config.json"
        ref_output_cfg = read_config_file(
            os.path.join(test_ref_output_path, cfg_file)
        )
        # Manually add output directory on reference output cfg
        ref_output_cfg["statistics"]["alti-diff"]["output_dir"] = (
            tmp_dir_ + "/stats" + "/alti-diff"
        )
        ref_output_cfg["coregistration"]["output_dir"] = (
            tmp_dir_ + "/coregistration"
        )

        output_cfg = read_config_file(os.path.join(tmp_dir_, cfg_file))
        np.testing.assert_equal(
            ref_output_cfg["statistics"]["alti-diff"],
            output_cfg["statistics"]["alti-diff"],
        )
        np.testing.assert_equal(
            ref_output_cfg["coregistration"], output_cfg["coregistration"]
        )

        # Test coregistration_results.json
        cfg_file = "./coregistration/coregistration_results.json"
        ref_coregistration_results = read_config_file(
            os.path.join(test_ref_output_path, cfg_file)
        )

        coregistration_results = read_config_file(
            os.path.join(tmp_dir_, cfg_file)
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dx"][
                "total_bias_value"
            ],
            coregistration_results["coregistration_results"]["dx"][
                "total_bias_value"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dy"][
                "total_bias_value"
            ],
            coregistration_results["coregistration_results"]["dy"][
                "total_bias_value"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dx"][
                "nuth_offset"
            ],
            coregistration_results["coregistration_results"]["dx"][
                "nuth_offset"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dy"][
                "nuth_offset"
            ],
            coregistration_results["coregistration_results"]["dy"][
                "nuth_offset"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dx"][
                "total_offset"
            ],
            coregistration_results["coregistration_results"]["dx"][
                "total_offset"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dy"][
                "total_offset"
            ],
            coregistration_results["coregistration_results"]["dy"][
                "total_offset"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"][
                "gdal_translate_bounds"
            ]["lry"],
            coregistration_results["coregistration_results"][
                "gdal_translate_bounds"
            ]["lry"],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"][
                "gdal_translate_bounds"
            ]["lrx"],
            coregistration_results["coregistration_results"][
                "gdal_translate_bounds"
            ]["lrx"],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"][
                "gdal_translate_bounds"
            ]["uly"],
            coregistration_results["coregistration_results"][
                "gdal_translate_bounds"
            ]["uly"],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"][
                "gdal_translate_bounds"
            ]["ulx"],
            coregistration_results["coregistration_results"][
                "gdal_translate_bounds"
            ]["ulx"],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dz"][
                "total_bias_value"
            ],
            coregistration_results["coregistration_results"]["dz"][
                "total_bias_value"
            ],
        )
        assert (
            os.path.normpath(
                ref_coregistration_results["coregistration_results"][
                    "reproj_coreg_ref"
                ]["path"]
            ).split(os.path.sep)[-1]
            == os.path.normpath(
                coregistration_results["coregistration_results"][
                    "reproj_coreg_ref"
                ]["path"]
            ).split(os.path.sep)[-1]
        )
        assert (
            os.path.normpath(
                ref_coregistration_results["coregistration_results"][
                    "reproj_coreg_sec"
                ]["path"]
            ).split(os.path.sep)[-1]
            == os.path.normpath(
                coregistration_results["coregistration_results"][
                    "reproj_coreg_sec"
                ]["path"]
            ).split(os.path.sep)[-1]
        )

        # TEST DIFF TIF

        # Test dem_for_stats.tif
        img = os.path.join("stats", "alti-diff", "dem_for_stats.tif")
        ref_output_data = os.path.join(test_ref_output_path, img)
        output_data = os.path.join(tmp_dir_, img)
        assert_same_images(ref_output_data, output_data, atol=TEST_TOL)

        # Test coreg_SEC.tif
        img = "./coregistration/coreg_SEC.tif"
        ref_output_data = os.path.join(test_ref_output_path, img)
        output_data = os.path.join(tmp_dir_, img)
        assert_same_images(ref_output_data, output_data, atol=TEST_TOL)

        # Test reproj_coreg_SEC.tif
        img = "./coregistration/reproj_coreg_SEC.tif"
        ref_output_data = os.path.join(test_ref_output_path, img)
        output_data = os.path.join(tmp_dir_, img)
        assert_same_images(ref_output_data, output_data, atol=TEST_TOL)

        # Test reproj_coreg_REF.tif
        img = "./coregistration/reproj_coreg_REF.tif"
        ref_output_data = os.path.join(test_ref_output_path, img)
        output_data = os.path.join(tmp_dir_, img)
        assert_same_images(ref_output_data, output_data, atol=TEST_TOL)

        # TESTS CSV STATS

        # Test dem_for_stats_pdf.csv
        file = os.path.join("stats", "alti-diff", "dem_for_stats_pdf.csv")
        ref_output_csv = read_csv_file(os.path.join(test_ref_output_path, file))
        output_csv = read_csv_file(os.path.join(tmp_dir_, file))
        np.testing.assert_allclose(ref_output_csv, output_csv, atol=TEST_TOL)

        # Test dem_for_stats_cdf.csv
        file = os.path.join("stats", "alti-diff", "dem_for_stats_cdf.csv")
        ref_output_csv = read_csv_file(os.path.join(test_ref_output_path, file))
        output_csv = read_csv_file(os.path.join(tmp_dir_, file))
        np.testing.assert_allclose(ref_output_csv, output_csv, atol=TEST_TOL)

        # TEST CSV STATS

        # Test stats/Slope0/stats_results.csv
        file = "stats/alti-diff/Slope0/stats_results.csv"
        ref_output_csv = read_csv_file(os.path.join(test_ref_output_path, file))
        output_csv = read_csv_file(os.path.join(tmp_dir_, file))
        np.testing.assert_allclose(ref_output_csv, output_csv, atol=TEST_TOL)

        # Test stats/Slope0/stats_results_exclusion.csv
        file = "stats/alti-diff/Slope0/stats_results_exclusion.csv"
        ref_output_csv = read_csv_file(os.path.join(test_ref_output_path, file))
        output_csv = read_csv_file(os.path.join(tmp_dir_, file))
        np.testing.assert_allclose(ref_output_csv, output_csv, atol=TEST_TOL)

        # Test stats/Slope0/stats_results_intersection.csv
        file = "stats/alti-diff/Slope0/stats_results_intersection.csv"
        ref_output_csv = read_csv_file(os.path.join(test_ref_output_path, file))
        output_csv = read_csv_file(os.path.join(tmp_dir_, file))
        np.testing.assert_allclose(ref_output_csv, output_csv, atol=TEST_TOL)


@pytest.mark.end2end_tests
@pytest.mark.functional_tests
def test_demcompare_srtm_test_data_with_roi():
    """
    Demcompare with srtm_test_data_with_roi main end2end test.
    Input data:
    - Input dems and configuration present in the
      "srtm_test_data_with_roi/input" test data directory
    Validation data:
    - Output data present in the
      "srtm_test_data_with_roi/ref_output" test data directory
    Validation process:
    - Reads the input configuration file
    - Runs demcompare on a temporary directory
    - Checks that the output files are the same as ground truth
    - Checked files: test_config.json, coregistration_results.json,
      dem_for_stats.tif, coreg_SEC.tif,
      reproj_coreg_REF.tif, reproj_coreg_SEC.tif,
      classif_layer/stats_results.csv,
      classif_layer/stats_results_intersection.csv
    """
    # Get "srtm_test_data_with_roi" test root
    # data directory absolute path
    test_data_path = demcompare_test_data_path("srtm_test_data_with_roi")

    # Load "srtm_test_data_with_roi" demcompare
    # config from input/test_config.json
    test_cfg_path = os.path.join(test_data_path, "input/test_config.json")
    test_cfg = read_config_file(test_cfg_path)

    # Get "srtm_test_data_with_roi" demcompare reference output path for
    test_ref_output_path = os.path.join(test_data_path, "ref_output")

    # Create temporary directory for test output
    with TemporaryDirectory(dir=temporary_dir()) as tmp_dir:
        # Modify test's output dir in configuration to tmp test dir
        test_cfg["output_dir"] = tmp_dir
        # Manually set the saving of internal dems to True
        test_cfg["coregistration"]["save_optional_outputs"] = True

        # Set a new test_config tmp file path
        tmp_cfg_file = os.path.join(tmp_dir, "test_config.json")

        # Save the new configuration inside the tmp dir
        save_config_file(tmp_cfg_file, test_cfg)

        # Run demcompare with "srtm_test_data" configuration
        # (and replace conf file)
        demcompare.run(tmp_cfg_file)

        # Now test demcompare output with test ref_output:

        # TEST JSON CONFIGURATION

        # Check initial config "test_config.json"
        cfg_file = "test_config.json"
        ref_output_cfg = read_config_file(
            os.path.join(test_ref_output_path, cfg_file)
        )
        # Manually add output directory on reference output cfg
        ref_output_cfg["statistics"]["alti-diff"]["output_dir"] = (
            tmp_dir + "/stats" + "/alti-diff"
        )
        ref_output_cfg["coregistration"]["output_dir"] = (
            tmp_dir + "/coregistration"
        )

        output_cfg = read_config_file(os.path.join(tmp_dir, cfg_file))

        np.testing.assert_equal(
            ref_output_cfg["statistics"]["alti-diff"],
            output_cfg["statistics"]["alti-diff"],
        )
        np.testing.assert_equal(
            ref_output_cfg["coregistration"], output_cfg["coregistration"]
        )

        # Test coregistration_results.json
        cfg_file = "./coregistration/coregistration_results.json"
        ref_coregistration_results = read_config_file(
            os.path.join(test_ref_output_path, cfg_file)
        )

        coregistration_results = read_config_file(
            os.path.join(tmp_dir, cfg_file)
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dx"][
                "total_bias_value"
            ],
            coregistration_results["coregistration_results"]["dx"][
                "total_bias_value"
            ],
        )

        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dy"][
                "total_bias_value"
            ],
            coregistration_results["coregistration_results"]["dy"][
                "total_bias_value"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dx"][
                "nuth_offset"
            ],
            coregistration_results["coregistration_results"]["dx"][
                "nuth_offset"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dy"][
                "nuth_offset"
            ],
            coregistration_results["coregistration_results"]["dy"][
                "nuth_offset"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dx"][
                "total_offset"
            ],
            coregistration_results["coregistration_results"]["dx"][
                "total_offset"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dy"][
                "total_offset"
            ],
            coregistration_results["coregistration_results"]["dy"][
                "total_offset"
            ],
        )
        np.testing.assert_equal(
            ref_coregistration_results["coregistration_results"]["dz"][
                "total_bias_value"
            ],
            coregistration_results["coregistration_results"]["dz"][
                "total_bias_value"
            ],
        )

        # TEST DIFF TIF

        # Test dem_for_stats.tif
        img = os.path.join("stats", "alti-diff", "dem_for_stats.tif")
        ref_output_data = os.path.join(test_ref_output_path, img)
        output_data = os.path.join(tmp_dir, img)
        assert_same_images(ref_output_data, output_data, atol=TEST_TOL)

        # TESTS CSV STATS

        # Test dem_for_stats_pdf.csv
        file = os.path.join("stats", "alti-diff", "dem_for_stats_pdf.csv")
        ref_output_csv = read_csv_file(os.path.join(test_ref_output_path, file))
        output_csv = read_csv_file(os.path.join(tmp_dir, file))
        np.testing.assert_allclose(ref_output_csv, output_csv, atol=TEST_TOL)

        # Test dem_for_stats_cdf.csv
        file = os.path.join("stats", "alti-diff", "dem_for_stats_cdf.csv")
        ref_output_csv = read_csv_file(os.path.join(test_ref_output_path, file))
        output_csv = read_csv_file(os.path.join(tmp_dir, file))
        np.testing.assert_allclose(ref_output_csv, output_csv, atol=TEST_TOL)

        # TEST CSV STATS

        # Test stats/Slope0/stats_results.csv
        file = "stats/alti-diff/Slope0/stats_results.csv"
        ref_output_csv = read_csv_file(os.path.join(test_ref_output_path, file))
        output_csv = read_csv_file(os.path.join(tmp_dir, file))
        np.testing.assert_allclose(ref_output_csv, output_csv, atol=TEST_TOL)

        # Test stats/Slope0/stats_results_intersection.csv
        file = "stats/alti-diff/Slope0/stats_results_intersection.csv"
        ref_output_csv = read_csv_file(os.path.join(test_ref_output_path, file))
        output_csv = read_csv_file(os.path.join(tmp_dir, file))
        np.testing.assert_allclose(ref_output_csv, output_csv, atol=TEST_TOL)
