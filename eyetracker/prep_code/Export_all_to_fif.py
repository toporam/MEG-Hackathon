#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May  3 15:39:34 2023

@author: jstout
"""

import mne
import glob
import os, os.path as op

data_dict = {
    '001': 'S01_discretePositions',
    '002': 'S01_movingPositions',
    '003': 'S02_discretePositions',
    '004': 'S03_discretePositions',
    '005': 'S04_discretePositions'
   	}

for dset in glob.glob('*.ds'):
    run=dset.split('_')[-1].split('.')[0]
    out_name = data_dict[run]
    
    #Read in data
    raw = mne.io.read_raw_ctf(dset, system_clock='ignore', preload=True)
    
    #Drop the MEG channels
    raw.pick_types(meg=False, misc=True)

    with raw.info._unlock():
        raw.info['comps'] = []
    
    #Save data
    out_fname = f'{out_name}_raw.fif'
    raw.save(out_fname)
