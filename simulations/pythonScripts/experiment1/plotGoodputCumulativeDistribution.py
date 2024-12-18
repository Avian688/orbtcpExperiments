#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import random
import json
import scienceplots
import subprocess

if __name__ == "__main__":
    plt.style.use('science')
    pd.set_option('display.max_rows', None)
    plt.rcParams['text.usetex'] = False
    
    BINS = 50
    runs = list(range(1,51))
    protocols = ["cubic", "orbtcp"]
    
    # List containing each data point (each run). Values for each datapoint: protocol, run_number, average_goodput, optimal_goodput
    rttData = []
    lossData = []
    
    #NO LOSS DATA 
    for protocol in protocols:
        for run in runs:
            filePath = '../../../../paperExperiments/experiment1/csvs/'+ protocol + '/run' + str(run) + '/singledumbbell.server[0].app[0].thread_9/goodput.csv'
            if os.path.exists(filePath):
                #BANDWIDTH
                
                with open('../../../../paperExperiments/bandwidths/experiment1/run'+ str(run) +'.json') as jsonData:
                    d = json.load(jsonData)
                
                floatD = {}
                for k, v in d.items():
                    floatD[float(k)] = float(v)
                    
                time, data = np.genfromtxt(filePath, dtype=float, delimiter=',',skip_header=1).transpose()
                    
                bwResults = data
                
                optimalBandwidthY = np.array(list(floatD.values()))
                optimalBandwidthX =  np.array(list(floatD.keys()))
                    
                optimalBandwidthMean = sum(optimalBandwidthY) / len(optimalBandwidthY)
                #GOODPUT
                rttData.append([protocol, run, bwResults.mean()*0.000001, optimalBandwidthMean]) #0.000001 = bytes to Mb
    #LOSS DATA 
    for protocol in protocols:
        for run in runs:
            filePath2 = '../../../../paperExperiments/experiment2/csvs/'+ protocol + '/run' + str(run) + '/singledumbbell.server[0].app[0].thread_9/goodput.csv'
            if os.path.exists(filePath):
                 #BANDWIDTH
    
                with open('../../../../paperExperiments/bandwidths/experiment2/run'+ str(run) +'.json') as jsonData:
                     d = json.load(jsonData)
                     
                floatD = {}
                for k, v in d.items():
                    floatD[float(k)] = float(v)
                        
                time2, data2 = np.genfromtxt(filePath2, dtype=float, delimiter=',',skip_header=1).transpose()
                bwResults2 = data2
                
                optimalBandwidthY2 = np.array(list(floatD.values()))
                optimalBandwidthX2 =  np.array(list(floatD.keys()))
                
                optimalBandwidthMean2 = sum(optimalBandwidthY2) / len(optimalBandwidthY2)
                
                #GOODPUT
                lossData.append([protocol, run, bwResults2.mean()*0.000001, optimalBandwidthMean2]) #0.000001 = bytes to Mb           
    
    bw_rtt_data = pd.DataFrame(rttData, columns=['protocol', 'run_number', 'average_goodput', 'optimal_goodput'])
    loss_data = pd.DataFrame(lossData, columns=['protocol', 'run_number', 'average_goodput', 'optimal_goodput'])
    
    colours = {'cubic': '#0C5DA5', 'bbr': '#00B945', 'orbtcp': '#FF9500'}
    
    fig, axes = plt.subplots(nrows=1, ncols=1,figsize=(3,1.5))
    ax = axes
    
    optimals = bw_rtt_data[bw_rtt_data['protocol'] == 'cubic']['optimal_goodput']
    
    values, base = np.histogram(optimals, bins=BINS)
    # evaluate the cumulative
    cumulative = np.cumsum(values)
    # plot the cumulative function
    ax.plot(base[:-1], cumulative/50*100, c='black')
    
    for protocol in protocols:
        avg_goodputs = bw_rtt_data[bw_rtt_data['protocol'] == protocol]['average_goodput']
        values, base = np.histogram(avg_goodputs, bins=BINS)
        # evaluate the cumulative
        cumulative = np.cumsum(values)
        # plot the cumulative function
        ax.plot(base[:-1], cumulative/50*100, label="%s-rtt" % protocol, c=colours[protocol])
    
        avg_goodputs = loss_data[loss_data['protocol'] == protocol]['average_goodput']
        values, base = np.histogram(avg_goodputs, bins=BINS)

        # evaluate the cumulative
        cumulative = np.cumsum(values)
        # plot the cumulative function
        ax.plot(base[:-1], cumulative / 50 * 100, label="%s-loss" % protocol, c=colours[protocol], linestyle='dashed')
    
    ax.set(xlabel="Average Goodput (Mbps)", ylabel="Percentage of Trials (\%)")
    ax.annotate('optimal', xy=(78, 50), xytext=(45, 20), arrowprops=dict(arrowstyle="->", linewidth=0.5))
    
    fig.legend(ncol=3, loc='upper center',bbox_to_anchor=(0.5, 1.19),columnspacing=0.5,handletextpad=0.5, handlelength=1)
    for format in ['pdf']:
        fig.savefig("joined_goodput_cdf.%s" % (format), dpi=720)                
                    

