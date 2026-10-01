# Running the corrected GOLD91 clean gate off-laptop

## Recommended cloud target

For the current clean native -> z=3 two-branch gate, Kaggle is a better fit than standard GitHub-hosted Actions.

The run is object-parallel and restartable. The 91-object bin can be split into three deterministic chunks of about 30 objects each and merged afterward.

## Minimal GOLD91 cloud bundle

The clean gate does not need the full real-background injection products. Package only the inputs required by the active notebook setup and PSF evaluation, for example:

- GOLD403/GOLD91 catalog rows;
- master initialization rows used for tile/position lookup;
- required NIRCam PSFEx files;
- the small context/coordinate manifest needed for target PSF evaluation;
- any compact morphology tables/cutouts required by the setup.

Do not upload the full real-background mosaic collection unless the real-injection stage is being run.

## Suggested split

Use a deterministic ordering by source ID and three chunks:

```
chunk 0: rows 0,3,6,...
chunk 1: rows 1,4,7,...
chunk 2: rows 2,5,8,...
```

or three contiguous chunks of 30/30/31. Each chunk writes its own restart-safe CSV. Merge only after all chunks finish.

## GitHub Actions

Standard GitHub-hosted runners are useful for tests and compact verification, but the full fitting workload is not a good default there because the job has a finite hosted-runner execution window and the repository intentionally does not contain the large survey data.

GitHub Actions remains appropriate for:

- regression tests;
- syntax/import checks;
- small synthetic closed-loop cases;
- receipt validation.

Use Kaggle or another compute node for the long object-level fitting.
