import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.transforms import offset_copy
import scienceplots
plt.style.use('science')
import os
from matplotlib.ticker import ScalarFormatter
import numpy as np

plt.rcParams['text.usetex'] = False


ROOT_PATH = "../../paperExperiments/experiment1/results/TwoFlows50ms50ms" #home/mihai/mininettestbed/nooffload/results_fairness_intra_rtt_async/fifo" 
PROTOCOLS = ['bbr']#['cubic', 'bbr', 'bbr1']
BWS = [100]
DELAYS = [50]#[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
QMULTS = [1] #[0.2, 1 ,4]
RUNS = [1] #[1, 2, 3, 4, 5]
LOSSES=[0]

def find_all(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result
        
def export_legend(legend, bbox=None, filename="legend.png"):
   fig = legend.figure
   fig.canvas.draw()
   if not bbox:
      bbox = legend.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
   fig.savefig(filename, dpi=1080, bbox_inches=bbox)


for mult in QMULTS:
    data = []
    for protocol in PROTOCOLS:
     for bw in BWS:
        for delay in DELAYS:
            duration = 2*delay
            start_time = 2*delay
            end_time = 3*delay
            keep_last_seconds = int(0.25*delay)
            
            BDP_IN_BYTES = int(bw * (2 ** 20) * 2 * delay * (10 ** -3) / 8)
            BDP_IN_PKTS = BDP_IN_BYTES / 1460
            
            goodput_ratios_20 = []
            goodput_ratios_total = []
            
            count = 0;
            for run in RUNS:
                for throughputFile in find_all("ReceiverSideThroughput.csv", ROOT_PATH):
                    if(count == 0):
                        receiver1_path = throughputFile
                    elif(count == 1):
                        receiver2_path = throughputFile
                    count = count + 1
                  
                    #PATH = ROOT_PATH + '/Dumbell_%smbit_%sms_%spkts_0loss_2flows_22tcpbuf_%s/run%s' % (bw,delay,int(mult * BDP_IN_PKTS),protocol,run)
                    #if os.path.exists(PATH + '/csvs/x1.csv') and os.path.exists(PATH + '/csvs/x2.csv'):
                if(receiver1_path):
                   #receiver1_total = pd.read_csv(PATH + '/csvs/x1.csv').reset_index(drop=True)
                   receiver1_total = pd.read_csv(receiver1_path).reset_index(drop=True)
                   #receiver2_total = pd.read_csv(PATH + '/csvs/x2.csv').reset_index(drop=True)
                   receiver2_total = pd.read_csv(receiver2_path).reset_index(drop=True)
                   
                   receiver1_total['time'] = receiver1_total['time'].apply(lambda x: int(float(x)))
                   receiver2_total['time'] = receiver2_total['time'].apply(lambda x: int(float(x)))
                   
                
                   receiver1_total = receiver1_total[(receiver1_total['time'] > start_time) & (receiver1_total['time'] < end_time)]
                   receiver2_total = receiver2_total[(receiver2_total['time'] > start_time) & (receiver2_total['time'] < end_time)]
                
                   receiver1_total = receiver1_total.drop_duplicates('time')
                   receiver2_total = receiver2_total.drop_duplicates('time')
                   receiver1 = receiver1_total[receiver1_total['time'] >= end_time - keep_last_seconds].reset_index(drop=True)
                   receiver2 = receiver2_total[receiver2_total['time'] >= end_time - keep_last_seconds].reset_index(drop=True)
                
                   receiver1_total = receiver1_total.set_index('time')
                   receiver2_total = receiver2_total.set_index('time')
                
                   receiver1 = receiver1.set_index('time')
                   receiver2 = receiver2.set_index('time')
                   
                   total = receiver1_total.join(receiver2_total, how='inner', lsuffix='1', rsuffix='2')[['value', 'value']]
                   partial = receiver1.join(receiver2, how='inner', lsuffix='1', rsuffix='2')[['value', 'value']]
                   print(partial)
                
                   # total = total.dropna()
                   # partial = partial.dropna()
                
                   goodput_ratios_20.append(partial.min(axis=1)/partial.max(axis=1))
                   goodput_ratios_total.append(total.min(axis=1)/total.max(axis=1))
                else:
                   avg_goodput = None
                   std_goodput = None
                   jain_goodput_20 = None
                   jain_goodput_total = None
                   #print("Folder %s not found." % PATH)
   
            if len(goodput_ratios_20) > 0 and len(goodput_ratios_total) > 0:
               goodput_ratios_20 = np.concatenate(goodput_ratios_20, axis=0)
               goodput_ratios_total = np.concatenate(goodput_ratios_total, axis=0)
   
               if len(goodput_ratios_20) > 0 and len(goodput_ratios_total) > 0:
                  data_entry = [protocol, bw, delay, delay/10, mult, goodput_ratios_20.mean(), goodput_ratios_20.std(), goodput_ratios_total.mean(), goodput_ratios_total.std()]
                  data.append(data_entry)
   
    summary_data = pd.DataFrame(data,
                               columns=['protocol', 'bandwidth', 'delay', 'delay_ratio','qmult', 'goodput_ratio_20_mean',
                                        'goodput_ratio_20_std', 'goodput_ratio_total_mean', 'goodput_ratio_total_std'])
   
    bbr_data = summary_data[summary_data['protocol'] == 'bbr'].set_index('delay')
    cubic_data = summary_data[summary_data['protocol'] == 'cubic'].set_index('delay')
    bbr1_data = summary_data[summary_data['protocol'] == 'bbr1'].set_index('delay')
   
    LINEWIDTH = 0.15
    ELINEWIDTH = 0.75
    CAPTHICK = ELINEWIDTH
    CAPSIZE= 2
   
    fig, axes = plt.subplots(nrows=1, ncols=1,figsize=(3,1.2))
    ax = axes
   
   
   
    markers, caps, bars = ax.errorbar(cubic_data.index*2, cubic_data['goodput_ratio_20_mean'], yerr=cubic_data['goodput_ratio_20_std'],marker='x',linewidth=LINEWIDTH, elinewidth=ELINEWIDTH, capsize=CAPSIZE, capthick=CAPTHICK, label='cubic')
    [bar.set_alpha(0.5) for bar in bars]
    [cap.set_alpha(0.5) for cap in caps]
    markers, caps, bars = ax.errorbar(bbr_data.index*2,bbr_data['goodput_ratio_20_mean'], yerr=bbr_data['goodput_ratio_20_std'],marker='^',linewidth=LINEWIDTH, elinewidth=ELINEWIDTH, capsize=CAPSIZE, capthick=CAPTHICK,label='bbr')
    [bar.set_alpha(0.5) for bar in bars]
    [cap.set_alpha(0.5) for cap in caps]
    markers, caps, bars = ax.errorbar(bbr1_data.index*2,bbr1_data['goodput_ratio_20_mean'], yerr=bbr1_data['goodput_ratio_20_std'],marker='+',linewidth=LINEWIDTH, elinewidth=ELINEWIDTH, capsize=CAPSIZE, capthick=CAPTHICK,label='bbr1')
    [bar.set_alpha(0.5) for bar in bars]
    [cap.set_alpha(0.5) for cap in caps]
   
    ax.set(yscale='linear',xlabel='RTT (ms)', ylabel='Goodput Ratio', ylim=[-0.1,1.1])
    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_major_formatter(ScalarFormatter())
    # ax.legend(loc=4,prop={'size': 6})
    # get handles
    handles, labels = ax.get_legend_handles_labels()
    # remove the errorbars
    handles = [h[0] for h in handles]
   
    legend = fig.legend(handles, labels,ncol=3, loc='upper center',bbox_to_anchor=(0.5, 1.08),columnspacing=0.8,handletextpad=0.5)
    # ax.grid()
   
    for format in ['pdf']:
       plt.savefig('goodput_ratio_async_intra_20_%s.%s' % (mult, format), dpi=1080)
