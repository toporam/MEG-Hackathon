import pandas as pd
import numpy as np
from psychopy import visual, event, core,parallel
from datetime import datetime
import os
import time

########## PARAMETERS ##########

participant = '999'
run = 1
runDur = 300 # s

ismeg = 0
isfullscreen = 1
iseyetracking = 0 # recuquires L.T.'s eyetracking script
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

fname_data = f'{curr_path}/results/S{participant.zfill(2)}_MovingDot_run{run}_{t}'


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



photorect_white = visual.Rect(win=win,width = 5,height=10,fillColor='white',pos=(-wWidth/factor,wHeight/factor))
photorect_black = visual.Rect(win=win,width = 5,height=10,fillColor='black',pos=(-wWidth/factor,wHeight/factor))

isiArr = np.random.randint(-refreshrate,refreshrate,100)
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
                df = pd.DataFrame(posXY[:frames+1,:], columns = ['xPos','yPos'])
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
# update radius using cartesian coordinates
dotX, dotY = 0,0
dotSpeeds = np.array([100,120,150])/refreshrate

motDirs = [30,60,120,150,45,135,0,90] *2
motDirs = np.array(motDirs)
motDirs[len(motDirs)//2:] *=-1
motDirs = motDirs[:len(motDirs)-2]


fixation.pos = (dotX,dotY)
condTimes = np.array([5,3,4,2,3,1,3,2,4,1]*20)

ind = np.where(np.cumsum(condTimes)>runDur)[0][0]
condTimes = condTimes[:ind+1]
condTimesCum = np.cumsum(condTimes)
frames = 0 
c_ = 0
i = np.random.randint(0, len(motDirs))
d = np.random.randint(0, len(dotSpeeds))

posXY = np.zeros([runDur * refreshrate,2])
posXY[frames,:] = [dotX,dotY]

init = time.time()
refr_rate = win.getActualFrameRate()
print('refresh rate', refr_rate)
init_c = init

def updateXY(dotX,dotY,motDirs,dotSpeeds,i,d):

    tmpX = dotX + np.cos(motDirs[i]*(np.pi/180))*dotSpeeds[d]
    tmpY = dotY + np.sin(motDirs[i]*(np.pi/180))*dotSpeeds[d]

    if (tmpX > .8*(-wWidth/factor) and tmpX < .8*(wWidth/factor)):
        dotX += np.cos(motDirs[i]*(np.pi/180))*dotSpeeds[d]
        
    else:
        tmpX = dotX + np.cos(-motDirs[i]*(np.pi/180))*dotSpeeds[d]
        outside = True
        
        while outside:
            
            if tmpX > .8*(-wWidth/factor) and tmpX < .8*(wWidth/factor):
                dotX += np.cos(-motDirs[i]*(np.pi/180))*dotSpeeds[d]
                outside = False
            else:
                i = np.random.randint(0, len(motDirs))
                tmpX = dotX + np.cos(motDirs[i]*(np.pi/180))*dotSpeeds[d]
                if tmpX > .8*(-wWidth/factor) and tmpX < .8*(wWidth/factor):
                    outside = False
                    dotX += np.cos(-motDirs[i]*(np.pi/180))*dotSpeeds[d]
            

    
    if tmpY > .8*(-wHeight/factor) and tmpY < .8*(wHeight/factor):
        dotY += np.sin(motDirs[i]*(np.pi/180))*dotSpeeds[d]
    else:
        tmpY = dotY + np.sin(-motDirs[i]*(np.pi/180))*dotSpeeds[d]
        outside = True
        
        while outside:
            
            if tmpY > .8*(-wHeight/factor) and tmpY < .8*(wHeight/factor):
                dotY += np.sin(-motDirs[i]*(np.pi/180))*dotSpeeds[d]
                outside = False
            else:
                i = np.random.randint(0, len(motDirs))
                tmpY = dotY + np.cos(motDirs[i]*(np.pi/180))*dotSpeeds[d]
                if tmpY > .8*(-wHeight/factor) and tmpY < .8*(wHeight/factor):
                    outside = False
                    dotY +=np.sin(motDirs[i]*(np.pi/180))*dotSpeeds[d]
    
    return dotX, dotY

for pp in range(len(condTimes)): 

    i = np.random.randint(0, len(motDirs))
    d = np.random.randint(0, len(dotSpeeds))
    
    # loop over all flips
    if iseyetracking:
        eyetracker.send_message(el_tracker,pp)

    draw_stim(win,fixation,photorect_white,trigger_code=0, port = port)
    once = True
    while time.time()-init <= condTimesCum[pp]:
        if once:
            print(pp, time.time()-init)
            once = False

        dotX, dotY = updateXY(dotX, dotY,motDirs,dotSpeeds,i,d)
        fixation.pos = (dotX, dotY)

        last_flip = draw_stim(win,fixation,photorect_black,trigger_code=0, port = port)
        pressed=event.getKeys(keyList=response_keys, modifiers=False, timeStamped=False) 
        
        if pressed:
            if pressed == ['q']:
                print('user quit experiment')
                df = pd.DataFrame(posXY[:frames+1,:], columns = ['xPos','yPos'])
                df.to_csv(f"{fname_data}_quit.csv",index=False)
                if iseyetracking:
                    eyetracker.exit(el_tracker,et_fname,results_folder=f'{curr_path}/results/')
                win.close()
                core.quit()

        frames +=1
        posXY[frames,:] = [dotX,dotY]

    if ismeg: 
        trigger(port=port,code=0)

    


# save data
df = pd.DataFrame(posXY, columns = ['xPos','yPos'])
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
