#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import json

if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    plt.rcParams['text.usetex'] = False
    
    results = []
    csvName = sys.argv[1].split("run",1)[1]
    runNumb = csvName.partition("/")[0]
    with open('../../../../../../paperExperiments/baseRtts/experiment1/run'+ str(runNumb) +'.json') as jsonData:
        d = json.load(jsonData)
        resultsOptimal = []
        for arg in sys.argv[1:]:
            time, data = np.genfromtxt(arg, delimiter=',').transpose()
            results.append((time, data))
    
        i = 0
        runs = 0
        
        floatD = {}
        for k, v in d.items():
            floatD[float(k)] = float(v)
    
        fig, axes = plt.subplots(figsize=(25,12))
        for result in results:
            colorNum = 0
            #result.index = np.arange(1, len(result) + 1)
            for expNum in range(len(results)):
                xAxis = result[0]
                yAxis = result[1]
                yAxisOptimal = np.array(list(floatD.values()))
                xAxisOptimal = np.array(list(floatD.keys()))
                axes.plot(xAxis,yAxis*1000, drawstyle='steps-post', label="RTT")
                axes.plot(xAxisOptimal, yAxisOptimal, label="Base RTT", linestyle='--', drawstyle="steps-post", color='purple') #'steps-mid', 'steps-pre', 'steps-post', 'steps'
                colorNum += 1
                break
        axes.set_aspect('auto')
        axes.set_xlim([0,300])
        axes.grid(True)
        plt.xlabel('Time (s)')
        plt.ylabel('RTT (ms)')
        plt.legend(loc = "upper left")
        plt.title("RTT")
        plt.tight_layout(rect=[0, 0, 1, 1], pad=1.0)  
        plt.savefig('rtt.pdf')
    

