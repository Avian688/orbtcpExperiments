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
    for arg in sys.argv[1:]:
        time, data = np.genfromtxt(arg, delimiter=',').transpose()
        results.append((time, data))

    i = 0
    runs = 0
    
    fig, axes = plt.subplots(figsize=(25,12))
    for result in results:
        colorNum = 0
        for expNum in range(len(results)):
            xAxis = result[0]
            yAxis = result[1]
            axes.plot(xAxis,yAxis*1000, drawstyle='steps-post', label="Tau")
            colorNum += 1
            break
    axes.set_aspect('auto')
    axes.grid(True)
    plt.xlabel('Time (s)')
    plt.ylabel('Tau')
    plt.legend(loc = "upper left")
    plt.title("Tau")
    plt.tight_layout(rect=[0, 0, 1, 1], pad=1.0)  
    plt.savefig('tau.pdf')
    

