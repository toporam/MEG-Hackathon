import mne
#MEG data
data = mne.io.read_raw_ctf('DATASETNAME.ds', preload=True, system_clock='ignore')