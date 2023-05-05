import mne
#MEG data
data = mne.io.read_raw_fif('eyetracker/data/S01_discretePositions_raw.fif', allow_maxshield=True)