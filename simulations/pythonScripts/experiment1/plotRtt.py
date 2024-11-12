#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import json
import scienceplots

def parse_if_number(s):
    try: return float(s)
    except: return True if s=="true" else False if s=="false" else s if s else None

def parse_ndarray(s):
    return np.fromstring(s, sep=' ') if s else None
    
def getResults(file):
    resultsFile = pd.read_csv(file, converters = {
    'attrvalue': parse_if_number,
    'binedges': parse_ndarray,
    'binvalues': parse_ndarray,
    'vectime': parse_ndarray,
    'vecvalue': parse_ndarray})
    vectors = resultsFile[resultsFile.type=='vector']
    vec = vectors[vectors.name == 'rtt:vector']
    return vec;

if __name__ == "__main__":
    plt.style.use('science')
    pd.set_option('display.max_rows', None)
    plt.rcParams['text.usetex'] = False
    
    results = []
    protocols = ["Cubic", "Orbtcp", "Bbr"]
    runNames = ["Run", "LossRun"]
    
    csvName = sys.argv[1].split("Run",1)[1]
    runNumb = csvName[:-4]
    with open('../../../../../../../paperExperiments/baseRtts/experiment1/run'+ str(runNumb) +'.json') as jsonData:
        d = json.load(jsonData)
        resultsOptimal = []
        for arg in sys.argv[1:]:
            results.append(getResults(arg))
    
        i = 0
        runs = 0
        
        floatD = {}
        for k, v in d.items():
            floatD[float(k)] = float(v)
    
        fig, axes = plt.subplots(figsize=(25,12))
        for result in results:
            colorNum = 0
            #result.index = np.arange(1, len(result) + 1)
            for expNum in range(len(result.vecvalue.to_numpy())):
                xAxis = result.vectime.to_numpy()[expNum]
                if(len(xAxis) > 1):
                    yAxis = result.vecvalue.to_numpy()[expNum]
                    yAxisOptimal = np.array(list(floatD.values()))
                    xAxisOptimal = np.array(list(floatD.keys()))
                    axes.plot(xAxis,yAxis*1000, drawstyle='steps-post', linewidth=1, label="RTT")
                    axes.plot(xAxisOptimal, yAxisOptimal, linewidth=1.5, label="Base RTT", drawstyle="steps-post") #'steps-mid', 'steps-pre', 'steps-post', 'steps'
                    colorNum += 1
                    break
        axes.set_aspect('auto')
        axes.set_xlim([0,300])
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        plt.xlabel('Time (s)', fontsize=28)
        plt.ylabel('RTT (ms)', fontsize=28)
        plt.legend(loc = "upper right")
        plt.title("RTT", fontsize=35)
        plt.savefig('rtt.png')
    

