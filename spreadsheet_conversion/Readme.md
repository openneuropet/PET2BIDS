# Spreadsheet conversion

When data are already converted, it can be easier to create metadata separately, here as json file to follow [PET-BIDS](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/09-positron-emission-tomography.html).

## Spreadsheet

You can use the [template](https://github.com/openneuropet/BIDS-converter/blob/main/Metadata_in/metadata_excel_template.xlsx) to prepare the metadata. Note that new/old excel (.xlsx .xls) or open format (.ods) can be used.  

The example files, show the excel file and the resulting conversion as json.

## convert_spreadsheet_metadata.m

The matlab function `convert_spreadsheet_metadata.m` can be called and users are prompted to select a spreadsheet, or it can be passed directly as input. If command line is used, output name can also be specified, overwise the same location and name is used to create the json file.