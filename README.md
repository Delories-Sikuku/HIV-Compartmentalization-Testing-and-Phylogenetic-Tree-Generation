# HIV Compartmentalization Testing and Phylogenetic Tree Generation

This repository renders compartment-coloured phylogenetic trees and runs HyPhy compartmentalization analyses for paired CVL and plasma HIV sequence datasets.

## Setup

Create the analysis environment with Conda:

```powershell
conda env create -f environment.yml
conda activate hyphy_env
```

The workflow requires the `hyphy` command to be available on `PATH` and uses ETE3 to render tree images.

## Protected data setup

Do not commit participant-level sequences, trees, clinical metadata, or analysis outputs. The repository's `.gitignore` excludes the local `data/`, `trees_output/`, and `tests_output/` directories, as well as common sequence, tree, spreadsheet, and log formats.

Create a local `data/` directory with one pair of files for each dataset listed in `datasets.txt`:

```text
data/
  CVL-498-and-PLA-498-Alignment.nex
  CVL-498-and-PLA-498-Alignment-tree.newick
```

Each alignment must use the `CVL` and `PLA` prefixes expected by `tests_config.json`. Store identifiers and clinical metadata only in approved local or access-controlled locations.

## Run

Render radial trees:

```powershell
python build_trees.py
```

Run the configured HyPhy tests and write `tests_output/hyphy_results.xlsx`:

```powershell
python run_tests.py
```

The scripts stop with an explicit error when a required alignment/tree file or the HyPhy executable is unavailable.

## Synthetic validation

The automated tests use temporary synthetic files and a mocked HyPhy process; no participant data or HyPhy installation is needed:

```powershell
python -m unittest -v test_workflow.py
```