import mne
import pandas as pd 
import numpy as np
import math, mne
from scipy import stats
from scipy.signal import butter,filtfilt
from scipy.interpolate import interp1d
global screensize_pix
screensize_pix=[1024, 768]
eye_channel = ['UADC009-2104', 'UADC010-2104', 'UADC013-2104']


#Read in eyetracking Data
data = mne.io.read_raw_fif('eyetracker/data/S01_discretePositions_raw.fif', preload=True)
eyeData = data.copy().pick_channels(eye_channel)

## Helper functions
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

# def expand_gap(tv,is_valid):
#     min_gap_width                                   = 75
#     max_gap_width                                   = 2000
#     pad_back                                        = 100
#     pad_forward                                     = 150
#     valid_t                                         = tv[is_valid]
#     valid_idx                                       = np.where(is_valid)[0]
#     gaps                                            = np.diff(valid_t)

#     # Convert to samples 
#     for i in min_gap_width, max_gap_width, pad_back, pad_forward:
#         i/=et_refreshrate

#     needs_padding                                   = [x and y for x,y in zip(gaps>min_gap_width,gaps<max_gap_width)]
#     gap_start_t                                     = valid_t[np.pad(needs_padding,(0,1),constant_values=False)]
#     gap_end_t                                       = valid_t[np.pad(needs_padding,(1,0),constant_values=False)]

#     remove_idx = []
#     for i_start,i_end in zip(gap_start_t,gap_end_t):
#         # when the gap is super large, it's most likely a recording artifact (and not an eyeblink), so we should clean around it more
#         if i_end -i_start > 500:
#             pb                                      = pad_back * 2
#             pf                                      = pad_forward * 2
#         else:
#             pb                                      = pad_back
#             pf                                      = pad_forward
#         remove_idx.extend(np.where([x and y for x,y in zip(valid_t>(i_start-pb),valid_t<(i_end+pf))])[0])
#     remove_idx                                      = np.unique(remove_idx)

#     if remove_idx.any():
#         is_valid[valid_idx[remove_idx]]             = False
#     return is_valid


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



raw_df = raw2df(eyeData)
print(raw_df)










