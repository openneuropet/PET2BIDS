"""
Contains class ecat2ii, used to write ecat information out to a nifti file, depends on
`nibabel <https://nipy.org/nibabel/>`_ and  :func:`pypet2bids.read_ecat.read_ecat`.

| *Authors: Anthony Galassi*
| *Copyright OpenNeuroPET team*
"""
import datetime
import nibabel
import numpy
import pathlib
from pypet2bids.read_ecat import read_ecat
import os
import pickle

try:
    import helper_functions
except ModuleNotFoundError:
    import pypet2bids.helper_functions as helper_functions


logger = helper_functions.log()

def ecat2nii(ecat_main_header=None,
             ecat_subheaders=None,
             ecat_pixel_data=None,
             ecat_file=None,
             nifti_file: str = '',
             sif_out=False,
             affine=None,
             save_binary=False,
             **kwargs):
    """
    Converts an ECAT file into a nifti and a sidecar json, used in conjunction with
    :func:`pypet2bids.read_ecat.read_ecat`
    
    :param ecat_main_header: the main header of an ECAT file
    :param ecat_subheaders: the subheaders for each frame of the ECAT file
    :param ecat_pixel_data: the imaging/pixel data from the ECAT file
    :param ecat_file: the path to the ECAT file, required and used to create .nii and .json output files
    :param nifti_file: the desired output path of the nifti file
    :param sif_out: outputs a .sif file containing the images pixel data
    :param affine: a user supplied affine, this is gathered from the ECAT if not supplied.
    :param save_binary: dumps a pickled ECAT object, you probably shouldn't be using this.
    :param kwargs: additional key value pairs that one wishes to add to the sidecar json accompanying a converted ECAT
        nii image
    :return: a nibabel nifti object if one wishes to muddle with the object in python and not in a .nii file

    """

    # if a nifti file/path is not included write a nifti next to the ecat file
    if not nifti_file:
        nifti_file = os.path.splitext(ecat_file)[0] + ".nii"
    else:
        nifti_file = nifti_file

    if not pathlib.Path(nifti_file).parent.exists():
        pathlib.Path(nifti_file).parent.mkdir(parents=True, exist_ok=True)

    # collect the output folder from the nifti path will use for .sif files
    output_folder = pathlib.Path(nifti_file).parent
    nifti_file_w_out_extension = os.path.splitext(str(pathlib.Path(nifti_file).name))[0]

    # if already read nifti file skip re-reading
    if ecat_main_header is None and ecat_subheaders is None and ecat_pixel_data is None and ecat_file:
        # collect ecat_file
        main_header, sub_headers, data = read_ecat(ecat_file=ecat_file)
    elif ecat_file is None and type(ecat_main_header) is dict and type(ecat_subheaders) is list and type(
            ecat_pixel_data) is numpy.ndarray:
        main_header, sub_headers, data = ecat_main_header, ecat_subheaders, ecat_pixel_data
    else:
        raise Exception("Must pass in filepath for ECAT file or "
                        "(ecat_main_header, ecat_subheaders, and ecat_pixel data "
                        f"got ecat_file={ecat_file}, type(ecat_main_header)={type(ecat_main_header)}, "
                        f"type(ecat_subheaders)={type(ecat_subheaders)}, "
                        f"type(ecat_pixel_data)={type(ecat_pixel_data)} instead.")

    # check for TimeZero supplied via kwargs
    if kwargs.get('TimeZero', None):
        TimeZero = kwargs['TimeZero']
    else:
        logger.warn("Metadata TimeZero is missing -- set to ScanStart or empty to use the scanning time as "
              "injection time")

    # get image shape
    img_shape = data.shape
    shape_from_headers = (sub_headers[0]['X_DIMENSION'],
                          sub_headers[0]['Y_DIMENSION'],
                          sub_headers[0]['Z_DIMENSION'],
                          main_header['NUM_FRAMES'])

    # make sure number of data elements matches frame number
    single_frame = False
    if img_shape[3] == 1 and img_shape[0:2] == shape_from_headers[0:2]:
        single_frame = True
    if img_shape != shape_from_headers and not single_frame:
        raise Exception(
            f"Mis-match between expected X,Y,Z, and Num. Frames dimensions ({shape_from_headers} obtained from headers"
            f"and shape of imaging data ({img_shape}")

    # format data into acceptable shape for nibabel, by first creating empty matrix
    img_temp = numpy.zeros(shape=(sub_headers[0]['X_DIMENSION'],
                                  sub_headers[0]['Y_DIMENSION'],
                                  sub_headers[0]['Z_DIMENSION'],
                                  main_header['NUM_FRAMES']),
                           dtype=numpy.dtype('>f4'))

    # collect timing information
    start, delta = [], []

    # collect prompts and randoms
    prompts, randoms = [], []

    # load frame data into img temp
    for index in reversed(range(img_shape[3])):  # Don't throw stones working from existing matlab code
        print(f"Loading frame {index + 1}")
        # save out our slice of data before flip to a text file to compare w/ matlab data
        img_temp[:, :, :, index] = numpy.flip(numpy.flip(numpy.flip(
            data[:, :, :, index].astype(numpy.dtype('>f4')) * sub_headers[index]['SCALE_FACTOR'], 1), 2), 0)
        start.append(sub_headers[index]['FRAME_START_TIME'] * 60)  # scale to per minute
        delta.append(sub_headers[index]['FRAME_DURATION'] * 60)  # scale to per minute

        if main_header.get('SW_VERSION', 0) >= 73:
            # scale both to per minute
            prompts.append(sub_headers[index]['PROMPT_RATE'] * sub_headers[index]['FRAME_DURATION'] * 60)
            randoms.append(sub_headers[index]['RANDOM_RATE'] * sub_headers[index]['FRAME_DURATION'] * 60)
        else:
            # this field is not available in ecat 7.2
            prompts.append(0)
            randoms.append(0)

    final_image = img_temp * main_header['ECAT_CALIBRATION_FACTOR']

    qoffset_x = -1 * (
        ((sub_headers[0]['X_DIMENSION'] * sub_headers[0]['X_PIXEL_SIZE'] * 10 / 2) - sub_headers[0][
            'X_PIXEL_SIZE'] * 5))

    qoffset_y = -1 * (
        ((sub_headers[0]['Y_DIMENSION'] * sub_headers[0]['Y_PIXEL_SIZE'] * 10 / 2) - sub_headers[0][
            'Y_PIXEL_SIZE'] * 5))

    qoffset_z = -1 * (
        ((sub_headers[0]['Z_DIMENSION'] * sub_headers[0]['Z_PIXEL_SIZE'] * 10 / 2) - sub_headers[0][
            'Z_PIXEL_SIZE'] * 5))

    # build affine if it's not included in function call
    if not affine:
        t = numpy.identity(4)
        t[0, 0] = sub_headers[0]['X_PIXEL_SIZE'] * 10
        t[1, 1] = sub_headers[0]['Y_PIXEL_SIZE'] * 10
        t[2, 2] = sub_headers[0]['Z_PIXEL_SIZE'] * 10

        t[3, 0] = qoffset_x
        t[3, 1] = qoffset_y
        t[3, 2] = qoffset_z

        # note this affine is the transform of of a nibabel ecat object's affine
        affine = t

    img_nii = nibabel.Nifti1Image(final_image, affine=affine)

    # populating nifti header
    if img_nii.header['sizeof_hdr'] != 348:
        img_nii.header['sizeof_hdr'] = 348
    # img_nii.header['dim_info'] is populated on object creation
    # img_nii.header['dim']  is populated on object creation
    img_nii.header['intent_p1'] = 0
    img_nii.header['intent_p2'] = 0
    img_nii.header['intent_p3'] = 0
    # img_nii.header['datatype'] # created on invocation seems to be 16 or int16
    # img_nii.header['bitpix'] # also automatically created and inferred 32 as of testing w/ cimbi dataset
    # img_nii.header['slice_type'] # defaults to 0
    # img_nii.header['pixdim'] # appears as 1d array of length 8 we rescale this
    img_nii.header['pixdim'] = numpy.array(
        [1,
         sub_headers[0]['X_PIXEL_SIZE'] * 10,
         sub_headers[0]['Y_PIXEL_SIZE'] * 10,
         sub_headers[0]['Z_PIXEL_SIZE'] * 10,
         0,
         0,
         0,
         0])
    img_nii.header['vox_offset'] = 352

    # TODO img_nii.header['scl_slope'] # this is a NaN array by default but apparently it should be the dose calibration
    #  factor img_nii.header['scl_inter'] # defaults to NaN array
    img_nii.header['scl_slope'] = main_header['ECAT_CALIBRATION_FACTOR']
    img_nii.header['scl_inter'] = 0
    img_nii.header['slice_end'] = 0
    img_nii.header['slice_code'] = 0
    img_nii.header['xyzt_units'] = 10
    img_nii.header['cal_max'] = final_image.min()
    img_nii.header['cal_min'] = final_image.max()
    img_nii.header['slice_duration'] = 0
    img_nii.header['toffset'] = 0
    img_nii.header['descrip'] = "OpenNeuroPET ecat2nii.py conversion"
    # img_nii.header['aux_file'] # ignoring as this is set to '' in matlab
    img_nii.header['qform_code'] = 0
    img_nii.header['sform_code'] = 1  # 0: Arbitrary coordinates;
    # 1: Scanner-based anatomical coordinates;
    # 2: Coordinates aligned to another file's, or to anatomical "truth" (co-registration);
    # 3: Coordinates aligned to Talairach-Tournoux Atlas; 4: MNI 152 normalized coordinates

    img_nii.header['quatern_b'] = 0
    img_nii.header['quatern_c'] = 0
    img_nii.header['quatern_d'] = 0
    # Please explain this
    img_nii.header['qoffset_x'] = qoffset_x
    img_nii.header['qoffset_y'] = qoffset_y
    img_nii.header['qoffset_z'] = qoffset_z
    img_nii.header['srow_x'] = numpy.array([sub_headers[0]['X_PIXEL_SIZE']*10, 0, 0, img_nii.header['qoffset_x']])
    img_nii.header['srow_y'] = numpy.array([0, sub_headers[0]['Y_PIXEL_SIZE']*10, 0, img_nii.header['qoffset_y']])
    img_nii.header['srow_z'] = numpy.array([0, 0, sub_headers[0]['Z_PIXEL_SIZE']*10, img_nii.header['qoffset_z']])

    img_nii.header['intent_name'] = ''
    img_nii.header['magic'] = 'n + 1 '

    # nifti header items to include
    img_nii.header.set_xyzt_units('mm', 'unknown')

    # save nifti
    nibabel.save(img_nii, nifti_file)

    # used for testing veracity of nibabel read and write.
    if save_binary:
        pickle.dump(img_nii, open(nifti_file + '.pickle', "wb"))

    # write out timing file
    if sif_out:
        with open(os.path.join(output_folder, nifti_file_w_out_extension + '.sif'), 'w') as sif_file:
            scantime = datetime.datetime.fromtimestamp(main_header['SCAN_START_TIME'])
            scantime = scantime.astimezone().isoformat()
            sif_file.write(f"{scantime} {len(start)} 4 1\n")
            for index in reversed(range(len(start))):
                start_i = round(start[index])
                start_i_plus_delta_i = start_i + round(delta[index])
                prompt = round(prompts[index])
                random = round(randoms[index])
                output_string = f"{start_i} {start_i_plus_delta_i} {prompt} {random}\n"
                sif_file.write(output_string)

    return img_nii
