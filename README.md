# Automated Illumina BCL to FASTQ Conversion

An automated workflow for monitoring Illumina sequencing runs and converting base call (BCL) files to FASTQ format using Illumina BCL Convert in a Docker container. The workflow validates sequencing run status, standardizes sample sheet names, initiates demultiplexing, manages output files, and restores file ownership for downstream processing.

## Features

- Automated discovery of recent sequencing runs.
- Validation of sequencing run completion.
- Detection and exclusion of previously converted runs.
- Automated sample sheet identification and renaming.
- Docker based execution of Illumina BCL Convert (v3.9.3).
- Demultiplexing with strict mode enabled by default.
- Consolidation of FASTQ files from multiple lanes.
- Integration of index metrics with Illumina Sequencing Analysis Viewer (SAV).
- Restoration of file and directory ownership.
- Error detection and logging.

## Workflow

1. Scan the configured sequencing output directory.
2. Identify sequencing runs generated within the last 24 hours.
3. Verify sequencing run completion.
4. Check whether BCL to FASTQ conversion has already completed.
5. Identify and rename the sample sheet to `SampleSheet.csv`.
6. Initiate BCL Convert in a detached Docker container.
7. Check conversion status after an initial waiting period.
8. Copy `IndexMetricsOut.bin` to the `InterOp` directory upon successful conversion.
9. Restore file ownership to match the original sequencing run directory.
10. Report conversion errors when completion cannot be verified.

## Requirements

- Linux
- Python 3.11
- Docker
- Illumina BCL Convert 3.9.3
- Access to Illumina sequencing run directories
- Appropriate permissions for Docker execution and file ownership management

The Python implementation uses standard library modules and local utility modules.

## Configuration

Configure the sequencing data directory in `utils/global_vars.py`:

```python
NGSDATA = "/path/to/sequencing/runs"
```

The workflow uses the following local utility modules:

| Module | Description |
|---|---|
| `utils.global_vars` | Sequencing data directory configuration |
| `utils.run_validation` | Sequencing run and conversion status validation |
| `utils.mnt_win` | Windows network drive mounting utilities (imported but not used in the current workflow) |

Pull the BCL Convert Docker image:

```bash
docker pull rakabari/bcl-convert:3.9.3
```

## Usage

Run the workflow against the configured sequencing data directory:

```bash
python3 run_bclconvert.py
```

Alternatively, process sequencing runs from a different directory:

```python
from run_bclconvert import run_bclconvert_on_output

run_bclconvert_on_output("/path/to/sequencing/runs")
```

To process an individual sequencing run:

```python
from run_bclconvert import run_bclconvert

run_bclconvert("/path/to/sequencing/run")
```

## BCL Convert Parameters

| Parameter | Value |
|---|---|
| BCL Convert version | 3.9.3 |
| Strict mode | `true` |
| Force output | Enabled |
| No lane splitting | `true` |
| Container execution | Detached |
| Container removal after exit | Enabled |

## Output Directory Structure

Conversion results are stored within the original sequencing run directory.

```text
Sequencing_Run/
├── Data/
├── InterOp/
│   └── IndexMetricsOut.bin
├── RunInfo.xml
├── SampleSheet.csv
└── bclConvert/
    ├── *.fastq.gz
    ├── Reports/
    │   └── IndexMetricsOut.bin
    └── Logs/
        └── Errors.log
```

## Error Handling

The workflow performs validation before initiating conversion to prevent premature or redundant processing. If conversion completion cannot be verified, the workflow reports the contents of the BCL Convert error log. Unexpected exceptions are recorded through Python's logging module.

## Applications

This workflow supports automated sequencing data processing in clinical molecular diagnostics, genomics laboratories, and research environments. It provides a standardized interface between Illumina sequencing instruments and downstream bioinformatics pipelines.
