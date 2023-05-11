import mne
import pandas as pd 
import numpy as np
import math, mne
from scipy import stats
from scipy.signal import butter,filtfilt
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

import eyetracker
modulepath = eyetracker.__path__[0]
import os


#Define Screen Size
global screensize_pix
screensize_pix=[1024, 768]

#Set channels where eyetracking happened and where triggers happened
eye_channel = ['UADC009-2104', 'UADC010-2104', 'UADC013-2104']
trigger_channel = ['UADC016-2104']

#Read in eyetracking data
subjID = 'S04'
data = mne.io.read_raw_fif(os.path.join(modulepath, 'data',f'{subjID}_discretePositions_raw.fif'), preload=True)
eyeData = data.copy().pick_channels(eye_channel)
triggerData = data.copy().pick_channels(trigger_channel)._data.flatten()

#Get refresh rate
global et_refreshrate
meg_refreshrate = et_refreshrate = eyeData.info['sfreq']

#find trial onsets based on ADC016 channel
onsets = np.where(triggerData < -4)[0]
index = np.insert(np.where(np.diff(onsets) > 5)[0]+1,0,0)
newonsets = onsets[index]

#What does this show again?
plt.hist(np.diff(newonsets)/eyeData.info['sfreq'])
plt.show()
events = np.zeros([len(newonsets),3])
events[:,0] = newonsets
events[:,2] = 1
events = events.astype(int)

#Plot showing when triggers occurred that indicate onset of a stimulus
plt.plot(triggerData)
plt.scatter(newonsets,triggerData[newonsets])
plt.show()

epochs = mne.Epochs(eyeData, events, tmin=0, tmax=3, baseline = None)

for i in range(epochs.get_data().shape[0]):
    plt.plot(epochs.times, epochs.get_data()[i,0,:])
plt.show()


## Helper functions

def crop_trailing_zeros(raw_eyes):
    '''
    the index of 20 consecutive zeros is used as an identifier to a terminated run (when user hit "abort")
    '''
    idx_crop = np.where((np.diff(np.convolve(np.ones(20),raw_eyes._data[2,:]==0)))==1)[0][0]
    raw_eyes.crop(0,idx_crop/raw_eyes.info['sfreq'])
    return raw_eyes

def volts_to_pixels(x,y,pupil,minvoltage,maxvoltage,minrange,maxrange,screenbottom,screenleft,screenright,screentop,scaling_factor):
    S_x                                             = ((x-minvoltage)/(maxvoltage-minvoltage))*(maxrange-minrange)+minrange
    S_y                                             = ((y-minvoltage)/(maxvoltage-minvoltage))*(maxrange-minrange)+minrange
    Xgaze                                           = S_x*(screenright-screenleft+1)+screenleft
    Ygaze                                           = S_y*(screenbottom-screentop+1)+screentop
    return(Xgaze,Ygaze)

def deviation_calculator(tv,dia,is_valid,t_interp,smooth_filt_a,smooth_filt_b):
    dia_valid                                       = dia[[x and y for x,y in zip(is_valid,~np.isnan(dia))]]
    t_valid                                         = tv[[x and y for x,y in zip(is_valid,~np.isnan(dia))]]
    interp_f_lin                                    = interp1d(t_valid,dia_valid,kind='linear',bounds_error=False)
    interp_f_near                                   = interp1d(t_valid,dia_valid,kind='nearest',fill_value='extrapolate')
    extrapolated                                    = interp_f_near(t_interp)
    uniform_baseline                                = interp_f_lin(t_interp)
    uniform_baseline[np.isnan(uniform_baseline)]    = extrapolated[np.isnan(uniform_baseline)]
    smooth_uniform_baseline                         = filtfilt(smooth_filt_b,smooth_filt_a,uniform_baseline)
    interp_f_baseline                               = interp1d(t_interp,smooth_uniform_baseline,kind='linear',bounds_error=False)
    smooth_baseline                                 = interp_f_baseline(tv)
    dev = np.abs(dia-smooth_baseline)

    return(dev,smooth_baseline)


def raw2df(raw_et, minvoltage=-5, maxvoltage=5, minrange=-0.2, maxrange=1.2,
           screenbottom=767, screenleft=0, screenright=1023, screentop=0, 
           screensize_pix=screensize_pix):
    '''
    Convert the MEG data lines (volts) to pixels for x/y and return a pandas
    dataframe.
    
    Median centering is performed on the data to reduce drift over the session
    Parameters
    ----------
    raw_et : mne raw
        Raw MNE dataset consisting of eye tracker channels.
    minvoltage : int or float
        DESCRIPTION.
    maxvoltage : TYPE
        DESCRIPTION.
    minrange : TYPE
        DESCRIPTION.
    maxrange : TYPE
        DESCRIPTION.
    screenbottom : TYPE
        DESCRIPTION.
    screenleft : TYPE
        DESCRIPTION.
    screenright : TYPE
        DESCRIPTION.
    screentop : TYPE
        DESCRIPTION.
    screensize_pix : TYPE
        DESCRIPTION.
    Returns
    -------
    raw_et_df : TYPE
        DESCRIPTION.
    '''
    raw_et_df                                       = pd.DataFrame(raw_et._data.T,columns=['x_volts','y_volts','pupil'])
    raw_et_df['x'],raw_et_df['y']                   = volts_to_pixels(raw_et_df['x_volts'],raw_et_df['y_volts'],raw_et_df['pupil'],minvoltage,maxvoltage,minrange,maxrange,screenbottom,screenleft,screenright,screentop,scaling_factor=978.982673828819)
    raw_et_df['x']                                  = raw_et_df['x']-screensize_pix[0]/2
    raw_et_df['x']                                  = raw_et_df['x']-np.median(raw_et_df['x'])
    raw_et_df['y']                                  = raw_et_df['y']-screensize_pix[1]/2
    raw_et_df['y']                                  = raw_et_df['y']-np.median(raw_et_df['y'])
    raw_et_df['pupil']                              = raw_et_df['pupil']-np.median(raw_et_df['pupil'])
    raw_et_df['time']                               = raw_et.times
    return raw_et_df


# Step 1: We are removing all samples where x,y is outside of the screen
def remove_invalid_samples(eyes,tv,screensize_pix=screensize_pix):
    withinwidth                                     = np.abs(eyes['x'])<(screensize_pix[0]/2)
    withinheight                                    = np.abs(eyes['y'])<(screensize_pix[1]/2)
    is_valid                                        = np.array([x and y for x,y in zip(withinwidth,withinheight)]).astype(bool)
    if not any(is_valid):
        is_valid                                    = remove_loners(is_valid,et_refreshrate)
        is_valid                                    = expand_gap(tv,is_valid)

    return is_valid.astype(bool)

# Step 2: Checking how much the pupil dliation changes from timepoint to timepoint and exclude timepoints where the dilation change is large
def madspeedfilter(tv,dia,is_valid):
    max_gap                                     = 200
    dilation                                    = dia[is_valid]
    cur_tv                                      = tv[is_valid]
    cur_dia_speed                               = np.diff(dilation)/np.diff(cur_tv)
    cur_dia_speed[np.diff(cur_tv)>max_gap]      = np.nan

    back_dilation                               = np.pad(cur_dia_speed,(1,0),constant_values=np.nan)
    fwd_dilation                                = np.pad(cur_dia_speed,(0,1),constant_values=np.nan)
    back_fwd_dilation                           = np.vstack([back_dilation,fwd_dilation])

    max_dilation_speed                          = np.empty_like(dia)
    max_dilation_speed[is_valid]                = np.nanmax(np.abs(back_fwd_dilation),axis=0)
    max_dilation_speed

    mad                                         = np.nanmedian(np.abs(max_dilation_speed-np.nanmedian(max_dilation_speed)))
    mad_multiplier                              = 16 # as defined in Kret et al., 2019
    if mad == 0: 
        print('mad is 0, using dilation speed plus constant as threshold')
        threshold                               = np.nanmedian(max_dilation_speed)+mad_multiplier
    else:
        threshold                               = np.nanmedian(max_dilation_speed)+mad_multiplier*mad
    print('threshold: ' + str(threshold))
    

    valid_out                                   = np.array(is_valid.copy())

    valid_out[max_dilation_speed>=threshold]    = False
    valid_out                                   = remove_loners(valid_out.astype(bool),et_refreshrate)
    valid_out                                   = expand_gap(tv,valid_out)
    valid_out                                   = remove_loners(valid_out.astype(bool),et_refreshrate)

    return valid_out.astype(bool)

# Step 3: Fitting a smooth line and exclude samples that deviate from that fitted line
def mad_deviation(tv,dia,is_valid):
    n_passes                                    = 4
    mad_multiplier                              = 16
    interp_fs                                   = 100
    lowpass_cf                                  = 16
    [smooth_filt_b,smooth_filt_a]               = butter(1,lowpass_cf/(interp_fs/2))
    t_interp                                    = np.arange(tv[0],tv[-1],1000/lowpass_cf)
    dia[~is_valid]                              = np.nan
    is_valid_running                            = is_valid.copy()
    residuals_per_pass                          = np.empty([len(is_valid),n_passes])
    smooth_baseline_per_pass                    = np.empty([len(is_valid),n_passes])

    is_done                                     = False
    for pass_id in range(n_passes):
        if is_done: 
            break
        is_valid_start                          = is_valid_running.copy()

        residuals_per_pass[:,pass_id], smooth_baseline_per_pass[:,pass_id] = deviation_calculator(tv,dia,[x and y for x, y in zip(is_valid_running, is_valid)],t_interp,smooth_filt_a,smooth_filt_b)

        mad                                     = np.nanmedian(np.abs(residuals_per_pass[:,pass_id]-np.nanmedian(residuals_per_pass[:,pass_id])))
        threshold                               = np.nanmedian(residuals_per_pass[:,pass_id])+mad_multiplier*mad

        is_valid_running                        = [x and y for x,y in zip((residuals_per_pass[:,pass_id] <= threshold), is_valid)]
        is_valid_running                        = remove_loners(np.array(is_valid_running).astype(bool),et_refreshrate)
        is_valid_running                        = expand_gap(tv,np.array(is_valid_running).astype(bool))
        
        if (pass_id>0 and np.all(is_valid_start==is_valid_running)):
            is_done                             = True
    valid_out                                   = is_valid_running
    return valid_out.astype(bool)


def remove_loners(is_valid,et_refreshrate):
    lonely_sample_max_length                        = 100 #in ms
    time_separation                                 = 40 #in ms
    valid_idx                                       = np.where(is_valid)[0]
    gap_start                                       = valid_idx[np.where(np.pad(np.diff(valid_idx),(0,1),constant_values=1)>1)]
    gap_end                                         = valid_idx[np.where(np.pad(np.diff(valid_idx),(1,0),constant_values=1)>1)]
    start_valid_idx                                 = [valid_idx[0]]
    end_valid_idx                                   = [valid_idx[-1]]
    valid_data_chunks                               = np.reshape(np.sort(np.concatenate([start_valid_idx,gap_start,gap_end,end_valid_idx])),[-1,2])
    size_valid_data_chunks                          = np.diff(valid_data_chunks,axis=1)
    size_idx                                        = np.where((size_valid_data_chunks/et_refreshrate*1000)<lonely_sample_max_length)[0]
    separation                                      = np.squeeze(np.diff(np.reshape(np.sort(np.concatenate([gap_start,gap_end])),[-1,2]),axis=1))
    if separation.shape == (): separation = [separation]
    sep_idx                                         = np.where(np.pad([i>(time_separation*1/et_refreshrate) for i in separation],(1,0)))[0]
    data_chunks_to_delete                           = valid_data_chunks[np.intersect1d(sep_idx,size_idx)]

    valid_out                                       = is_valid.copy()
    for i in data_chunks_to_delete:
        valid_out[np.arange(i[0],i[1]+1)]           = 0

    print('removed ' + str(is_valid.sum()-valid_out.sum()) + ' samples')
    
    return valid_out.astype(bool)

def expand_gap(tv,is_valid):
    min_gap_width                                   = 75
    max_gap_width                                   = 2000
    pad_back                                        = 100
    pad_forward                                     = 150
    valid_t                                         = tv[is_valid]
    valid_idx                                       = np.where(is_valid)[0]
    gaps                                            = np.diff(valid_t)

    # Convert to samples 
    for i in min_gap_width, max_gap_width, pad_back, pad_forward:
        i/=et_refreshrate

    needs_padding                                   = [x and y for x,y in zip(gaps>min_gap_width,gaps<max_gap_width)]
    gap_start_t                                     = valid_t[np.pad(needs_padding,(0,1),constant_values=False)]
    gap_end_t                                       = valid_t[np.pad(needs_padding,(1,0),constant_values=False)]

    remove_idx = []
    for i_start,i_end in zip(gap_start_t,gap_end_t):
        # when the gap is super large, it's most likely a recording artifact (and not an eyeblink), so we should clean around it more
        if i_end -i_start > 500:
            pb                                      = pad_back * 2
            pf                                      = pad_forward * 2
        else:
            pb                                      = pad_back
            pf                                      = pad_forward
        remove_idx.extend(np.where([x and y for x,y in zip(valid_t>(i_start-pb),valid_t<(i_end+pf))])[0])
    remove_idx                                      = np.unique(remove_idx)

    if remove_idx.any():
        is_valid[valid_idx[remove_idx]]             = False
    return is_valid

# This is the last step of the preocessing, all invalid samples are removed and the data is detrended
def remove_invalid_detrend(eyes_in,is_valid,isdetrend):
    all_tp                                          = np.arange(len(eyes_in))
    eyes_in[~is_valid]                              = np.nan
    if isdetrend:
        m, b, _, _, _                               = stats.linregress(all_tp[is_valid],eyes_in[is_valid])
        eyes_in                                     = eyes_in - (m*all_tp + b)
    return eyes_in


def pix_to_deg(full_size_pix,screensize_pix=screensize_pix,screenwidth_cm=42,screendistance_cm=75):
    pix_per_cm = screensize_pix[0]/screenwidth_cm
    size_cm = full_size_pix/pix_per_cm
    dva = math.atan(size_cm/2/screendistance_cm)*2
    return np.rad2deg(dva)


cropped_raw = crop_trailing_zeros(eyeData)

#transform MNE-struct to pandas and change from volts to degrees (x,y) and area (pupil)
eye_df = raw2df(cropped_raw)


# Define parameters such as pupil diameter
tv=(eye_df.index.to_numpy()*1/meg_refreshrate)*1000
dia = eye_df['pupil'].copy().to_numpy()

#What unit is diameter in?

#Preprocessing steps
isvalid1 = remove_invalid_samples(eye_df,tv,screensize_pix=screensize_pix)
isvalid2 = madspeedfilter(tv, dia, is_valid=isvalid1)
isvalid3 = mad_deviation(tv, dia, isvalid2)
eyes_preproc_meg = eye_df.copy()
eyes_preproc_meg['x'] = remove_invalid_detrend(eyes_preproc_meg['x'].to_numpy(),isvalid3,True)
eyes_preproc_meg['x_deg'] = [pix_to_deg(i,screensize_pix=screensize_pix,screenwidth_cm=42,screendistance_cm=75) for i in eyes_preproc_meg['x']]
eyes_preproc_meg['y'] = remove_invalid_detrend(eyes_preproc_meg['y'].to_numpy(),isvalid3,True)
eyes_preproc_meg['y_deg'] = [pix_to_deg(i,screensize_pix=screensize_pix,screenwidth_cm=42,screendistance_cm=75) for i in eyes_preproc_meg['y']]
eyes_preproc_meg['pupil'] = remove_invalid_detrend(eyes_preproc_meg['pupil'].to_numpy(),isvalid3,True)



#Turning data pack into raw type so we can epoch it
info = mne.create_info(ch_names = ['x', 'y'], sfreq = 1200)
rawpreproc = mne.io.RawArray(eyes_preproc_meg.loc[:,['x','y']].to_numpy().T, info, first_samp=0, copy='auto', verbose=None)


#Showing two plots, one with the x y positins on the stimulus screen before processing, and then one after processing with
#the true positions of the stimuli layered on the back
plt.scatter(eye_df['x'], eye_df['y'], alpha=.2)
plt.scatter(eyes_preproc_meg['x'], eyes_preproc_meg['y'])
truePositions = pd.read_csv(os.path.join(modulepath,'stimulus', 'results', f'{subjID}_run1.csv'))
plt.scatter(truePositions['xPos'], truePositions['yPos'], marker='x', color='k')
plt.show()



#Epoching Data

epochs = mne.Epochs(rawpreproc, events, tmin=0, tmax=3, baseline= None)

for i in range(epochs.get_data().shape[0]):
    plt.plot(epochs.times, epochs.get_data()[i,0,:])
plt.show()


# expand this to all trials
ind = epochs.times<=1 # durations[1] # select times within trial duration

cropped_epo = epochs.get_data()[:,:,ind]
for i in range(cropped_epo.shape[0]):
    plt.plot(epochs.times[ind], cropped_epo[i,0,:])
plt.show()

# plot error over time per trial
# TODO: iterate over trials
trial = 0
err = np.sqrt(np.sum((cropped_epo[trial,:,:].T-truePositions.loc[trial,:].to_numpy())**2,axis=1)) # plot euclidian distance as error measure
plt.plot(err)