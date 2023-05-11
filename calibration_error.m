% Lucrezia Liuzzi
% Created 05/05/2023
% Read eyetracking data from UADC MEG channels and compared to expected
% fixation coordinates

% Start fieldtrip to read .fif file
addpath /home/liuzzil2/fieldtrip-20190812/
ft_defaults

datapath =  '/data/liuzzil2/MEG-Hackathon/';
filename =[ datapath, '/eyetracker/data/S04_discretePositions_raw.fif'];
hdr = ft_read_header(filename); % load fif-filename
dat = ft_read_data(filename);

x = dat(strcmp(hdr.label,'UADC009-2104'),:);
y = dat(strcmp(hdr.label,'UADC010-2104'),:);
stimonset  = dat(strcmp(hdr.label,'UADC016-2104'),:);
% Gaze locations on screen, gorund truth
pix = readtable([datapath,'eyetracker/stimulus/stim/121trials_2dur_MEGLAB_FullScreen.csv']);
pix.xPos = pix.xPos + 1024/2;
pix.yPos = 768 - (pix.yPos + 768/2); % vertical axis is flipped

time = (1:length(x) )/hdr.Fs;


% Find triggers from UADC016 channel
[pks,locs]= findpeaks( -stimonset, 'MinPeakDistance',0.1*hdr.Fs, 'MinPeakHeight',1 ) ;
if length(locs) > size(pix,1) % delete extra triggers
    locs = locs(1:size(pix,1));
    pks = pks(1:size(pix,1));
end
figure; plot(time,stimonset)
hold on 
plot(locs/hdr.Fs,-pks,'x'); 
xlabel('time (s)'); ylabel('V'); title('Task triggers, UADC016 channel')

% duration of last event
lastev_duration = 2 + 1/60 *(-33); % hard-coded, 60Hz refresh rate
% Add end of last event
locs(end+1) =  locs(end) + lastev_duration*hdr.Fs;


% Detect blinks from UADC channels voltage < -4.5
blinkind = x < -4.0 | y < -4.0;

blinkind(1:locs(1)-100) = 1;
% padding blinks: 100ms before, 150ms after
indt1 = find(diff(blinkind) > 0 );
indt2 = find(diff(blinkind) < 0 );

bInd = find(blinkind);

% Add padding to blinks: 100ms before and 150ms after 
padding1 = cell(size(indt1));
for k = 1:length(indt1)
    pad1 = (indt1(k) - 0.100*hdr.Fs) : (indt1(k)-1 );
    pad1(pad1 < 0) = [];
    padding1{k} = pad1;
end

padding2 = cell(size(indt2));
for k = 1:length(indt2)
    pad2 =  (indt2(k)+1) : (indt2(k) + 0.150*hdr.Fs);
    padding2{k} = pad2;
end

bInd = [bInd, cell2mat(padding1), cell2mat(padding2)];
bInd = unique(bInd);

figure; plot(time, x)
hold on
plot(time(bInd), x(bInd), '.')
legend('x coordinate voltage','blinks','location','best')
xlabel('time (s)'); ylabel('V'); 
title('eyetracker UADC009 channel with labeled blinks')


% Convert voltage to pixels, based on eyetracking_preprocessing.py from
% nih2mne github (https://github.com/nih-megcore/nih_to_mne)

% def volts_to_pixels(x,y,pupil,minvoltage,maxvoltage,minrange,maxrange,screenbottom,screenleft,screenright,screentop,scaling_factor):
minvoltage=-5; 
maxvoltage=5; 
minrange=-0.2; 
maxrange=1.2;
screenbottom=767; 
screenleft=0; 
screenright=1023; 
screentop=0;
% 78.5 cm distance from screen

S_x                         = ((x-minvoltage)/(maxvoltage-minvoltage))*(maxrange-minrange)+minrange;
S_y                         = ((y-minvoltage)/(maxvoltage-minvoltage))*(maxrange-minrange)+minrange;
Xgaze                       = S_x*(screenright-screenleft+1)+screenleft;
Ygaze                       = S_y*(screenbottom-screentop+1)+screentop;

%% Saccade detection
close all

Xgaze_clean = Xgaze;
Ygaze_clean = Ygaze;
Xgaze_clean(bInd) = NaN;
Ygaze_clean(bInd) = NaN;

figure; 
plot(Xgaze_clean,Ygaze_clean,'.'); hold on
plot(pix.xPos , pix.yPos, 'x')
xlabel('pixels (screen width=1024)')
ylabel('pixels (screen height=768)')
title('Eyegaze positions over all time (no blinks)')
legend('eyegaze','expected fixations','location','best')

vx = diff(Xgaze_clean);
vy = diff(Ygaze_clean);
v = sqrt(vx.^2 + vy.^2);

ax = diff(vx);
ay = diff(vy);
a = sqrt(ax.^2 + ay.^2);

figure; histogram(v)
title('eyegaze velocity')
xlim([0,4]); xlabel('velocity (pixels/s)')

figure; histogram(a)
title('eyegaze acceleration')
xlim([0,3]); xlabel('acceleration (pixels/s^2)')

% threshold for saccade detection (TO DO: compare to 
    % eyelink fixation/saccade detection)
sacc = v(1:end-1) > 1.5 | a > 1.1;

Xgaze_clean(sacc) = NaN;
Ygaze_clean(sacc) = NaN;

% 78.5 cm distance from screen
figure; 
plot(Xgaze_clean,Ygaze_clean,'.'); hold on
plot(pix.xPos, pix.yPos, 'x')
xlabel('pixels (screen width=1024)')
ylabel('pixels (screen height=768)')
title('Fixation positions over all time (no blinks, no saccades)')
legend('fixations','expected fixations','location','best')


%% Manually delete outliers
Xgaze_clean(Ygaze_clean < 70) = nan;
Ygaze_clean(Ygaze_clean < 70) = nan;

%% Find calibration error for each fixation
err = cell(length(locs)-1,1);
errm = zeros(length(locs)-1,2);
XYk = cell(length(locs)-1,1);
% figure;
for k = 1:(length(locs)-1)
    xk = Xgaze_clean(locs(k):(locs(k+1)+0.1*hdr.Fs));
    yk = Ygaze_clean(locs(k):(locs(k+1)+0.1*hdr.Fs));
    
     
    xk = xk(~isnan(xk))';
    yk = yk(~isnan(yk))'; 
   
    % find jumps in gaze position to get fixations (TO DO: compare to 
    % eyelink fixation/saccade detection)
    fixTrans = find(( abs(diff(xk)) >20) | (abs(diff(yk)) ) >20 );
%     subplot(11,11,k); plot(diff(xk)); hold on; plot(diff(yk));
    fixs = cell(1,length(fixTrans)+1);
    fixtime = zeros(1,length(fixTrans)+1);
    if length(fixTrans) >=1   
        fixs{1} = [xk(1:fixTrans(1)),  yk(1:fixTrans(1))];
        fixtime(1) = length(fixs{1});
        for ii = 1:length(fixTrans)-1
            fixs{ii+1} = [xk(fixTrans(ii)+1:fixTrans(ii+1)) , ...
                yk(fixTrans(ii)+1:fixTrans(ii+1))];
            fixtime(ii+1) = length(fixs{ii+1});
        end
        fixs{end} = [xk(fixTrans(length(fixTrans))+1:end) , ...
            yk(fixTrans(length(fixTrans))+1:end)];  
        fixtime(end) = length(fixs{end});
    else
        fixs{1} = [xk, yk];
        fixtime(1) = length(fixs{1});
    end
  
    % find distance of fixations to last fixation of previous trial
    d = zeros(1,length(fixs));
    if k > 1
        for ii = 1:length(fixs)
           d(ii) =sqrt( sum((mean(fixs{ii},1) -  mean(fix0,1)).^2) );
        end
        fix0 = fixs{end};
       % if find distance <10 pixel, delete fixation (participant still looking at previous location)
        fixs(d<10) = [];
        fixtime(d<10) = [];
    else
        fix0 = fixs{end};
    end
    % eliminate fixations shorter than 100ms
    fixs(fixtime<hdr.Fs*0.1) = [];
    fixtime(fixtime<hdr.Fs*0.1) = [];
    
    % find longest fixation in trial
    [~,m] = max(fixtime);
    
    XYk{k} = cell2mat(fixs');

    err{k} = zeros(length(fixs),2);
    for ii = 1:length(fixs)
        err{k}(ii,:) = [  mean( fixs{ii}(:,1) ) - (pix.xPos(k) ) , ...
              mean(fixs{ii}(:,2)) - (pix.yPos(k) ) ];
    end
    
    if ~isempty(m)
        errm(k,:) = [  mean( fixs{m}(:,1) ) - (pix.xPos(k) ) , ...
                  mean(fixs{m}(:,2)) - (pix.yPos(k) ) ];
    end
end

%% Plot fixation error
XY = cell2mat(XYk);
figure; hold all
scatter(XY(:,1), XY(:,2),10,[ 0   0.4470  0.7410])
plot(pix.xPos , pix.yPos, 'xr')

for k = 1:(length(locs)-1)

    plot(pix.xPos(k) +[0,errm(k,1)],pix.yPos(k)  +[0,errm(k,2)],'k','linewidth',2)
% % plot distance between expected fixation and all fixations during trial
    %     for ii = 1:size(err{k},1)
%         plot(pix.xPos(k) +[0,err{k}(ii,1)],pix.yPos(k)  +[0,err{k}(ii,2)],'-','color',[0.7 0.7 0.7],'linewidth',0.5)
%     end
end

xlabel('pixels (screen width=1024)')
ylabel('pixels (screen height=768)')
title('Fixation calibration error')
legend('fixation points','expected fixations','error vector','location','best')


