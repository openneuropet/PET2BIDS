import argparse
import ast
import os
import pathlib
import sys
import textwrap
from os.path import join
from pypet2bids.ecat import Ecat
from pypet2bids.helper_functions import load_vars_from_config, ParseKwargs

"""
simple command line tool to extract header and pixel information from ecat files and convert ecat to nifti.

:format:
:param:
:return:

Anthony Galassi
-----------------------------
Copyright Open NeuroPET team
"""


epilog = textwrap.dedent('''
    
    example usage:
    
    ecatpet2bids ecatfile.v --dump # dumps ecat header information
    ecatpet2bids ecatfile.v --json # dumps header and subheader information to stdout
    ecatpet2bids ecatfile.v --nifti sub-01_ses-example_pet.nii --convert --kwargs TimeZero="12:34:56" # convert to nii
    ecatpet2bids ecatfile.v --scannerparams ge_parameters.txt --nifti sub-01_pet.nii --convert # load scanner specific \
params
    
    For additional (highly verbose) example usage call this program with the --show-examples flag.
''')


def cli():
    """
    Builds an argparse.ArgumentParser() object to access the methods available in the Ecat class in pypet2bids.ecat.ECAT

    :return: argparse.ArgumentParser.args for later use in executing conversions or ECAT methods
    """
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,epilog=epilog)
    parser.add_argument("ecat", nargs='?', metavar="ecat_file", help="Ecat image to collect info from.")
    parser.add_argument("--affine", "-a", help="Show affine matrix", action="store_true", default=False)
    parser.add_argument("--convert", "-c", required=False, action='store_true',
                        help="If supplied will attempt conversion.")
    parser.add_argument("--dump", "-d", help="Dump information in Header", action="store_true", default=False)
    parser.add_argument("--json", "-j", action="store_true", default=False, help="""
        Output header and subheader info as JSON to stdout, overrides all other options""")
    parser.add_argument("--nifti", "-n", metavar="file_name", help="Name of nifti output file", required=False,
                        default=None)
    parser.add_argument("--subheader", '-s', help="Display subheaders", action="store_true", default=False)
    parser.add_argument("--sidecar", action="store_true", help="Output a bids formatted sidecar for pairing with"
                                                               "a nifti.")
    parser.add_argument('--kwargs', '-k', nargs='*', action=ParseKwargs, default={},
                        help="Include additional values int the nifti sidecar json or override values extracted from "
                             "the supplied nifti. e.g. including `--kwargs TimeZero='12:12:12'` would override the "
                             "calculated TimeZero. Any number of additional arguments can be supplied after --kwargs "
                             "e.g. `--kwargs BidsVariable1=1 BidsVariable2=2` etc etc.")
    parser.add_argument('--scannerparams', nargs='*',
                        help="Loads saved scanner params from a configuration file following "
                             "--scanner-params/-s if this option is used without an argument "
                             "this cli will look for any scanner parameters file in the "
                             "directory with the name *parameters.txt from which this cli is "
                             "called.")
    parser.add_argument("--directory_table", '-t', help="Collect table/array of ECAT frame byte location map",
                        action="store_true", default=False)
    parser.add_argument('--show-examples', '-E', '--HELP', '-H', help='Shows example usage of this cli.',
                        action='store_true')

    args = parser.parse_args()
    return args


example1 = textwrap.dedent('''
    
Usage examples are below, the first being the most brutish way of injecting BIDS required fields
into the output from ecatpet2bids. Additional arguments/fields are passed via the kwargs flag
in key value pairs.

example 1 (Passing PET metadat via the --kwargs argument):
    
    # Note `#` denotes a comment
    
    # ecatfile -> SiemensHRRT-NRU/XCal-Hrrt-2022.04.21.15.43.05_EM_3D.v  
    # nifti -> sub-SiemensHRRTNRU/pet/sub-SiemensHRRTNRU_pet.nii
    # kwargs -> a bunch of key pair arguments spaced 1 space apart with the values surrounded by double quotes

    ecatpet2bids SiemensHRRT-NRU/XCal-Hrrt-2022.04.21.15.43.05_EM_3D.v 
    --nifti sub-SiemensHRRTNRU/pet/sub-SiemensHRRTNRU_pet.nii --convert 
    --kwargs
    TimeZero="10:10:10"
    Manufacturer=Siemens
    ManufacturersModelName=HRRT
    InstitutionName="Rigshospitalet, NRU, DK"
    BodyPart=Phantom Units="Bq/mL"
    Manufacturer=Siemens
    ManufacturersModelName=HRRT
    InstitutionName="Rigshospitalet, NRU, DK"
    BodyPart="Phantom"
    Units="Bq/mL"
    TracerName=FDG
    TracerRadionuclide=F18
    InjectedRadioactivity=81.24
    SpecificRadioactivity="1.3019e+04"
    ModeOfAdministration="infusion"
    InjectedMass=1
    InjectedMassUnits=grams
    AcquisitionMode="list mode"
    ImageDecayCorrected="True"
    ImageDecayCorrectionTime=0
    ReconFilterType="None"
    ReconFilterSize=0
    AttenuationCorrection="10-min transmission scan"
    SpecificRadioactivityUnits="Bq"
    ScanStart=0
    InjectionStart=0
    InjectedRadioactivityUnits="Bq"
    ReconFilterType="['n/a']"
''')


def main():
    """
    Executes cli() and then uses Ecat class to convert or extract information from an Ecat file

    :return: N/A
    """
    cli_args = cli()

    if cli_args.show_examples:
        print(example1)
        sys.exit(0)

    collect_pixel_data = False
    if cli_args.convert:
        collect_pixel_data = True
    if cli_args.scannerparams is not None:
        # if no args are supplied to --scannerparams/-s
        if cli_args.scannerparams == []:
            files_in_command_line_dir_call = os.listdir()
            scanner_txt = None
            for each in files_in_command_line_dir_call:
                if "parameters.txt" in each:
                    scanner_txt = each
                    break
            if scanner_txt is None:
                called_dir = os.getcwd()
                error_string = f'No scanner file found in {called_dir}. Either create a parameters.txt file, omit ' \
                               f'the --scannerparams argument, or specify a full path to a scanner.txt file after the '\
                               f'--scannerparams argument.'
                raise Exception(error_string)
        else:
            scanner_txt = cli_args.scannerparams[0]
        scanner_params = load_vars_from_config(scanner_txt)

        # if any additional non null values have been included in a scanner.txt include those in the sidecar,
        # variable supplied via the --kwargs argument to the cli will override any variables in scanner.txt
        if scanner_params:
            scanner_params.update(cli_args.kwargs)
            cli_args.kwargs.update(scanner_params)

    ecat = Ecat(ecat_file=cli_args.ecat,
                nifti_file=cli_args.nifti,
                collect_pixel_data=collect_pixel_data)
    if cli_args.json:
        ecat.json_out()
        sys.exit(0)

    if cli_args.dump:
        ecat.show_header()
        sys.exit(0)
    if cli_args.directory_table:
        ecat.show_directory_table()
        sys.exit(0)
    if cli_args.affine:
        ecat.show_affine()
    if cli_args.subheader:
        ecat.show_subheaders()
    if cli_args.sidecar:
        ecat.populate_sidecar(**cli_args.kwargs)
        ecat.show_sidecar()
    if cli_args.convert:
        output_path = pathlib.Path(ecat.make_nifti())
        ecat.populate_sidecar(**cli_args.kwargs)
        ecat.prune_sidecar()
        sidecar_path = join(str(output_path.parent), output_path.stem + '.json')
        ecat.show_sidecar(output_path=sidecar_path)


if __name__ == "__main__":
    main()
