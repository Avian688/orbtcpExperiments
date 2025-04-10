import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.transforms import offset_copy
import scienceplots
plt.style.use('science')
import os, sys
from matplotlib.ticker import ScalarFormatter
import numpy as np

plt.rcParams['text.usetex'] = False

PROTOCOLS = ['cubic', 'bbr', 'orbtcp', 'bbr3']
BWS = [100]
DELAYS = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200]
QMULTS = [0.2,1,4]
QMULTDICT = {0.2 : "smallbuffer", 1 : "mediumbuffer", 4 : "largebuffer" }
RUNS = [1, 2, 3, 4, 5]

LINEWIDTH = 0.30
ELINEWIDTH = 0.75
CAPTHICK = ELINEWIDTH
CAPSIZE= 2

def plot_points_rtt(ax, df, data, error,  marker, label):
   if not df.empty:
      xvals = df.index
      yvals = df[data]
      yerr  = df[error]
      markers, caps, bars = ax.errorbar(
         xvals, yvals,
         yerr=yerr,
         marker=marker,
         linewidth=LINEWIDTH,
         elinewidth=ELINEWIDTH,
         capsize=CAPSIZE,
         capthick=CAPTHICK,
         label=label
      )
      [bar.set_alpha(0.5) for bar in bars]
      [cap.set_alpha(0.5) for cap in caps]

for mult in QMULTS:
   data = []
   for protocol in PROTOCOLS:
     for bw in BWS:
        for delay in DELAYS:
           start_time = 1.5*delay
           end_time = 2*delay
           keep_last_seconds = int(0.25*delay)

           goodput_ratios_20 = []
           goodput_ratios_total = []

           for run in RUNS:
               PATH = '../../../paperExperiments/experiment4/csvs/'+ protocol + '/' + QMULTDICT.get(mult) + '/' + str(delay) + 'ms/run' + str(run) + '/' #add ../ 
               receiver1GoodputPath = PATH + 'singledumbbell.server[0].app[0]/goodput.csv'
               receiver2GoodputPath = PATH + 'singledumbbell.server[1].app[0]/goodput.csv'
               if os.path.exists(receiver1GoodputPath) and os.path.exists(receiver2GoodputPath):
                  receiver1_total = pd.read_csv(receiver1GoodputPath).reset_index(drop=True)
                  receiver2_total = pd.read_csv(receiver2GoodputPath).reset_index(drop=True)

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

                  total = receiver1_total.join(receiver2_total, how='inner', lsuffix='1', rsuffix='2')[['goodput1', 'goodput2']]
                  partial = receiver1.join(receiver2, how='inner', lsuffix='1', rsuffix='2')[['goodput1', 'goodput2']]

                  total = total.dropna()
                  partial = partial.dropna()

                  goodput_ratios_20.append(partial.min(axis=1)/partial.max(axis=1))
                  goodput_ratios_total.append(total.min(axis=1)/total.max(axis=1))
               else:
                  avg_goodput = None
                  std_goodput = None
                  jain_goodput_20 = None
                  jain_goodput_total = None
                  print("Files %s not found." % receiver1GoodputPath)

           if len(goodput_ratios_20) > 0 and len(goodput_ratios_total) > 0:
              goodput_ratios_20 = np.concatenate(goodput_ratios_20, axis=0)
              goodput_ratios_total = np.concatenate(goodput_ratios_total, axis=0)

              if len(goodput_ratios_20) > 0 and len(goodput_ratios_total) > 0:
                 data_entry = [protocol, bw, delay, delay/10, mult, goodput_ratios_20.mean(), goodput_ratios_20.std(), goodput_ratios_total.mean(), goodput_ratios_total.std()]
                 data.append(data_entry)

   summary_data = pd.DataFrame(data,
                              columns=['protocol', 'goodput', 'delay', 'delay_ratio','qmult', 'goodput_ratio_20_mean',
                                       'goodput_ratio_20_std', 'goodput_ratio_total_mean', 'goodput_ratio_total_std'])

   cubic_data = summary_data[summary_data['protocol'] == 'cubic'].set_index('delay')
   bbr_data = summary_data[summary_data['protocol'] == 'bbr'].set_index('delay')
   orbtcp_data = summary_data[summary_data['protocol'] == 'orbtcp'].set_index('delay')
   bbr3_data = summary_data[summary_data['protocol'] == 'bbr3'].set_index('delay')


   fig, axes = plt.subplots(nrows=1, ncols=1,figsize=(3,1.2))
   ax = axes

   plot_points_rtt(ax, summary_data[summary_data['protocol'] == 'cubic'].set_index('delay'), 'goodput_ratio_total_mean', 'goodput_ratio_total_std',   'x', 'cubic')
   plot_points_rtt(ax, summary_data[summary_data['protocol'] == 'bbr'].set_index('delay'), 'goodput_ratio_total_mean', 'goodput_ratio_total_std',  '.', 'bbr')
   plot_points_rtt(ax, summary_data[summary_data['protocol'] == 'orbtcp'].set_index('delay'), 'goodput_ratio_total_mean', 'goodput_ratio_total_std',   '^', 'orbtcp')
   plot_points_rtt(ax, summary_data[summary_data['protocol'] == 'bbr3'].set_index('delay'), 'goodput_ratio_total_mean', 'goodput_ratio_total_std',   '_', 'bbr3')

   ax.set(yscale='linear',xlabel='RTT (ms)', ylabel='Goodput Ratio')
   for axis in [ax.xaxis, ax.yaxis]:
       axis.set_major_formatter(ScalarFormatter())


   # Build a 2-row "pyramid" legend
   handles, labels = ax.get_legend_handles_labels()
   # Convert errorbar handles if needed
   line_handles = [h[0] if isinstance(h, tuple) else h for h in handles]
   legend_map   = dict(zip(labels, line_handles))

   # Decide which protocols go top vs. bottom row
   handles_top = [legend_map.get('cubic'), legend_map.get('bbr'), legend_map.get('orbtcp'), legend_map.get('bbr3')]
   labels_top  = ['cubic', 'bbr', 'orbtcp', 'bbr3']


   legend_top = plt.legend(
      handles_top, labels_top,
      ncol=3,
      loc='upper center',
      bbox_to_anchor=(0.5, 1.41),
      columnspacing=1.0,
      handletextpad=0.5,
      labelspacing=0.1,
      borderaxespad=0.0
   )
   plt.gca().add_artist(legend_top)
   plt.savefig(f"goodput_ratio_inter_rtt_{mult}.pdf" , dpi=1080)