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

Yes there is and no not at all, but you're more than able to use this tool as a Python library. For more information on
usage refer to :ref:`pypet2bids-package`.


Additionally, many
(if not more) of the features present in the Python module are available in Matlab too, for a comprehensive list of
available commands/methods see :ref:`matlab`.
