# MEG-Hackathon - Eye Tracking
Datasets were collected from 4 subjects.  <br>
These datasets were converted from CTF format to fif (./prep_code/Export_all_to_fif.py), and all of the MEG channels were dropped. <br>
A dot on the screen jumped to random positions during the task (discretePositions files).  The subject would then fixate on the new dot position <br>
The "ground truth" locations are in the .csv files and the calculated positions will be derived from the UADC channels in the MEG files <br>

#### The eyetracking channels are located on the following channels: <br>
Vertical: UADC???? <br>
Horizontal: UADC??? <br>
Pupil Diameter: UADC??? <br>
Projector Stim Onset: UADC016 <br>


## Datasets
MEG data are located in the data directory of this repository <br>
Ground truth stimuli are located in ./stimulus/results/????.csv <br>

## Required install to read datasets
```
#Required to read in the meg data
mamba create --override-channels --channel=conda-forge --name=<<ENVNAME>> mne   
mamba activate <<ENVNAME>>  #might need to use conda activate
```
## Download this repository
```
git clone https://github.com/sebmonte/MEG-Hackathon.git
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

# Stimuli positions
```
pos = pd.read_csv('./results/...csv')
```

