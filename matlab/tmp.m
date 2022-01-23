meta = get_pet_metadata('Scanner','PhillipsVereos','TimeZero','ScanStart','tracer','CB36','Radionuclide','C11', ...
               'ModeOfAdministration','infusion','Radioactivity', 605.3220,'InjectedMass', 1.5934,'MolarActivity', 107.66);
dcm2niix4pet('D:\BIDS\ONP\PhilipsData\BODY_DY_CTAC_LIN_VER',meta); % change dcm2nii default

