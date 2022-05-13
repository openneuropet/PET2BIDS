usage
=====

Python
------

The python library is available for use on Posix systems (OSX and Linux) only, and requires
that dcm2niix be installed and findable on the system path. For more information on how to
install dcm2niix see Dcm2niix_.

.. _Dcm2niix: https://github.com/rordenlab/dcm2niix#install

**Installation**

The python version of PET2BIDS (from herein refrenced by it's library name *pypet2bids*) can be installed via pip for Python versions >3.7.1,<3.10

.. code-block::

    pip install pypet2bids

Additionally, pypet2bids can be run from source by cloning the source code at our Github_.

.. _Github: https://github.com/openneuropet/PET2BIDS

.. code-block::

    git clone git@github.com:openneuropet/PET2BIDS.git

and then installing it's dependencies via pip or poetry

.. code-block::

    cd PET2BIDS/pypet2bids
    pip install -r requirements.txt

Or

.. code-block::

    cd PET2BIDS/pypet2bids
    poetry install



