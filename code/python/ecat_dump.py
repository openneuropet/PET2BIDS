import datetime
import re
import nibabel
import os
import json
from helper_functions import compress, decompress
from sidecar import sidecar_template_full, sidecar_template_short
from dateutil import parser


def parse_this_date(date_like_object):
    if type(date_like_object) is int:
        parsed_date = datetime.datetime.fromtimestamp(date_like_object)
    else:
        parsed_date = parser.parse(date_like_object)

    return parsed_date.strftime("%H:%M:%S")


class EcatDump:

    def __init__(self, ecat_file, nifti_file=None, decompress=True):
        self.ecat_header = {}
        self.subheaders = []
        self.ecat_info = {}
        self.affine = {}
        self.frame_start_times = []
        self.frame_durations = []
        self.decay_factors = []
        self.sidecar_template = sidecar_template_full
        self.sidecar_template_short = sidecar_template_short
        if os.path.isfile(ecat_file):
            self.ecat_file = ecat_file
        else:
            raise FileNotFoundError(ecat_file)

        if '.gz' in self.ecat_file and decompress is True:
            uncompressed_ecat_file = re.sub('.gz', '', self.ecat_file)
            decompress(self.ecat_file, uncompressed_ecat_file)

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

        if not nifti_file:
            self.nifti_file = os.path.splitext(self.ecat_file)[0] + ".nii"
        else:
            self.nifti_file = nifti_file

    def make_nifti(self, output_path=None):
        # read ecat
        img = self.ecat
        # convert to nifti
        img_nii = nibabel.Nifti1Image(img.get_fdata(), img.affine)
        img_nii.header.set_xyzt_units('mm', 'unknown')

        # save nifti
        if output_path is None:
            output = self.nifti_file
        else:
            output = output_path
        nibabel.save(img_nii, output)

        return output

    def display_ecat_and_nifti(self):
        print(f"ecat is {self.ecat_file}\nnifti is {self.nifti_file}")

    def extract_affine(self):
        self.affine = self.ecat.affine.tolist()

    def extract_header_info(self):
        """
        Extracts header and coverts it to sane type -> dictionary
        :return: self.header_info
        """
        header_entries = [entry for entry in self.ecat.header]
        for name in header_entries:

            value = self.ecat.header[name].tolist()
            value_not_to_list = self.ecat.header[name]

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
        for row in self.affine:
            print(row)

    def show_header(self):
        for key, value in self.ecat_header.items():
            print(f"{key}: {value}")

    def show_subheaders(self):
        for subheader in self.subheaders:
            print(subheader)

    def populate_sidecar(self):
        """
        creates a side car json with any bids relevant information within the ecat.
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

    def show_sidecar(self, output_path):
        self.prune_sidecar()
        if output_path:
            with open(output_path, 'w') as outfile:
                json.dump(self.sidecar_template, outfile, indent=4)
        else:
            print(json.dumps(self.sidecar_template, indent=4))

    def json_out(self):
        temp_json = json.dumps(self.ecat_info, indent=4)
        print(temp_json)

    @staticmethod
    def transform_from_bytes(bytes_like):
        if type(bytes_like) is bytes:
            return bytes_like.decode()
        else:
            return bytes_like
