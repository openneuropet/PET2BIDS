import os
import unittest
import dotenv
from pypet2bids.dicom_convert import Convert

# collect test data test will fail to run without it
dotenv.load_dotenv(dotenv.load_dotenv())


class DicomConvert(unittest.TestCase):
    @classmethod
    def setUp(cls) -> None:
        cls.image_folder = os.environ['TEST_DICOM_IMAGE_FOLDER']
        cls.metadata_path = os.environ['TEST_DICOM_CONVERT_METADATA_FROM_TEMPLATE_PATH']
        cls.metadata_translation_script_path = 'metadata_excel_example_reader.py'
        cls.subject_id = 'dicomconverttestsubject'
        cls.dicom_convert = Convert(image_folder=cls.image_folder,
                                    metadata_path=cls.metadata_path,
                                    metadata_translation_script_path=cls.metadata_translation_script_path,
                                    subject_id=cls.subject_id)

    def test_convert(self):
        what_is = self.dicom_convert
        print('pause')

if __name__ == '__main__':
    unittest.main()
