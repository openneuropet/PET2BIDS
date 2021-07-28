import datetime
import re
import nibabel
import os
import json
import helper_functions
from sidecar import sidecar_template_full, sidecar_template_short
from dateutil import parser
import numpy


def parse_this_date(date_like_object):
    if type(date_like_object) is int:
        parsed_date = datetime.datetime.fromtimestamp(date_like_object)
    else:
        parsed_date = parser.parse(date_like_object)

    return parsed_date.strftime("%H:%M:%S")


class EcatDump:
    """
    This class reads an ecat file w/ nibabel.ecat.load and extracts header, subheader, and image matrices for
    viewing in stdout. Additionally, this class can be used to convert an ECAT7.X image into a nifti image.
    """
    def __init__(self, ecat_file, nifti_file=None, decompress=True):
        """
        Initialization of this class requires only a path to an ecat file
        :param ecat_file: path to a valid ecat file
        :param nifti_file: when using this class for conversion from ecat to nifti this path, if supplied, will be used
        to output the nevly generated nifti
        :param decompress: attempt to decompress the ecat file, should probably be set to false
        """
        self.ecat_header = {}           # ecat header information is stored here
        self.subheaders = []            # subheader information is placed here
        self.ecat_info = {}
        self.affine = {}                # affine matrix/information is stored here.
        self.frame_start_times = []     # frame_start_times, frame_durations, and decay_factors are all
        self.frame_durations = []       # extracted from ecat subheaders. They're pretty important and get
        self.decay_factors = []         # stored here
        self.sidecar_template = sidecar_template_full  # bids approved sidecar file with ALL bids fields
        self.sidecar_template_short = sidecar_template_short  # bids approved sidecar with only required bids fields
        if os.path.isfile(ecat_file):
            self.ecat_file = ecat_file
        else:
            raise FileNotFoundError(ecat_file)

        if '.gz' in self.ecat_file and decompress is True:
            uncompressed_ecat_file = re.sub('.gz', '', self.ecat_file)
            helper_functions.decompress(self.ecat_file, uncompressed_ecat_file)

        if '.gz' in self.ecat_file and decompress is False:
            raise Exception("Nifti must be decompressed for reading of file headers")

        try:
            self.ecat = nibabel.ecat.load(self.ecat_file)
        except nibabel.filebasedimages.ImageFileError as err:
            print("\nFailed to load ecat image.\n")
            raise err

        # extract ecat info
        self.extract_header_info()
        self.extract_subheaders()
        self.extract_affine()

        # aggregate ecat info into ecat_info dictionary
        self.ecat_info['header'] = self.ecat_header
        self.ecat_info['subheaders'] = self.subheaders
        self.ecat_info['affine'] = self.affine

        # swap file extensions and save output nifti with same name as original ecat
        if not nifti_file:
            self.nifti_file = os.path.splitext(self.ecat_file)[0] + ".nii"
        else:
            self.nifti_file = nifti_file

    def make_nifti(self, output_path=None):
        """
        Outputs a nifti from the read in ECAT file
        :param output_path: Optional path to output file to, if not supplied saves nifti in same directory as ECAT
        :return: the output path the nifti was written to, used later for placing metadata/sidecar files
        """
        # read ecat
        img = self.ecat
        # convert to nifti
        fdata_int16 = img.get_fdata(dtype=numpy.int16)
        fdata_int32 = img.get_fdata(dtype=numpy.int32)
        fdata_float64 = img.get_fdata()
        #fdata_prescaled_data = img.raw_data_from_file_obj()
        img_nii = nibabel.Nifti1Image(img.get_fdata(dtype=numpy.int16), img.affine)
        img_nii.header.set_xyzt_units('mm', 'unknown')

        # save nifti
        if output_path is None:
            output = self.nifti_file
        else:
            output = output_path
        nibabel.save(img_nii, output)

        return output

    def extract_affine(self):
        """
        Extract affine matrix from ecat
        """
        self.affine = self.ecat.affine.tolist()

    def extract_header_info(self):
        """
        Extracts header and coverts it to sane type -> dictionary
        :return: self.header_info
        """
        header_entries = [entry for entry in self.ecat.header]
        for name in header_entries:

            value = self.ecat.header[name].tolist()

            # convert to string if value is type bytes
            if type(value) is bytes:
                try:
                    value = value.decode("utf-8")
                except UnicodeDecodeError as err:
                    print(f"Error decoding header entry {name}: {value}\n {value} is type: {type(value)}")
                    print(f"Attempting to decode {value} skipping invalid bytes.")

                    if err.reason == 'invalid start byte':
                        value = value.decode("utf-8", "ignore")
                        print(f"Decoded {self.ecat.header[name].tolist()} to {value}.")

            self.ecat_header[name] = value

        return self.ecat_header

    def extract_subheaders(self):
        """
        Similar to extract headers, but iterates through subheaders as well
        :return:
        """
        # collect subheaders
        subheaders = self.ecat.dataobj._subheader.subheaders
        for subheader in subheaders:
            holder = {}
            subheader_data = subheader.tolist()
            subheader_dtypes = subheader.dtype.descr

            for i in range(len(subheader_data)):
                holder[subheader_dtypes[i][0]] = {
                    'value': self.transform_from_bytes(subheader_data[i]),
                    'dtype': self.transform_from_bytes(subheader_dtypes[i][1])}

            self.subheaders.append(holder)

    def show_affine(self):
        """
        Display affine to stdout
        :return: affine matrix row by row.
        """
        for row in self.affine:
            print(row)

    def show_header(self):
        """
        Display header to stdout in key: value format
        :return: None
        """
        for key, value in self.ecat_header.items():
            print(f"{key}: {value}")

    def show_subheaders(self):
        """
        Displays subheaders to stdout
        :return: None
        """
        for subheader in self.subheaders:
            print(subheader)

    def populate_sidecar(self):
        """
        creates a side car dictionary with any bids relevant information extracted from the ecat.
        """
        # if it's an ecat it's Siemens
        self.sidecar_template['Manufacturer'] = 'Siemens'
        # Siemens model best guess
        self.sidecar_template['ManufacturersModelName'] = self.ecat_header.get('serial_number', None)

        self.sidecar_template['TracerRadionuclide'] = self.ecat_header.get('isotope_name', None)

        self.sidecar_template['PharmaceuticalName'] = self.ecat_header.get('radiopharmaceutical', None)
        # collect frame time start
        for header in self.subheaders:
            self.frame_start_times.append(header['frame_start_time']['value'])
            self.frame_durations.append(header['frame_duration']['value'])
            self.decay_factors.append(header['decay_corr_fctr']['value'])

        self.sidecar_template['DecayFactor'] = self.decay_factors
        self.sidecar_template['FrameTimesStart'] = self.frame_start_times
        self.sidecar_template['FrameDuration'] = self.frame_durations

        # collect and convert start times for acquisition/time zero?
        scan_start_time = self.ecat_header.get('scan_start_time', None)
        if scan_start_time:
            scan_start_time = parse_this_date(scan_start_time)
            self.sidecar_template['AcquisitionTime'] = scan_start_time
            self.sidecar_template['ScanStart'] = scan_start_time

        # collect dose start time
        dose_start_time = self.ecat_header.get('dose_start_time', None)
        if dose_start_time:
            parsed_dose_time = parse_this_date(dose_start_time)
            self.sidecar_template['PharmaceuticalDoseTime'] = parsed_dose_time

        # if decay correction exists mark decay correction boolean as true
        if len(self.decay_factors) > 0:
            self.sidecar_template['ImageDecayCorrected'] = "true"

    def prune_sidecar(self):
        """
        Eliminate unpopulated fields in sidecar while leaving in mandatory fields even if they are unpopulated.
        """
        short_fields = list(self.sidecar_template_short.keys())
        full_fields = list(self.sidecar_template)
        exclude_list = []
        for field, value in self.sidecar_template.items():
            if value:
                exclude_list.append(field)

        exclude_list = exclude_list + short_fields

        destroy_list = set(full_fields) - set(exclude_list)

        destroyed = []
        for to_be_destroyed in destroy_list:
            destroyed.append(self.sidecar_template.pop(to_be_destroyed))

        return destroyed

    def show_sidecar(self, output_path=None):
        """
        Write sidecar file to a json or display to stdout if no filepath is supplied
        :param output_path: path to output a json file
        :return:
        """
        self.prune_sidecar()
        if output_path:
            with open(output_path, 'w') as outfile:
                json.dump(self.sidecar_template, outfile, indent=4)
        else:
            print(json.dumps(self.sidecar_template, indent=4))

    def json_out(self):
        """
        Dumps entire ecat header and header info into stdout formatted as json.
        :return: None
        """
        temp_json = json.dumps(self.ecat_info, indent=4)
        print(temp_json)

    @staticmethod
    def transform_from_bytes(bytes_like):
        """
        Attempts to decode from bytes, not particularly well
        :param bytes_like: a bytes like object e.g. b'x\00\01\
        :return: a decoded object
        """
        if type(bytes_like) is bytes:
            return bytes_like.decode()
        else:
            return bytes_like
