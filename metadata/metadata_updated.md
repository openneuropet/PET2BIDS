# Metadata update report

- Date: 2026-08-25
- BIDS version: 1.11.1
- Schema version: 1.2.7
- Schema source: https://jsr.io/@bids/schema/1.2.7/schema.json

## PET_metadata.json

- Added to recommended: TaskName, Instructions, TaskDescription, CogAtlasID, CogPOID
- Added to optional: BodyPartDetails, BodyPartDetailsOntology
- Moved BodyPart: recommended -> optional
- Moved ReconMethodParameterUnits: mandatory -> recommended
- Moved ReconMethodParameterValues: optional -> recommended
- Moved ReconFilterSize: optional -> recommended
- Preserved local-only recommended: ScanDate

## blood_metadata.json

- No category changes.

## PET_metadata.json blood_recording_fields

- Added: WithdrawalRate, TubingType, TubingLength, DispersionConstant, Haematocrit, BloodDensity, PlasmaFreeFraction, PlasmaFreeFractionMethod, metabolite_polar_fraction, hplc_recovery_fractions
