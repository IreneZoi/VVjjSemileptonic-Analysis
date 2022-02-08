# Semileptonic VV Analysis

## Inputs
- `ntuples`
  - Produced with:
    - Code and Doc: https://github.com/singh-ramanpreet/VVjjSemileptonic-Selection
    - Inputs
      - `NanoAOD` skim
        - Produced with:
          - Code and Doc: https://github.com/singh-ramanpreet/VVjjSemileptonic-NanoSkim
          - Inputs
            - Central `NanoAOD`
            - Custom `NanoAOD`
              - Produced with:
                - Code and Doc: https://github.com/singh-ramanpreet/VBS-customNanoAODProduction/
                - Inputs
                  - Central `MiniAOD`

## Setup this code

NB: The installation should go in the lpc nobackup area!!

### First time
```bash
git clone git@github.com:singh-ramanpreet/VVjjSemileptonic-Analysis
cd VVjjSemileptonic-Analysis
source setup/setup.sh --with-install
```

### For every new `bash` session

```bash
source setup/setup.sh
```

## Analysis

1. [framework](#framework)
2. [analysis flow](#flow-of-the-analysis)
3. [prepare](#prepare)
4. [training](#training)
5. [plotting](#plotting)

### Framework
- variable map: `variables_map.json`
  - for adding additional variables post `ntupling` step
- systematics map: `systematics_map.json`
  - `<tags>`: diboson channel (`zv`, `zjj`, `wv`, `wjj`)
    - systematics: `_<name>` -> `array` of variables
- samples lookup file: `datasets_<year>.json`
    - samples tag: (`data_obs`, `VBS_EWK`, ... )
      - properties:
        - `lumi`: integrated luminosity (1/pb)
        - `filelist.name`: samples name without `_XX.root`
        - `filelist.xs`: cross-section of sample (pb)
        - `filelist.nMC`: effective generated events, `genEventSumw`
        - `filelist.kf`: (optional) k-factor, defaults to `1.0`

Datasets should consistent `nMC`, they are already save in lookup file, to verify the `ntuples` are read properly script `verify_dataset.py` will `hadd` them and print the `nMC` both from file and directly from `ntuples`.

```bash
./verify_dataset.py --datasets datasets_2016.json --location /store/user/rsingh/wv_vbs_ntuples/WVJJTree_2020_Dec_12/2016 --sample-tag all
```

The output will look something like this.

```txt
> ...
> /store/user/rsingh/wv_vbs_ntuples/WVJJTree_2020_Dec_12/2016
> Sample Tag:  VBS_EWK
> ====================================================================
> Sample:  WminusTo2JZTo2LJJ_EWK_LO_SM_MJJ100PTJ10_TuneCUETP8M1_13TeV-madgraph-pythia8
> XS:  0.02982
> k-factor:  1.0
> nMC(in json):  200000.0
> nMC(from hist):  200000.0
> Sample: ...
> ...
```

### Flow of the analysis
- `prepare` (without MVA): process `ntuples` with this `framework` without any MVA inference, this should be fast. Put the `root` files to be used in same `eos` directory, suffix the `root` file name with `<year>` tag, if combining multiple `MC` of multiple years.
  - ↳ `training`: directory path (`eos`) from the previous step will be input pool of `root` files.
      - ↳   `prepare` (with MVA): re-run prepare step, now with training inference.
          - ↳ `plotting`: make plots and datacard for statistical analysis


### Prepare

This step basically makes copy of input root file with additional branches defined in `variables_map.json` and MVA score using training files.

Output file will have `sample_tag` and `xs_weight` branches so that for the next steps dependency on lookup files is not required.

#### 1. Run `prepare` step,

```bash
cd prepare
```

The wrapper `run_prepare.sh` basically runs `prepare_dataset.py` python script. The wrapper basically allows use same executable locally and condor.

`run_prepare.sh` usage:
1.
   - `local`: run interactively
   - `.tar.gz` file: to run on condor
2. `year`
   - `2016`, `2017`, `2018`
   - Note: it will look for file `datasets_<year>.json`
3. `output-folder`
   - it will create output folder in the current directory
4. `sample-name`
   - `.root` file full path to run on
5. `eos_output_path`
   - `eos` path for copying output from condor jobs
   - `None` for running interactively.
6. `isWithoutMVA`
   - default: `No`
   - `Yes` to run without MVA inference


Interactive example (without MVA)

```bash
./run_prepare.sh local 2016 output root://cmseos.fnal.gov//store/user/rsingh/wv_vbs_ntuples/WVJJTree_2020_Dec_12/2016/WminusToLNuWminusTo2JJJ_EWK_LO_SM_MJJ100PTJ10_TuneCUETP8M1_13TeV-madgraph-pythia8_01.root None Yes
```

Condor submission (adjust the parameters accordingly)

1. Make sample list

```bash
./make_list.sh /eos/uscms/store/user/rsingh/wv_vbs_ntuples/WVJJTree_2020_Dec_12 2016
./make_list.sh /eos/uscms/store/user/rsingh/wv_vbs_ntuples/WVJJTree_2020_Dec_12 2017
./make_list.sh /eos/uscms/store/user/rsingh/wv_vbs_ntuples/WVJJTree_2020_Dec_12 2018
```

Output will be in `sample_list/${year}.txt`

2. Download training

Change the script `download_training.sh` to update the training location.

```bash
rm ./trainings/*.xml
rm ./trainings/*.txt
./download_training.sh
```

3. Submit jobs

```bash
condor_submit tar_file=setup.tar.gz \
year=2018 \
output_dir=2018 \
eos_path=root://cmseos.fnal.gov//store/user/rsingh/wv_vbs_ntuples/mva_z11_2020_Dec_12/ \
is_without_mva=No \
prepare_submit.jdl
```

The output will be in `eos_path/output_dir` and logs in `./condor_logs`.


### Training
### Plotting
