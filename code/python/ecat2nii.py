import nibabel
import numpy
import pathlib
from read_ecat import read_ecat
import os


def ecat2nii(ecat_file: str, nifti_file: str = '', sif_out=False, affine=None, **kwargs):
    # if a nifti file/path is not included write a nifti next to the ecat file
    if not nifti_file:
        nifti_file = os.path.splitext(ecat_file)[0] + ".nii"
    else:
        nifti_file = nifti_file
    # collect the output folder from the nifti path will use for .sif files
    output_folder = pathlib.Path(nifti_file).parent

    # collect ecat_file
    main_header, sub_headers, data = read_ecat(ecat_file=ecat_file)
    # check for TimeZero supplied via kwargs
    if kwargs.get('TimeZero', None):
        TimeZero = kwargs['TimeZero']
    else:
        print("Metadata TimeZero is missing -- set to ScanStart or empty to use the scanning time as "
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
    for index in range(img_shape[3]):
        print(f"Loading frame {index + 1}")
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

    # rescale for quantitative PET
    max_image = img_temp.max()
    img_temp = img_temp / (max_image * 32767)
    sca = max_image / 32767
    min_image = img_temp.min()
    if min_image < -32768:
        img_temp = img_temp / (min_image * (-32768))
        sca = sca * min_image / (-32768)

    properly_scaled = img_temp * sca * main_header['ECAT_CALIBRATION_FACTOR']

    img_nii = nibabel.Nifti1Image(properly_scaled, affine=affine)

    # nifti header items to include
    img_nii.header.set_xyzt_units('mm', 'unknown')

    # save nifti
    nibabel.save(img_nii, nifti_file)

    # write out timing file
    if sif_out:
        pass

    return nifti_file
