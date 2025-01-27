.. _report:

Generated output report
=======================

.. warning::
  Demcompare report is work in progress ! 


If the **demcompare** execution includes the **statistics** step 
and the output directory has been specified, a report can be generated using the "report" step.

For now, only a HTML and PDF report can be generated from a specific sphinx source report. 

Report configuration: 

.. csv-table::
    :header: "Report config", "Description", "Type" 
    :widths: auto
    :align: left

      ``'default'``,"default choice, equal to sphinx for now","string"
      ``'sphinx'``,"demcompare sphinx report generator (only one for now)","string"

Example of json syntax for configuration file: 

.. code-block:: json

      "report": "default"


Sphinx report
*************

The output `<test_output>/report/published_report/` directory contains 
a full generated sphinx documentation with the results in html or latex format.

The source of the sphinx report is in  `<test_output>/report/src``

Once **demcompare** has been executed with report configuration,
the report can be observed using a browser:

.. code-block:: bash

    firefox test_output/report/published_report/html/index.html &


