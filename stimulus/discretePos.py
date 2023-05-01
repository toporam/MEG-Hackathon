import pandas as pd
import numpy as np
from psychopy import visual, event, core,parallel
from datetime import datetime
import os


########## PARAMETERS ##########

participant = '999'
run = 1
nTrials = 100
stim_duration = 2

ismeg = 0
isfullscreen = 1
iseyetracking = 0
refreshrate = 60

ismacos = 1 # With Retina, the the screen has a “virtual” size that’s double the actual physical size and PsychoPy handles this by reporting the physical size after window creation (in win.size)
response_keys = ['1','2','3','4','q', 'Q']
background_col = [100, 100, 100] # rgb 255 space

# current date and time, for saving
now = datetime.now()
t = now.strftime("%m%d%Y_%H%M%S")

# setting paths
curr_path = os.path.abspath(os.path.dirname(__file__)) 
if not os.path.exists(curr_path+'/results'):
    os.makedirs(curr_path+'/results')

fname_data = f'{curr_path}/results/S{participant.zfill(2)}_run{run}_{t}'


########## HELPER FUNCTIONS ##########

def setup_window(background_color = background_col, color_space = 'rgb255', isfullscreen = 0, ismeg = ismeg):
    win = visual.Window(color=background_color,colorSpace=color_space,units='pix',checkTiming=True,fullscr=isfullscreen)
    return win 

def draw_stim(win,stim,photorect_white,trigger_code=100, port = []):
    stim.draw()
    photorect_white.draw()
    if ismeg:
        win.callOnFlip(trigger,port = port,code=trigger_code)
    return win.flip()

def setup_triggers():
    port = parallel.ParallelPort(address=0x0378)
    port.setData(0)
    return port

def trigger(port,code):
    port.setData(int(code))

if iseyetracking:
    import eyetracker 
    fname = f'{participant}R{str(run)}'
    et_fname = eyetracker.make_filename(fname=fname)
    # mon = eyetracker.setup_monitor(monitorwidth=screen_width,viewing_distance=view_dist,widthpix=1027,heightpix=768)
    el_tracker,win = eyetracker.connect(fname=et_fname,isfullscreen=isfullscreen,background_col=background_col)
    eyetracker.do_setup(el_tracker)
    # eyetracker.calib(win,el_tracker,fix_size=deg_to_pix(1,win,screen_width,view_dist))
else:
    win = setup_window(background_color = background_col, color_space = 'rgb255', isfullscreen = isfullscreen, ismeg = ismeg)

wWidth,wHeight= win.size

if ismacos:
    factor = 4
else:
    factor = 2 


def definePos(nTrials, wWidth,wHeight, factor):

    ''' use numpy's meshgrid to define a uniform sampling of the stimulus screen '''

    dim = int(np.ceil(np.sqrt(nTrials)))
    nx, ny = (dim, dim)
    x = np.linspace(.8*(-wWidth/factor), .8*(wWidth/factor), nx)
    y = np.linspace(.8*(-wHeight/factor), .8*(wHeight/factor), ny)
    xv, yv = np.meshgrid(x, y)
    posArr =  np.reshape(np.concatenate((xv.flatten(),yv.flatten()),axis=0), (2,len(xv.flatten()))).T

    if nTrials != (dim**2):
        print(f"original n trials = {nTrials} was changed to {dim**2} to ensure uniform sampling")
    
    rng = np.random.default_rng()
    i = rng.permuted(np.arange(len(posArr)))

    '''
    # plot grid
    import matplotlib.pyplot as plt
    fig,ax = plt.subplots()
    ax.plot(xv, yv, marker='o', color='k', linestyle='none')
    ax.plot(posArr[:,0], posArr[:,1], marker='o', color='r', alpha=.5, linestyle='none')
    plt.show(block=False)
    '''

    return posArr[i,:]


# if already defined, use existing stimulus files. Otherwise create a new sampling

stim_path = os.path.join(curr_path,'stim')
if isfullscreen:
    fname_stim = f'{curr_path}/stim/{nTrials}trials_{stim_duration}dur_FullScreen'
else:
    fname_stim = f'{curr_path}/stim/{nTrials}trials_{stim_duration}dur_notFullScreen'

if os.path.exists(os.path.join(stim_path,fname_stim+'.csv')):
    posArr = pd.read_csv(os.path.join(stim_path,fname_stim + '.csv')).to_numpy()
    isiArr = pd.read_csv(os.path.join(stim_path,fname_stim + '_isi.csv')).to_numpy().flatten()
else:
    posArr = definePos(nTrials, wWidth,wHeight, factor)
    isiArr = np.random.randint(-refreshrate,refreshrate,len(posArr))

    df_posArr = pd.DataFrame(posArr, columns = ['xPos','yPos'])
    df_posArr.to_csv(f'{fname_stim}.csv',index=False)

    df_isiArr = pd.DataFrame(isiArr)
    df_isiArr.to_csv(f'{fname_stim}_isi.csv',index=False)

print(f"\n\n\nrun length is: {np.cumsum(isiArr/refreshrate+2)[-1]}\n\n\n")


photorect_white = visual.Rect(win=win,width = 5,height=10,fillColor='white',pos=(-wWidth/factor,wHeight/factor))
photorect_black = visual.Rect(win=win,width = 5,height=10,fillColor='black',pos=(-wWidth/factor,wHeight/factor))


# setup triggers
if ismeg:
    port = setup_triggers()
else:
    port = []

      
def draw_text(text,win):
    text.draw()
    photorect_black.draw()
    win.flip()


def instruction_screen(keylist,text):
    while 1:
        draw_text(visual.TextStim(win,text),win)
        pressed=event.getKeys(keyList=keylist, modifiers=False, timeStamped=False) 
        if pressed:
            if pressed == ['q']:
                print('user quit experiment')
                df = pd.DataFrame(posArr, columns = ['xPos','yPos'])
                df.to_csv(f"{fname_data}_quit.csv",index=False)
                if iseyetracking:
                    eyetracker.exit(el_tracker,et_fname,results_folder=f'{curr_path}/results/')
                win.close()
                core.quit()
            else:
                event.clearEvents()
                break

####### MAIN ########

instruction_screen(['c','q'],'Run ' +str(run)+ ': Head localization' + '\n\n\nPlease close your eyes and rest for a minute.\n\n\n[start the recording and hit c to continue]')
instruction_screen(response_keys+['q'],f"Follow the dot.\n\n\n[Ready to go? Press button to start!]")

for _ in range(100):
    photorect_black.draw()
    last_flip = win.flip()

# loop over trials

fixation  = visual.Circle(win,size=15,fillColor='black')

win.mouseVisible = False

for pp in range(np.shape(posArr)[0]): 
    fixation.pos = tuple(posArr[pp,:])
    # loop over all flips
    if iseyetracking:
        eyetracker.send_message(el_tracker,pp)

    draw_stim(win,fixation,photorect_white,trigger_code=pp+1, port = port)
    for t in range(int(stim_duration*refreshrate)-1 + isiArr[pp]):
        last_flip = draw_stim(win,fixation,photorect_black,trigger_code=0, port = port)
        pressed=event.getKeys(keyList=response_keys, modifiers=False, timeStamped=False) 
    
        if pressed:
            if pressed == ['q']:
                print('user quit experiment')
                df = pd.DataFrame(posArr, columns = ['xPos','yPos'])
                df.to_csv(f"{fname_data}_quit.csv",index=False)
                if iseyetracking:
                    eyetracker.exit(el_tracker,et_fname,results_folder=f'{curr_path}/results/')
                win.close()
                core.quit()
    
    if ismeg: 
        trigger(port=port,code=0)


# save data
df = pd.DataFrame(posArr, columns = ['xPos','yPos'])
df.to_csv(f"{fname_data}.csv",index=False)


if iseyetracking:
    eyetracker.exit(el_tracker,et_fname,results_folder=f'{curr_path}/results/')

# close
text = visual.TextStim(win,"End of the run.\n")
draw_text(text,win)
core.wait(3)

instruction_screen(['c','q'],'Running head localization. \n\n\nPlease close your eyes and rest for a minute.\n\n\n[hit c to close]')

win.mouseVisible = True
win.close()
