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
# pylint:disable=too-few-public-methods
"""
Mainly contains different DEM processing classes
"""
# pylint:disable=too-many-lines

import logging
from typing import Dict

import numpy as np

# Third party imports
import xarray as xr
from numpy.fft import fft2, ifft2, ifftshift

from demcompare.dem_tools import (
    accumulates_class_layers,
    compute_dem_slope,
    create_dem,
)
from demcompare.img_tools import (
    calc_spatial_freq_2d,
    compute_surface_normal,
    neighbour_interpol,
    remove_nan_and_flatten,
)

from .dem_processing import DemProcessing
from .dem_processing_template import DemProcessingTemplate


@DemProcessing.register("alti-diff")
class AltiDiff(DemProcessingTemplate):
    """
    Altitude difference between two DEMs
    """

    def __init__(self, parameters: Dict = None):
        """
        Initialization the DEM processing object
        :return: None
        """

        super().__init__()

        self.fig_title = "[REF - SEC] difference"
        self.colorbar_title = "Elevation difference (m)"
        self.cmap = "bwr"

    def compute_dems_diff(
        self,
        dem_1: xr.Dataset,
        dem_2: xr.Dataset,
    ) -> xr.Dataset:
        """
        Compute altitude difference dem_1 - dem_2 and
        return it as an xr.Dataset with the dem_2
        georeferencing and attributes.

        :param dem_1: dem_1 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_1: xr.Dataset
         :param dem_2: dem_2 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_2: xr.Dataset
        :return: difference xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """
        diff_raster = dem_1["image"].data - dem_2["image"].data

        diff_dem = create_dem(
            diff_raster,
            transform=dem_2.georef_transform.data,
            nodata=dem_1.attrs["nodata"],
            img_crs=dem_2.crs,
            bounds=dem_2.bounds,
        )
        return diff_dem

    def process_dem(
        self,
        dem_1: xr.Dataset,
        dem_2: xr.Dataset,
    ) -> xr.Dataset:
        """
        Compute the difference between dem_1 and dem_2.
        Add classification layers to the difference.

        :param dem_1: dem_1 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_1: xr.Dataset
        :param dem_2: dem_2 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_2: xr.Dataset
        :return: difference xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """
        diff = self.compute_dems_diff(dem_1, dem_2)
        diff = accumulates_class_layers(dem_1, dem_2, diff)
        return diff


@DemProcessing.register("alti-diff-slope-norm")
class AltiDiffSlopeNorm(DemProcessingTemplate):
    """
    Altitude difference between two DEMs normalized by the slope
    """

    def __init__(self, parameters: Dict = None):
        """
        Initialization the DEM processing object
        :return: None
        """

        super().__init__()

        self.fig_title = "[REF - SEC] difference normalized by the slope"
        self.colorbar_title = "Elevation difference normalized by the slope"
        self.cmap = "bwr"

    def compute_dems_diff_slope_norm(
        self,
        dem_1: xr.Dataset,
        dem_2: xr.Dataset,
    ) -> xr.Dataset:
        """
        Compute altitude difference dem_1 - dem_2,
        normalized by the slope of the DEM and
        return it as an xr.Dataset with the dem_2
        georeferencing and attributes.

        :param dem_1: dem_1 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_1: xr.Dataset
         :param dem_2: dem_2 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_2: xr.Dataset
        :return: difference normalized by the slope xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """
        diff_raster = dem_1["image"].data - dem_2["image"].data

        diff_raster = self.dh_compute_normalization_factor(diff_raster, dem_2)

        diff_dem = create_dem(
            diff_raster,
            transform=dem_2.georef_transform.data,
            nodata=dem_1.attrs["nodata"],
            img_crs=dem_2.crs,
            bounds=dem_2.bounds,
        )
        return diff_dem

    def dh_compute_normalization_factor(
        self, diff: np.ndarray, dem: xr.Dataset, nbins: int = 100
    ) -> np.ndarray:
        """
        Compute the normalization factor for several (nbins) slope classes.
        First: compute the tangent of the slope at each pixel.
        Then: compute the angle of the slope at each pixel.
        Then: classification of the pixels by the angle of the slope value.
        Then: compute the std of the error for each of the pixel classes
        Then: perform linear regression: a,b=regLin(tan(angle),std)
        Finally: Error normalization for each slope class:
        dh = dh/(1+b/a*tan(angle))

        :param diff: difference between the ref and sec DEMs
        :type diff: np.ndarray
        :param dem: dem xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem: xr.Dataset
        :param nbins: number of bins of the histogram
        :type nbins: int
        :return: altitude difference normalized by the slope
        :rtype: np.ndarray
        """

        if hasattr(dem, "ref_slope"):
            alpha = dem["ref_slope"].data
        else:
            dem = compute_dem_slope(dem)
            alpha = dem["ref_slope"].data

        tan_alpha = np.tan(alpha)

        no_nan = (~np.isnan(tan_alpha)) & (~np.isnan(diff))
        _, bin_alpha = np.histogram(alpha[no_nan], bins=nbins)

        # exclude extreme slope values before performing linear regression
        # in this case change [0, 1] -> [0.1, 0.9]
        v_min, v_max = np.quantile(alpha[no_nan], [0, 1])

        alpha_reg_lin = bin_alpha[
            (bin_alpha <= v_max) & (bin_alpha >= v_min)
        ]  # slope classes used for linear regression

        std_alpha_reg_lin = []
        alpha_reg_lin_for_fit = []
        for n in range(alpha_reg_lin.size - 1):
            mask = (
                (alpha > alpha_reg_lin[n]) & (alpha <= alpha_reg_lin[n + 1])
            ) & no_nan
            if diff[mask].size > 1:
                std_alpha_reg_lin.append(
                    np.std(diff[mask])
                )  # standard deviation of error for slope class
                alpha_reg_lin_for_fit.append(alpha_reg_lin[n])

        if len(std_alpha_reg_lin) <= 1:
            logging.error("Not enough pints to fit!")
            raise ValueError

        a, b = np.polyfit(np.tan(alpha_reg_lin_for_fit), std_alpha_reg_lin, 1)

        # calculation of normalization factor
        f_norm = np.ones(diff.shape) * np.nan
        for n in range(len(bin_alpha) - 1):
            mask = (alpha >= bin_alpha[n]) & (alpha <= bin_alpha[n + 1])
            y_alpha, x_alpha = np.where(mask)
            f_norm[y_alpha, x_alpha] = (
                1 + b / a * tan_alpha[y_alpha, x_alpha]
            ) ** (-1)

        # application of normalization factor to DEM elevation errors
        # bias subtraction before applying the factor.
        mu = np.mean(remove_nan_and_flatten(diff))
        dh_norm = (np.copy(diff) - mu) * f_norm

        return dh_norm

    def process_dem(
        self,
        dem_1: xr.Dataset,
        dem_2: xr.Dataset,
    ) -> xr.Dataset:
        """
        Compute the difference between dem_1 and dem_2 normalized by the slope.
        Add classification layers to the difference.

        :param dem_1: dem_1 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_1: xr.Dataset
        :param dem_2: dem_2 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_2: xr.Dataset
        :return: difference normalized by the slope xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """
        diff = self.compute_dems_diff_slope_norm(dem_1, dem_2)
        diff = accumulates_class_layers(dem_1, dem_2, diff)
        return diff


@DemProcessing.register("angular-diff")
class AngularDiff(DemProcessingTemplate):
    """
    Angular difference between two DEMs
    """

    def __init__(self, parameters: Dict = None):
        """
        Initialization the DEM processing object
        :return: None
        """

        super().__init__()

        self.fig_title = "[REF vs SEC] angular difference"
        self.colorbar_title = "Angular difference"
        self.cmap = "twilight"

    def compute_dems_angular_diff(
        self,
        dem_1: xr.Dataset,
        dem_2: xr.Dataset,
    ) -> xr.Dataset:
        """
        Compute angular difference dem_1 - dem_2 and
        return it as an xr.Dataset with the dem_2
        georeferencing and attributes.

        :param dem_1: dem_1 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_1: xr.Dataset
         :param dem_2: dem_2 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_2: xr.Dataset
        :return: angular difference xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """
        normal_dem_1 = compute_surface_normal(
            dem_1["image"].data,
            dem_1.georef_transform.data[1],
            dem_1.georef_transform.data[5],
        )

        normal_dem_2 = compute_surface_normal(
            dem_2["image"].data,
            dem_2.georef_transform.data[1],
            dem_2.georef_transform.data[5],
        )

        diff_raster = self.compute_angular_similarity(
            normal_dem_1, normal_dem_2
        )

        diff_dem = create_dem(
            diff_raster,
            transform=dem_2.georef_transform.data,
            nodata=dem_1.attrs["nodata"],
            img_crs=dem_2.crs,
            bounds=dem_2.bounds,
        )
        return diff_dem

    def compute_angular_similarity(
        self, n_a: np.ndarray, n_b: np.ndarray
    ) -> np.ndarray:
        """
        Compute the angular difference theta (radians) between two vector maps.

        :param n_a: surface normal vector to first DEM
        :type n_a: np.ndarray
        :param n_b: surface normal vector to second DEM
        :type n_ab: np.ndarray
        :return: angular difference between the two vectors
        :rtype: np.ndarray
        """

        n_a_b = (
            n_a[0] * n_b[0] + n_a[1] * n_b[1] + n_a[2] * n_b[2]
        )  # Scalar product between the 2 vectors
        n_a_b[n_a_b > 1] = 1
        n_a_b[n_a_b < -1] = -1
        dh_norm = np.arccos(np.abs(n_a_b))

        return dh_norm

    def process_dem(
        self,
        dem_1: xr.Dataset,
        dem_2: xr.Dataset,
    ) -> xr.Dataset:
        """
        Compute the angular difference between dem_1 and dem_2.
        Add classification layers to the difference.

        :param dem_1: dem_1 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_1: xr.Dataset
        :param dem_2: dem_2 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_2: xr.Dataset
        :return: angular difference xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """
        diff = self.compute_dems_angular_diff(dem_1, dem_2)
        diff = accumulates_class_layers(dem_1, dem_2, diff)
        return diff


@DemProcessing.register("ref")
class Ref(DemProcessingTemplate):
    """
    REF DEM
    """

    def __init__(self, parameters: Dict = None):
        """
        Initialization the DEM processing object
        :return: None
        """

        super().__init__()

        self.fig_title = "REF dem"
        self.colorbar_title = "Elevation (m)"
        self.cmap = "terrain"

    def process_dem(
        self,
        dem_1: xr.Dataset,
        dem_2: xr.Dataset = None,
    ) -> xr.Dataset:
        """
        Return dem_1

        :param dem_1: dem_1 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_1: xr.Dataset
        :param dem_2: dem_2 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_2: xr.Dataset
        :return: xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """
        return dem_1


@DemProcessing.register("sec")
class Sec(DemProcessingTemplate):
    """
    SEC DEM
    """

    def __init__(self, parameters: Dict = None):
        """
        Initialization the DEM processing object
        :return: None
        """

        super().__init__()

        self.fig_title = "SEC dem"
        self.colorbar_title = "Elevation (m)"
        self.cmap = "terrain"

    def process_dem(
        self,
        dem_1: xr.Dataset,
        dem_2: xr.Dataset,
    ) -> xr.Dataset:
        """
        Return dem_1

        :param dem_1: dem_1 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_1: xr.Dataset
        :param dem_2: dem_2 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_2: xr.Dataset
        :return: xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """
        dem_2["classification_layer_masks"] = (
            dem_1["classification_layer_masks"]
            if hasattr(dem_1, "classification_layer_masks")
            else None
        )
        return dem_2


@DemProcessing.register("ref-curvature")
class RefCurvature(DemProcessingTemplate):
    """
    Curvature of the REF DEM
    """

    def __init__(self, parameters: Dict = None):
        """
        Initialization the DEM processing object
        :return: None
        """

        super().__init__()

        self.fig_title = "REF dem curvature"
        self.colorbar_title = "Curvature"
        self.cmap = "bwr"

    def compute_curvature_filtering(
        self,
        dem: xr.Dataset,
        filter_intensity: float = 0.9,
        replication: bool = True,
    ) -> xr.Dataset:
        """
        Return the curvature of the input dem.
        First, compute the FFT of the input dem: F(y) = FFT(DEM).
        Then, apply a filter y^filter_intensity
        with s=0.9: F(y) = F(y)* y^filter_intensity.
        Finally, apply the inverse FFT: IFFT(F(y)).
        We keep the real part (imaginary part = digital noise).

        :param dem: dem xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem: xr.Dataset
        :param filter_intensity: parameter of the DEM's FFT filter intensity.
                                 Should be close to 1.
                                 Default = 0.9.
        :type filter_intensity: float
        :param replication: if true, the image is replicated
                            by x4 in order to improve resolution.
                            Default = True.
        :type replication: bool
        :return: curvature xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """

        no_data_location = np.logical_or(
            dem["image"].data == dem.attrs["nodata"],
            np.isnan(dem["image"].data),
        )

        # no data pixel interpolation
        data_all = neighbour_interpol(dem["image"].data, no_data_location)

        high, wide = dem["image"].data.shape

        if replication:
            data_all = np.hstack([data_all, np.flip(data_all, axis=1)])
            data_all = np.vstack([data_all, np.flip(data_all, axis=0)])
            f_y, f_x = calc_spatial_freq_2d(2 * high, 2 * wide, edge=np.pi)

        else:
            f_y, f_x = calc_spatial_freq_2d(high, wide, edge=np.pi)

        # spatial frequency (module)
        spatial_freq = (f_x**2 + f_y**2) ** (filter_intensity / 2)
        spatial_freq = ifftshift(spatial_freq)

        image = fft2(data_all)
        image_filtered = image * spatial_freq

        image_filtered = ifft2(image_filtered)

        if replication:
            image_filtered = image_filtered[:high, :wide]

        image_filtered[no_data_location] = dem.attrs["nodata"]

        return create_dem(
            image_filtered.real,
            transform=dem.georef_transform.data,
            nodata=dem.attrs["nodata"],
            img_crs=dem.crs,
            bounds=dem.bounds,
            classification_layer_masks=dem["classification_layer_masks"]
            if hasattr(dem, "classification_layer_masks")
            else None,
        )

    def process_dem(
        self,
        dem_1: xr.Dataset,
        dem_2: xr.Dataset = None,
    ) -> xr.Dataset:
        """
        Return the curvature of dem_1

        :param dem_1: dem_1 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_1: xr.Dataset
        :param dem_2: dem_2 xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :type dem_2: xr.Dataset
        :return: curvature xr.DataSet containing :

                - image : 2D (row, col) xr.DataArray float32
                - georef_transform: 1D (trans_len) xr.DataArray
                - classification_layer_masks : 3D (row, col, indicator)
                  xr.DataArray
        :rtype: xr.Dataset
        """
        return self.compute_curvature_filtering(dem_1)
