About
=====

**What does this tool do?**

PET2BIDS accepts PET imaging and radiological/blood data as inputs (e.g. dicom, ecat, spreadsheets)
and delivers BIDS fomatted outputs (e.g. nifti, json, and tsv files). See the below diagram:

.. image:: media/pypet2bids_floow.drawio.png

**It looks like you're just wrapping dcm2niix, why not just use it?**

That's a correct assessment, however dcm2niix only handles the conversion from dicom to nii. It has
no idea what a spreadsheet is and knows roughly what BIDS is, but is not fully compliant with the standard.

**Is there a CLI or do I need to learn Python to use this tool?**

Yes there is a CLI and no you don't need to learn Python at all, but you're more than able to use this tool as a Python
library. For more information on usage individual methods or modules refer to :ref:`pypet2bids-package`.

Additionally, many (if not more) of the features present in the Python module are available in Matlab too, for a
comprehensive list of available commands/methods see :ref:`matlab`.

**How do I use this tool?**

Please refer to the :ref:`usage` page for details on how to go about using this software or the :ref:`quickstart` page
for a small walk-through. Additionally, if you want to truly see how this software works on real data, take a look at
our CI on `Github <https://github.com/openneuropet/PET2BIDS/actions/workflows/setup_and_cli_test_posix.yaml>`_
as a further demonstration of running this software.

**This tool doesn't work/this is really hard....**

Reshaping PET data into BIDS can often be difficult, but it's the goal of this software and it's developers to make the
process easier for you the user. If you are struggling with using the software (or the software is struggling to work
with your data) reach out us via our `Issues Page <https://github.com/openneuropet/PET2BIDS/issues>`_ or through our
`Website/Email <https://openneuropet.github.io/#[object%20Object]>`_.
