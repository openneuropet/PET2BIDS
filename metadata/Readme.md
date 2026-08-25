# metadata

This folder contains metadata information for PET, some of them being loaded by our Matlab and Python code (ensuring both use the same info).

## [definitions](https://github.com/openneuropet/PET2BIDS/blob/main/metadata/definitions.json)

List of terms, just making sure we agree on what we are talking about.

## [PET_metadata](https://github.com/openneuropet/PET2BIDS/blob/main/metadata/PET_metadata.json)

Lists the mandatory, recommended and optional keys of the [*_pet.json file](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/09-positron-emission-tomography.html#pet-metadata)
 of the BIDS specification.

## [dicom2bids](https://github.com/openneuropet/PET2BIDS/blob/main/metadata/dicom2bids.json)

List of matched keys between dicom tags and json keys, by using this we can:

- check values of the json match the dicom information
- add missing information to the json
- also contains the list of Radionuclide matching the dicom code to a name

## [PET_Radionuclide](https://github.com/openneuropet/PET2BIDS/blob/main/metadata/PET_Radionuclide.mkd)

A markdown table of the CID 4020 PET Radionuclide (same as what is in dicom2bids.json).

## [blood_metadata](https://github.com/openneuropet/PET2BIDS/blob/main/metadata/blood_metadata.json)

Lists the mandatory and recommended keys of the [*_blood.json and *blood.tsv files](https://bids-specification.readthedocs.io/en/stable/04-modality-specific-files/09-positron-emission-tomography.html#blood-recording-data) of the BIDS specification.

## update_metadata.py

Updates the local PET-only metadata requirement files from the latest BIDS schema:

- `PET_metadata.json`
- `blood_metadata.json`
- `metadata_updated.md`

Run from the repository root:

```bash
python metadata/update_metadata.py
```

To preview the report without changing files:

```bash
python metadata/update_metadata.py --dry-run
```

The utility fetches the latest `@bids/schema` package from JSR, reads the PET sidecar and blood recording rules, and maps BIDS `required`, `recommended`, and `optional` levels onto the local `mandatory`, `recommended`, and `optional` fields. Existing local metadata items are never deleted: new upstream items are added, and existing items are moved only when the schema assigns them a different supported level. If JSR is unavailable, the utility tries GitHub schema URLs and then the latest ReadTheDocs schema as a final fallback. Each run writes `metadata_updated.md` with the date, schema version, source URL, and applied changes.
