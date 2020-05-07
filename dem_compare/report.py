#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

# Copyright (C) 2017-2018 Centre National d'Etudes Spatiales (CNES)

"""
Create sphinx report and compile it for html and pdf format

"""
import collections
import os
import glob
import csv
import sys
import fnmatch

from .sphinx_project_generator import SphinxProjectManager


def recursive_search(directory, pattern):
    """
    Recursively look up pattern filename into dir tree

    :param directory:
    :param pattern:
    :return:
    """""

    if sys.version[0:3] < '3.5':
        matches = []
        for root, dirnames, filenames in os.walk(directory):
            for filename in fnmatch.filter(filenames, pattern):
                matches.append(os.path.join(root, filename))
    else:
        matches = glob.glob('{}/**/{}'.format(directory, pattern), recursive=True)

    return matches


def generate_report(workingDir, dsmName, refName, partitionsList=None, docDir='.', projectDir='.'):
    """
    Create pdf report from png graph and csv stats summary

    :param workingDir: directory in which to find *mode*.png and *mode*.csv files for each mode in modename
    :param dsmName: name or path to the dsm to be compared against the ref
    :param refName: name or path to the reference dsm
    :param partitionsList: list of partition, contains modes by partition
    :param docDir: directory in which to find the output documentation
    :param projectDir:
    :return:
    """

    if partitionsList is None:
        partitionsList = ['standard']

    # Initialize the sphinx project
    SPM = SphinxProjectManager(projectDir, docDir, 'dem_compare_report', 'DEM Compare Report')

    # TODO modes_information[mode] ecras�, il faut un par partition => modes_information[partition_name][mode]

    # Initialize mode informations
    modes_information = collections.OrderedDict()

    for partition_name, stats_results_d in partitionsList.items():
        # Initialize mode informations for partition
        modes_information[partition_name] = collections.OrderedDict()
        modes_information[partition_name]['standard'] = {
            'pitch': 'This mode results simply relies only on valid values. This means nan '
                     'values (whether they are from the error image or the reference support '
                     'image when do_classification is on), but also ouliers and masked ones '
                     'has been discarded.'}
        modes_information[partition_name]['coherent-classification'] = {'pitch': 'This is the standard mode where only the pixels for '
                                                                 'which input DSMs classifications are coherent.'}
        modes_information[partition_name]['incoherent-classification'] = {'pitch': 'This mode is the \'coherent-classification\' '
                                                                   'complementary.'}
        modes = ['standard', 'coherent-classification', 'incoherent-classification']

        for mode in modes:
            #for mode in modes_information:
            # find both graph and csv stats associated with the mode
            # - histograms
            result = recursive_search(os.path.join(workingDir, '*', partition_name), '*Real*_{}*.png'.format(mode))
            if len(result):
                modes_information[partition_name][mode]['histo'] = result[0]
            else:
                modes_information[partition_name][mode]['histo'] = None

            # - graph
            result = recursive_search(os.path.join(workingDir, '*', partition_name), '*Fitted*_{}*.png'.format(mode))
            if len(result):
                modes_information[partition_name][mode]['fitted_histo'] = result[0]
            else:
                modes_information[partition_name][mode]['fitted_histo'] = None
            # - csv
            result = recursive_search(os.path.join(workingDir, '*', partition_name), '*_{}*.csv'.format(mode))
            if len(result):
                if os.path.exists(result[0]):
                    csv_data = []
                    with open(result[0], 'r') as csv_file:
                        csv_lines_reader = csv.reader(csv_file, quoting=csv.QUOTE_NONNUMERIC)
                        for row in csv_lines_reader:
                            csv_data.append(','.join([item if type(item) is str else format(item, '.2f') for item in row]))
                    modes_information[partition_name][mode]['csv'] = '\n'.join(['    '+csv_single_data for csv_single_data in csv_data])
                else:
                    modes_information[partition_name][mode]['csv'] = None
            else:
                modes_information[partition_name][mode]['csv'] = None

    # Find DSMs differences
    dem_diff_without_coreg = recursive_search(workingDir, 'initial_dem_diff.png')[0]
    result = recursive_search(workingDir, 'final_dem_diff.png')
    if len(result):
        dem_diff_with_coreg = result[0]
    else:
        dem_diff_with_coreg = None

    # Create source
    # -> header part
    src = '\n'.join([
        '.. _DSM_COMPARE_REPORT:',
        '',
        '*********************',
        ' DSM COMPARE REPORT',
        '*********************'
        '',
        '**This report shows comparison results between the following DSMs:**',
        '',
        '* **The DSM to evaluate**: {}'.format(dsmName),
        '* **The Reference DSM**  : {}'.format(refName),
        ''
    ])
    # -> DSM differences
    src = '\n'.join([
        src,
        '**Below is shown elevation differences between both DSMs:**',
        '',
        # 'DSM diff without coregistration',
        # '-------------------------------',
        '.. image:: /{}'.format(dem_diff_without_coreg),
        ''
    ])
    if dem_diff_with_coreg:
        src = '\n'.join([
            src,
            # 'DSM diff with coregistration',
            # '----------------------------',
            '.. image:: /{}'.format(dem_diff_with_coreg),
            ''
        ])
    # -> table of contents
    src = '\n'.join([
        src,
        '**The comparison outcomes are provided for the evaluation mode listed hereafter:**',
        ''
    ])
    for mode in modes:
        src = '\n'.join([
            src,
            '* The :ref:`{} <{}>` mode'.format(mode, mode)
        ])

    # -> the results
    for partition_name, stats_results_d in partitionsList.items():
        src = '\n'.join([
            src,
            '*{} classification layer*'.format(partition_name),
            '{}'.format('#'*len(partition_name))
        ])

        for mode in modes:
            if mode in stats_results_d:
                the_mode_pitch = modes_information[partition_name][mode]['pitch']
                the_mode_histo = modes_information[partition_name][mode]['histo']
                the_mode_fitted_histo = modes_information[partition_name][mode]['fitted_histo']
                the_mode_csv = modes_information[partition_name][mode]['csv']
            else:
                continue
            src = '\n'.join([
                src,
                '',
                '.. _{}:'.format(mode),
                '',
                '*Results for the {} evaluation mode*'.format(mode),
                '=================================={}'.format('='*len(mode)),
                '',
                '{}'.format(the_mode_pitch),
                ''
            ])
            if the_mode_histo:
                src = '\n'.join([
                    src,
                    # 'Graph showing mean and standard deviation',
                    # '-----------------------------------------',
                    '.. image:: /{}'.format(the_mode_histo),
                    ''
                ])
            if the_mode_fitted_histo:
                src = '\n'.join([
                    src,
                    # 'Fitted graph showing mean and standard deviation',
                    # '-----------------------------------------',
                    '.. image:: /{}'.format(the_mode_fitted_histo),
                    ''
                ])
            if the_mode_csv:
                src = '\n'.join([
                    src,
                    # 'Table showing comparison metrics',
                    # '--------------------------------',
                    '.. csv-table::',
                    '',
                    '{}'.format(the_mode_csv),
                    ''
                ])
    # Add source to the project
    SPM.write_body(src)

    # Build & Install the project
    try:
        SPM.build_project('html')
    except:
        print(('Error when building report as {} output (ignored)'.format('html')))
        raise
    try:
        SPM.build_project('latexpdf')
    except:
        print(('Error when building report as {} output (ignored)'.format('pdf')))
        pass
    SPM.install_project()
