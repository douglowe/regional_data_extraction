# EMEP data extraction for GM region.

## Setup

The necessary packages can be installed using conda:
```
conda env create --file conda_env.yml
```

## Usage

To extract the model data edit the script `gm_extract_data.py` to define the input files
and required settings. Load the conda environment and run the script:
```
conda activate emep_extract
python gm_extract_data.py
```