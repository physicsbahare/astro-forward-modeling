# Required NIRCam throughput input provenance

Science runs must use the user's official NIRCam Jan-2025 v7 mean-system throughput files, supplied in `nircam_throughputs_all.zip` (the individual mean-throughput filenames inside are labelled May2024).

Archive SHA256: `1aace14fbcfee640ba286102a97e1acfc80dd14796fa229aa33a479e89caceec`

Required source files and SHA256:
- `F115W_May2024_mean_system_throughput.txt`: `0ed11483342bb380928a1ac5a912706983dadaa6bc8d16b406522b19de4cded6`
- `F150W_May2024_mean_system_throughput.txt`: `d13a549b8f3df2848ecaa8072a0cd296c76322114e971a2c4aa682c95d39e5a0`
- `F277W_May2024_mean_system_throughput.txt`: `8980999603464cf59ad6cea7f31c83ff8553f131d8b6d32b8e4dac81d7ebcfec`
- `F444W_May2024_mean_system_throughput.txt`: `97c148048ed0239b417c494c4cb5663c6d108f2197cee4f650aa0bfec87c3aa1`

The repository intentionally stores provenance/checksums rather than silently copying or updating these external calibration inputs. The science renderer requires an explicit throughput directory and must fail if the files are unavailable or inconsistent. A throughput-version update requires a new provenance receipt and sensitivity check.
