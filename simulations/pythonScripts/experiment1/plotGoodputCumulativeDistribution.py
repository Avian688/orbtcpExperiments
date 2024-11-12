#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import random
import scienceplots
import subprocess

def parse_if_number(s):
    try: return float(s)
    except: return True if s=="true" else False if s=="false" else s if s else None

def parse_ndarray(s):
    return np.fromstring(s, sep=' ') if s else None
    
def getResults(file, vecname):
    resultsFile = pd.read_csv(file, converters = {
    'attrvalue': parse_if_number,
    'binedges': parse_ndarray,
    'binvalues': parse_ndarray,
    'vectime': parse_ndarray,
    'vecvalue': parse_ndarray})
    vectors = resultsFile[resultsFile.type=='vector']
    vec = vectors[vectors.name == vecname + ':vector']
    return vec;

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
    
    for protocol in protocols:
        for run in runs:
            filePath = '../../../../paperExperiments/experiment1/results/'+ protocol.title() + 'Run' + str(run) + '.csv'
            if os.path.exists(filePath):
                #BANDWIDTH
                bwResults = getResults(filePath, "bandwidth")
                optimalBandwidthY = []
                optimalBandwidthX = []
                optimalBandwidthVar = 0
                for mod in range(len(bwResults.vecvalue.to_numpy())):
                    bwYAxis = bwResults.vecvalue.to_numpy()[mod] #VALUE
                    bwXAxis = bwResults.vectime.to_numpy()[mod] #TIME
                    modName = bwResults.module.to_numpy()[mod] #TIME
                    variance = np.var(bwResults.vecvalue.to_numpy()[mod])
                    if(variance > optimalBandwidthVar):
                        optimalBandwidthVar = variance
                        optimalBandwidthY = bwYAxis
                        optimalBandwidthX =  bwXAxis
                optimalBandwidthMean = sum(optimalBandwidthY) / len(optimalBandwidthY)
                
                #GOODPUT
                gpResult = getResults(filePath, "goodput")
                gpYAxis = gpResult.vecvalue.to_numpy()[0] #VALUE
                rttData.append([protocol, run, gpYAxis.mean()*0.000001, optimalBandwidthMean*0.000001])
                
    #LossData      
    for protocol in protocols:
        for run in runs:
            filePath = '../../../../../../../paperExperiments/experiment2/results/'+ protocol.title() + 'LossRun' + str(run) + '.csv'
            if os.path.exists(filePath):
                #BANDWIDTH
                bwResults = getResults(filePath, "bandwidth")
                optimalBandwidthY = []
                optimalBandwidthX = []
                optimalBandwidthVar = 0
                for mod in range(len(bwResults.vecvalue.to_numpy())):
                    bwYAxis = bwResults.vecvalue.to_numpy()[mod] #VALUE
                    bwXAxis = bwResults.vectime.to_numpy()[mod] #TIME
                    modName = bwResults.module.to_numpy()[mod] #TIME
                    variance = np.var(bwResults.vecvalue.to_numpy()[mod])
                    if(variance > optimalBandwidthVar):
                        optimalBandwidthVar = variance
                        optimalBandwidthY = bwYAxis
                        optimalBandwidthX =  bwXAxis
                optimalBandwidthMean2 = sum(optimalBandwidthY) / len(optimalBandwidthY)
                
                #GOODPUT
                gpResult2 = getResults(filePath, "goodput")
                gpYAxis2 = gpResult2.vecvalue.to_numpy()[0] #VALUE
                lossData.append([protocol, run, gpYAxis2.mean()*0.000001, optimalBandwidthMean2*0.000001])
    
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
                    

