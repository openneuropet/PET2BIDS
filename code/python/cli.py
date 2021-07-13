import argparse
import pathlib
import sys
from os.path import join

from ecat_dump import EcatDump
"""
simple command line tool to extract header info from ecat files.
"""


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("ecat", metavar="ecat_file", help="Ecat image to collect info from.")
    parser.add_argument("--affine", "-a", help="Show affine matrix", action="store_true", default=False)
    parser.add_argument("--convert", "-c", required=False, action='store_true', help="If supplied will attempt conversion.")
    parser.add_argument("--dump", "-d", help="Dump information in Header", action="store_true", default=False)
    parser.add_argument("--json", "-j", action="store_true", default=False, help="""
        Output header and subheader info as JSON to stdout, overrides all other options""")
    parser.add_argument("--nifti", "-n", metavar="file_name", help="Name of nifti output file", required=False)
    parser.add_argument("--subheader", '-s', help="Display subheaders", action="store_true", default=False)
    parser.add_argument("--sidecar", action="store_true")
    args = parser.parse_args()
    return args


def main():
    cli_args = cli()
    ecat = EcatDump(cli_args.ecat)
    if cli_args.json:
        ecat.json_out()
        sys.exit(0)
    if cli_args.dump:
        ecat.show_header()
    if cli_args.affine:
        ecat.show_affine()
    if cli_args.subheader:
        ecat.show_subheaders()
    if cli_args.sidecar:
        ecat.populate_sidecar()
        ecat.show_sidecar()
    if cli_args.convert:
        output_path = pathlib.Path(ecat.make_nifti())
        ecat.populate_sidecar()
        sidecar_path = join(str(output_path.parent), output_path.stem + '.json')
        ecat.show_sidecar(output_path=sidecar_path)


if __name__ == "__main__":
    main()
