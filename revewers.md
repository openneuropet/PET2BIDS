- [ ] `Statement of needs` do not state the need of software, you may add a small trivial phrase why pet2bids exists (not what it does).

The guidelines https://joss.readthedocs.io/en/latest/submitting.html say 'A Statement of need section that clearly illustrates the research purpose of the software and places it in the context of related work'. Therefore, what it does is required. We have added however the 'why' we created it as introductory sentence.

- [ ] JOSS asks to compare the software with similar tools

There are no other tools doing that type of conversion for PET data, and mention that in the 'why' introductory sentence.

- [ ] `File conversation`/`PET Metadata`/`Spreadsheet conversation` may be worth to be put in the dedicated (sub)sections

We could but rather stick to the minimalistic recommended JOSS guideline section format.

- [ ] Are conversation, metadata and spreadsheets export are extensive list of pet2bids tools? 

The section on conversion was rewritten to make it clear is it done using a single wrapper function for DICOM files or a single wrapper function for Ecat files. We also clarified that there are 3 spreadsheets export functions.

- [ ] In Metadata/Spreadsheet section you need to change `JSON file` to `sidecar JSON file`, first one is an any generic JSON file, second is BIDS specific one that supplements image data with metadata.

JSON are always sidecar files, we now distinguish the image from tsv sidecar JSON.

- [ ] In spreadsheets section, I don't really like the usage of points (`(a)` ,  `(i)`, etc.) -- you never reference them. Maybe replace the first `and` at line 54 by `as well as`, and make the iteration in lines 55-58 to a list. I think it would be easier to read.

Given that we now explain that there are 3 functions, those points are logical - but removed a and b.

### Inline comments

- [ ] On line 27, missing references to ECAT and DICOM formats

added ref to DICOM and added working for ECAT is proprietary

- [ ] On line 27, by time measurements do you mean the timing of each PET frame? Just to be sure.

not necessarily, frame information is ofen present, so we added 'e.g. time zero' as a different example. 

- [ ] Line 30 is a little bit confusing, do you mean by `library code, allowing conversion ... using the command line`, that you provide a library **and** a (command line) script?

This sentence has been removed.

- [ ] Line 30, I may be wrong here, but `library code` reads as a code that do something with library. Library of tools/functions sounds better for me.

We now use code library throughout.

- [ ]  Line 31, `it can be integrated into software` because it's library, not because it modular. Need to be rephrased.

Sure - rewritten. 

- [ ]  Line 39, needed references for BT Christian and RF Muzic, are those people or tools or functions?

Those are the people who wrote the ecat reading function.

- [ ]  Line 43, What do you mean by `the further testing of data reading`?

We meant that we tested the reading/writting of the data, i.e. which bits are read according to the PET data frames. Referering now explicitly to [ecat validation](https://github.com/openneuropet/PET2BIDS/tree/main/ecat_validation).

- [ ]  Line 46, It's not immediately clear that `JSON files created from reading PET` refers to JSON sidecar files from conversion using pet2bids.

fixed

- [ ]  Line 46, `data are always missing...`, `always` seems too strong, maybe better to replace by `often` or `usually`.

no 'always' is correct - we have never seen a JSON file with all the metadata simply because information from the scanner do not encode eg pharmaceutical information.

- [ ] Line 48, as original PET data (DICOM/ECAT) don't contain JSON, there no `original JSON file`, I guess you meant sidecar JSON file?

fixed

- [ ] Line 48, before you provided the names of function (for ex. ecat2nii for conversion), but here you use `PET JSON updater`, can you change it into function name(s)?

fixed

- [ ] Line 52, is `xls, xlsx, csv, tsv, bld` it extensive list of tabular data formats in existence, or list of data  that bids2pet supports? If it's first, than an `for example` may be needed.

changes to Supported formats are .xls, .xlsx, .csv, .tsv and .bld.

- [ ] Line 57, what is `blood.tsv` file, you never mentioned it before. Maybe rephrase it to `exports blood data from PMOD tabular file`?

The conversion goes the other way around. We have now changed this to BIDS blood.tsv to make it clear.