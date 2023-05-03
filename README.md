# MEG-Hackathon
2023 MEG Eye-Tracking Hackathon

## Datasets
Located in the data directory of this repository

## Required install to read datasets
```
#Required to read in the meg data
mamba create --override-channels --channel=conda-forge --name=<<ENVNAME>> mne   
mamba activate <<ENVNAME>>  #might need to use conda activate
```
## If you are using spyder - find the version you need here: 
https://docs.spyder-ide.org/current/troubleshooting/common-illnesses.html <br>
`pip install spyder-kernels==<<VERSION>>`

## To read in the data
```
import mne
#MEG data
data = mne.io.read_raw_ctf('DATASETNAME.ds', preload=True, system_clock='ignore')
```

#Stimuli positions
```
pos = pd.read_csv('./results/...csv')
```

