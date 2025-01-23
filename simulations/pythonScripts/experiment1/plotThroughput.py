#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import json
import scienceplots

if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    plt.rcParams['text.usetex'] = False
    
    results = []
    csvName = sys.argv[1].split("run",1)[1]
    runNumb = csvName.partition("/")[0]
    with open('../../../../paperExperiments/bandwidths/experiment1/run'+ str(runNumb) +'.json') as jsonData:
        d = json.load(jsonData)
        resultsOptimal = []
        for arg in sys.argv[1:]:
            time, data = np.genfromtxt(arg, delimiter=',',skip_header=1).transpose()
            results.append((time, data))
    
        i = 0
        runs = 0
        
        floatD = {}
        for k, v in d.items():
            floatD[float(k)] = float(v)
    
        fig, axes = plt.subplots(figsize=(17, 5))
        for result in results:
            colorNum = 0
            #result.index = np.arange(1, len(result) + 1)
            for expNum in range(len(results)):
                xAxis = result[0]
                yAxis = result[1]
                yAxisOptimal = np.array(list(floatD.values()))
                xAxisOptimal = np.array(list(floatD.keys()))
                axes.plot(xAxis,yAxis/1000000, label="Throughput")
                
                axes.plot(xAxisOptimal, yAxisOptimal, label="Available Bandwidth", linestyle='--', drawstyle="steps-post", color='purple') #'steps-mid', 'steps-pre', 'steps-post', 'steps'
                colorNum += 1
                break
        axes.set_aspect('auto')
        axes.set_ylim([0,150])
        axes.set_xlim([0,300])
        axes.set_xbound(lower=0.0, upper=300)
        axes.grid(True)
        plt.xlabel('Time (s)')
        plt.ylabel('Throughput (Mbps)')
        plt.legend(loc = "upper left")
        plt.title("Throughput")
        plt.tight_layout(rect=[0, 0, 1, 1], pad=1.0)  
        plt.savefig('throughput.pdf')
    

