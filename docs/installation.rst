.. _installation:

Installation
============

Matlab
------

Clone the repo at https://github.com/openneuropet/PET2BIDS.git and the contents of the `matlab` folder to your matlab
path with `addpath`:

.. code-block::

    >> addpath("PET2BIDS/matlab/")


.. raw:: html

    <script id="asciicast-RPxiHW6afISPmWYFBOGKWNem1" src="https://asciinema.org/a/RPxiHW6afISPmWYFBOGKWNem1.js"
    async data-autoplay="true" data-speed="1.5" data-loop="true"></script>


Python
------

The python version of PET2BIDS (from herein referenced by it's library name *pypet2bids*) can be installed
via pip for Python versions >3.7.1,=<3.11

.. code-block::

    pip install pypet2bids


.. raw:: html

    <script id="asciicast-TZJg5BglDMFM2fEEX9dSpnJEy" src="https://asciinema.org/a/TZJg5BglDMFM2fEEX9dSpnJEy.js"
    async data-autoplay="true" data-speed="1" data-loop="true"></script>

If you wish to contribute, are unable to install from PyPi, or simply wish to run pypet2bids from source, continue
reading the `Additional Install Notes`_ section below.

Additional Install Notes
------------------------

**Matlab**

------------------------------------------------------------------------------------------------------------------------

**Dependencies**

*To convert DICOM files*,
`dcm2niix <https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage>`__ (Chris Rorden) must be installed.

We recommend using dcm2niix version v1.0.20220720 or above as it has been updated to better tease out PET information
from source dicoms. Using older dcm2niix versions (especially year 2020 or later) can cause issues with this software.
The latest releases can always be found at
`dcm2niix/releases <https://github.com/rordenlab/dcm2niix/releases/>`__

Windows users must, in addition, indicate its full path in
`dcm2niix4pet.m <https://github.com/openneuropet/PET2BIDS/blob/main/matlab/dcm2niix4pet.m#L42>`__.

**Redistributed functions**

To convert ECAT files, `ecat2nii.m <https://github.com/openneuropet/PET2BIDS/blob/main/matlab/ecat2nii.m>`_ uses
`readECAT7 <https://github.com/openneuropet/PET2BIDS/blob/main/matlab/readECAT7.m>`_ (Raymond Muzic, 2002) and
`nii_tool <https://github.com/xiangruili/dicm2nii>`_ (Xiangrui Li, 2016), who are included and redistributed in the
repository. *To write the JSON sidecar files*, one uses jsonwrite.m (Guillaume Flandin, 2020) taken from
`json.io <https://github.com/gllmflndn/JSONio>`_.

**Configuration**

The entire repository or only the matlab subfolder (your choice) should be in your matlab path.

Defaults parameters should be set in (scannername).txt files to generate metadata easily (i.e. avoiding to pass
all arguments in although this is also possible). You can find templates of such parameter file under /template_txt
(SiemensHRRTparameters.txt, SiemensBiographparameters.txt, GEAdvanceparameters.txt,  PhilipsVereosparameters.txt).

------------------------------------------------------------------------------------------------------------------------

**Python**

If you are unable to install this library from PyPi you can clone this repository to build and install the package
as distributed on PyPi yourself with poetry.

We use `poetry <https://python-poetry.org/>`_ to build this package, no other build methods are supported,
further we encourage the use of `GNU make <https://www.gnu.org/software/make/>`_ and a bash-like shell to simplify the
build process.

After installing poetry, you can build and install this package to your local version of Python with the following
commands (keep in mind the commands below are executed in a bash-like shell):

.. code-block::

    cd PET2BIDS
    cp -R metadata/ pypet2bids/pypet2bids/metadata
    cp pypet2bids/pyproject.toml pypet2bids/pypet2bids/pyproject.toml
    cd pypet2bids && poetry lock && poetry build
    pip install dist/pypet2bids-X.X.X-py3-none-any.whl

.. note::

    Make and the additional scripts contained in the `scripts/` directory are for the convenience of
    non-windows users.

If you have GNU make installed and are using a bash or something bash-like in you your terminal of choice, run the
following:

.. code-block::

    cd PET2BIDS
    make installpoetry buildpackage installpackage

.. _Github: https://github.com/openneuropet/PET2BIDS


pypet2bids can be run from source by cloning the source code at our Github_.

.. code-block::

    git clone https://github.com/openneuropet/PET2BIDS

and then installing it's dependencies via pip:

.. code-block::

    cd PET2BIDS/pypet2bids
    pip install .

or installing them with `Poetry <https://python-poetry.org/>`_:

.. code-block::

    cd PET2BIDS/pypet2bids
    poetry install

After either poetry or pip installation of dependencies modules can be executed as follows:

.. code-block::

    cd PET2BIDS/pypet2bids
    python dcm2niix4pet.py --help

**Windows Only**

It's important that python be on your windows path; when installing Python be sure to select **Add Python 3.XXX**
to PATH:

.. image:: media/check_python_path_windows_install.png

Otherwise, if you're a savvy user w/ admin you config your PATH variable/cmd however you see fit. The above is simply
this easiest and most universal way of getting python onto windows path.

Windows requires the user to manually point to the installed path of
`dcm2niix <https://github.com/rordenlab/dcm2niix>`_.
Pypet2bids checks for this path in the *.petbidsconfig* file located at the users home director. This file needs to
exist and contain a valid path to dcm2niix.exe stored under the name *DCM2NIIX_PATH*. This can be set up by either
manually creating the file:

.. code-block::

    # get the home directory
    echo $Home

    C:\Users\pet2bidsuser\

    # then save a configuration file at the location $Home\.pet2bidsconfig containing the following line
    DCM2NIIX_PATH="<path to dcm2niix exe>"

    # e.g. when printing out the contents of the file at .pet2bidsconfig on should see something
    # resembling the following
    cat C:\Users\pet2bidsuser\.pet2bidsconfig
    DCM2NIIX_PATH="C:\Users\pet2biduser\dcm2niix.exe"

Or using the *dcm2niix4pet* tool itself to set up the configuration:

.. code-block::

    dcm2niix4pet --set-dcm2niix-path \path\to\dcm2niix.exe
