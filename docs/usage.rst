.. _usage:

Usage
=====

Matlab
------

**Read and write raw scanner files as nifti + json**

BIDS requires nifti files and json. While json can be writen be hand, this is more convenient to populate them as one reads data. One issue is that some information is not encoded in ecat/dicom headers and thus needs to be created overwise.

**Dependencies**

*To convert DICOM files*, `dcm2niix <https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage>`_ (Chris Rorden) must be installed. Windows users must, in addition, indicate its full path in `dcm2niix4pet.m <https://github.com/openneuropet/PET2BIDS/blob/main/matlab/dcm2niix4pet.m#L42>`_.

**Redistributed functions**

 To convert ECAT files, `ecat2nii.m <https://github.com/openneuropet/PET2BIDS/blob/main/matlab/ecat2nii.m>`_ uses `readECAT7 ><https://github.com/openneuropet/PET2BIDS/blob/main/matlab/readECAT7.m>`_ (Raymond Muzic, 2002) and `nii_tool <https://github.com/xiangruili/dicm2nii>`_ (Xiangrui Li, 2016), who are included and redistributed in the repository. *To write the JSON sidecar files*, one uses jsonwrite.m (Guillaume Flandin, 2020) taken from `json.io <https://github.com/gllmflndn/JSONio>`_. 

**Configuration**

The entire repository or only the matlab subfolder (your choice) should be in your matlab path.  

Defaults parameters should be set in (scannername).txt files to generate metadata easily (i.e. avoiding to pass all arguments in although this is also possible). You can find templates of such parameter file under /template_txt (SiemensHRRTparameters.txt, SiemensBiographparameters.txt, GEAdvanceparameters.txt,  PhilipsVereosparameters.txt).

**Using matlab code**

To simplify the curation of json files, one uses the `get_pet_metadata.m <https://github.com/openneuropet/PET2BIDS/blob/main/matlab/get_pet_metadata.m>`_ function. This function takes as arguments the scanner info (thus loading the relevant *parameters.txt file) and also need some manual input related to the injected tracer.  
  
*Feel free to reach out if you have an issue with your scanner files, we can help*.

The simplest way to convert DICOM files is to call `dcm2niix4pet.m <https://github.com/openneuropet/PET2BIDS/blob/main/matlab/dcm2niix4pet.m>`_ which wraps around dcm2niix. Assuming dcm2niix is present in your environment, Matlab will call it to convert your data to nifti and json - and the wrapper function will additionally edit the json file. Arguments in are the dcm folder(s) in, the metadata as a structure (using the get_pet_metadata.m function for instance) and possibly options as per dcm2nixx.  

*Note for windows user*: edit the dcm2niix4pet.m line 51 to indicate where is the .exe function located

``meta = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart', 'TracerName','CB36','TracerRadionuclide','C11', 'ModeOfAdministration', 'infusion','SpecificRadioactivity', 605.3220,'InjectedMass', 1.5934, 'MolarActivity', 107.66, 'InstitutionName','Rigshospitalet, NRU, DK', 'AcquisitionMode','list mode','ImageDecayCorrected','true', 'ImageDecayCorrectionTime' ,0,'ReconMethodName','OP-OSEM', 'ReconMethodParameterLabels',{'subsets','iterations'}, 'ReconMethodParameterUnits',{'none','none'},    'ReconMethodParameterValues',[21 3], 'ReconFilterType','XYZGAUSSIAN', 'ReconFilterSize',2, 'AttenuationCorrection','CT-based attenuation correction'); dcm2niix4pet(dcmfolder,meta,'o','mynewfolder');``  

The get_pet_metadata function can be called in a much simpler way if you have a `*parameters.txt` seating on disk next to this function. The call would then looks like:

``meta = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart','TracerName','CB36', 'TracerRadionuclide','C11', 'ModeOfAdministration','infusion','SpecificRadioactivity', 605.3220, 'InjectedMass', 1.5934,'MolarActivity', 107.66); dcm2niix4pet(dcmfolder,meta,'o','mynewfolder');``  

*Alternatively*, you could have data already converted to nifti and json, and you need to update the json file. This can be done 2 ways:

1. Use the `updatejsonpetfile.m <https://github.com/openneuropet/PET2BIDS/blob/main/matlab/updatejsonpetfile.m>`_ function. Arguments in are the json file to update and metadata to add as a structure (using a get_metadata.m function for instance) and possibly a dicom file to check additional fields. This is show below for data from the biograph.

``jsonfilename = fullfile(pwd,'DBS_Gris_13_FullCT_DBS_Az_2mm_PRR_AC_Images_20151109090448_48.json')``
your SiemensBiographparameters.txt file is stored next to get_pet_metadata.m

``metadata = get_pet_metadata('Scanner','SiemensBiograph','TimeZero','ScanStart','TracerName','AZ10416936','TracerRadionuclide','C11',           'ModeOfAdministration','bolus','InjectedRadioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66); dcminfo = dicominfo('DBSGRIS13.PT.PETMR_NRU.48.13.2015.11.11.14.03.16.226.61519201.dcm'); status = updatejsonpetfile(jsonfilename,metadata,dcminfo)``

2. Add the metadata 'manually' to the json file, shown below for GE Advance data. 

`` metadata1 = jsondecode(textread(myjsonfile.json)); % or use jsonread from the matlab BIDS library``
your GEAdvance.txt file is stored next to get_pet_metadata.m
``metadata2 = get_pet_metadata('Scanner', 'GEAdvance','TimeZero','XXX','TracerName','DASB','TracerRadionuclide','C11',                   'ModeOfAdministration','bolus', 'InjectedRadioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66); metadata  = [metadata2;metadata1]; jsonwrite('mynewjsonfile.json'],metadata)``

**Converting ecat files**

If you have ecat (.v) instead of dicom (.dcm), we have build a dedicated converter. Arguments in are the file to convert and some metadata as a structure (using the get_pet_metadata.m function for instance). This is shown below for HRRT data.

Your SiemensHRRT.txt file is stored next to get_pet_metadata.m
``metadata = get_pet_metadata('Scanner','SiemensHRRT','TimeZero','XXX','TracerName','DASB','TracerRadionuclide','C11', 'ModeOfAdministration','bolus', 'InjectedRadioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66); ecat2nii({full_file_name},{metadata})``
 
See the `documentation <https://github.com/openneuropet/PET2BIDS/blob/main/matlab/unit_tests/Readme.md>`_ for further details on ecat conversion


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

and then installing it's dependencies via pip:

.. code-block::

    cd PET2BIDS/pypet2bids
    pip install -r requirements.txt

Or with `Poetry <https://python-poetry.org/>`_:

.. code-block::

    cd PET2BIDS/pypet2bids
    poetry install

If successfully installed you should have access to 3 command line tools, check to see if they are available via your
terminal/commandline:

ecatpet2bids for converting ecat data into nii & json

.. code-block::

    # our ecat conversion library should be available via the following
    ecatpet2bids -h
    usage: ecatpet2bids [-h] [--affine] [--convert] [--dump] [--json] [--nifti file_name] [--subheader] [--sidecar] [--kwargs [KWARGS ...]] [--scannerparams [SCANNERPARAMS ...]] [--directory_table]
                    ecat_file

    positional arguments:
      ecat_file             Ecat image to collect info from.

    optional arguments:
      -h, --help            show this help message and exit
      --affine, -a          Show affine matrix
      --convert, -c         If supplied will attempt conversion.
      --dump, -d            Dump information in Header
      --json, -j            Output header and subheader info as JSON to stdout, overrides all other options
      --nifti file_name, -n file_name
                            Name of nifti output file
      --subheader, -s       Display subheaders
      --sidecar             Output a bids formatted sidecar for pairing witha nifti.
      --kwargs [KWARGS ...], -k [KWARGS ...]
                            Include additional values int the nifti sidecar json or override values extracted from the supplied nifti. e.g. including `--kwargs TimeZero='12:12:12'` would override the
                            calculated TimeZero. Any number of additional arguments can be supplied after --kwargs e.g. `--kwargs BidsVariable1=1 BidsVariable2=2` etc etc.
      --scannerparams [SCANNERPARAMS ...]
                            Loads saved scanner params from a configuration file following --scanner-params/-s if this option is used without an argument this cli will look for any scanner parameters file
                            in the directory with the name *parameters.txt from which this cli is called.
      --directory_table, -t
                            Collect table/array of ECAT frame byte location map


For converting dicom to BIDS use dcm2niix4pet via:

.. code-block::

    dcm2niix4pet -h
    usage: dcm2niix4pet [-h] [--metadata-path METADATA_PATH] [--translation-script-path TRANSLATION_SCRIPT_PATH] [--destination-path DESTINATION_PATH] [--kwargs [KWARGS ...]] [--silent SILENT]
                    [--write-template-script]
                    folder

    positional arguments:
      folder                Folder path containing imaging data

    optional arguments:
      -h, --help            show this help message and exit
      --metadata-path METADATA_PATH, -m METADATA_PATH
                            Path to metadata file for scan
      --translation-script-path TRANSLATION_SCRIPT_PATH, -t TRANSLATION_SCRIPT_PATH
                            Path to a script written to extract and transform metadata from a spreadsheet to BIDS compliant text files (tsv and json)
      --destination-path DESTINATION_PATH, -d DESTINATION_PATH
                            Destination path to send converted imaging and metadata files to. If omitted defaults to using the path supplied to folder path. If destination path doesn't exist an attempt to
                            create it will be made.
      --kwargs [KWARGS ...], -k [KWARGS ...]
                            Include additional values int the nifti sidecar json or override values extracted from the supplied nifti. e.g. including `--kwargs TimeZero='12:12:12'` would override the
                            calculated TimeZero. Any number of additional arguments can be supplied after --kwargs e.g. `--kwargs BidsVariable1=1 BidsVariable2=2` etc etc.
      --silent SILENT, -s SILENT
                            Display missing metadata warnings and errorsto stdout/stderr

**Using pypet2bids**

Pypet2bids is primarily designed to run as a command line utility, design choice was made for 2 purposes:

1) to provide a universal interface (API) so the library is operable with any scripting or programming language
2) keeping the usage as simple as possible, use of this library is as simple as install -> run command

Additionally, one has access to the underlying python methods and classes if one wishes to use this library from within
a Python environment.

Command line usage:

In the most simple use case one can convert a folder full of dicoms into a NIFTI

.. code-block::

    dcm2niix4pet /folder/with/PET/dicoms/ -d /folder/with/PET/nifti_jsons


However, more often than not the information required to create a valid PET BIDS nifti and json isn't present
w/ in the dicom headers of the PET Image files. Extra information can be extracted at the time of conversion by
including a spreadsheet file (tsv, xlsx, etc) and an extraction script

.. code-block::

    dcm2niix /folder/with/PET/dicoms/ --destination /folder/with/PET/nifti_jsons --metadatapath /file/with/PET_metadata.xlsx --translation-script translate.py

It this point you may be asking self what is a metadata translation script? It's a python script designed to collect
relevant PET metadata from a spreadsheet. There are two approaches to extracting additional PET metadata from a spreasheet.

    - Format a spreadsheet to be more BIDS like and read use that data in the conversion:

      .. image:: media/image_example_bids_spreadsheet.png

    - Create a translation script that will extract and transform data from an existing spreadsheet. This method has the
      benefit of better preserving the original data, but the cost is that it requires more fiddling directly in Python.
      An example can be see below

      .. code-block::

            def translate_metadata(metadata_dataframe, image_path=NotImplemented):

            nifti_json = {
                'Manufacturer': '',
                'ManufacturersModelName': '',
                'Units': 'Bq/mL',
                'TracerName': '[11C]PS13',
                'TracerRadionuclide': '11C',
                'InjectedRadioactivity': metadata_dataframe['Analyzed:'][32]*(1/1000)*(37*10**9), # mCi convert to Bq -> (mCi /1000) *  37000000000
                'InjectedRadioactivityUnits': 'Bq',
                'InjectedMass': metadata_dataframe['Met365a.xls - 011104'][35] * metadata_dataframe['Analyzed:'][38] , #provided in nmol/kg for subject
                'InjectedMassUnits': 'nmol',
                'SpecificRadioactivity': 9218*37*10**9, # c11 is maximum 9218 Ci/umol,
                'SpecificRadioactivityUnits': 'Bq/mol',
                'ModeOfAdministration': 'bolus',
                'TimeZero': 0,
                'ScanStart': 0,
                'InjectionStart': 0,
                'FrameTimesStart': [],
                'FrameDuration': [],
                'AcquisitionMode': '',
                'ImageDecayCorrected': '',
                'ImageDecayCorrectionTime': 0,
                'ReconMethodName': '',
                'ReconMethodParameterLabels': [],
                'ReconMethodParameterUnits': [],
                'ReconMethodParameterValues': [],
                'ReconFilterType': '',
                'ReconFilterSize': 0,
                'AttenuationCorrection': '',
                'InstitutionName': '',
                'InstitutionalDepartmentName': ''
            }

If you're thinking it's to much to ask you to generate this script from scratch, you're absolutely right. You can generate a
template script by running the following command:

.. code-block::

    pet2bids-spreadsheet-template /path/to/save/template/script.py
    ls /path/to/save/template/script.py
    script.py

Now assuming you've located your dicom images, set up your template script/and or your metadata spreadsheet you should
be able produce the output resembling the following:

.. code-block::

    machine:folder user$ ls ~/Desktop/testdcm2niix4pet/
    PET_Brain_Dyn_TOF_7801580_20180322104003_5.json         PET_Brain_Dyn_TOF_7801580_20180322104003_5_blood.json
    PET_Brain_Dyn_TOF_7801580_20180322104003_5.nii.gz       PET_Brain_Dyn_TOF_7801580_20180322104003_5_blood.tsv





Pypet2bids can be run via the command line after being installed, often additional radiological information will need to
be passed to pypet2bids in addition to PET imaging data. Passing this data can be done in a number of increasingly
complex ways. The simplest method to pass on information is directly at the command line when calling either
**dcm2niix4pet** or **ecatpet2bids**. Both of these tools accept additional arguments via key pair's separated by the
equals sign `=`. This functionality is designed to mirror that of the Matlab code.

Some extra values in the case of this Siemens Biograph would look like the following:

.. code-block::

    dcm2niix4pet OpenNeuroPET-Phantoms/source/SiemensBiographPETMR-NRU --kwargs
    TimeZero=ScanStart
    Manufacturer=Siemens
    ManufacturersModelName=Biograph InstitutionName="Rigshospitalet, NRU, DK"
    BodyPart=Phantom
    Units=Bq/mL
    TracerName=none
    TracerRadionuclide=F18
    InjectedRadioactivity=81.24
    SpecificRadioactivity=13019.23
    ModeOfAdministration=infusion
    FrameTimesStart=0
    AcquisitionMode="list mode"
    ImageDecayCorrected=true
    ImageDecayCorrectionTime=0
    AttenuationCorrection=MR-corrected
    FrameDuration=300
    FrameTimesStart=0


And similarly, extra key pair values can be passed to ecatpet2bids:

.. code-block::

    ecatpet2bids OpenNeuroPET-Phantoms/source/SiemensHRRT-NRU/XCal-Hrrt-2022.04.21.15.43.05_EM_3D.v
    --convert
    --kwargs
    TimeZero=ScanStart
    Manufacturer=Siemens
    ManufacturersModelName=HRRT
    InstitutionName="Rigshospitalet, NRU, DK"
    BodyPart=Phantom
    Units=Bq/mL
    TracerName=none
    TracerRadionuclide=F18
    InjectedRadioactivity=81.24
    SpecificRadioactivity=13019.23
    ModeOfAdministration=infusion
    AcquisitionMode="list mode"
    ImageDecayCorrected=true
    ImageDecayCorrectionTime=0
    AttenuationCorrection="10-min transmission scan"



