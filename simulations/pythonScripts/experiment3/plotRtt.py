#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import json
import re

if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    plt.rcParams['text.usetex'] = False
    
    results = []
    plotTitle = ""
    csvName = sys.argv[1].split("run",1)[1]
    runNumb = csvName.partition("/")[0]
    for arg in sys.argv[1:]:
        match = re.search(r'([a-zA-Z_]+\[\d+\])', arg)
        module_name = match.group(1) if match else ""
        if(plotTitle == ""):
            plotTitle = module_name
        else:
            plotTitle = plotTitle + "_" + module_name
        time, data = np.genfromtxt(arg, delimiter=',').transpose()
        results.append((time, data))

    i = 0
    runs = 0
    
    fig, axes = plt.subplots(figsize=(17, 5))
    for result in results:
        colorNum = 0
        for expNum in range(len(results)):
            xAxis = result[0]
            yAxis = result[1]
            axes.plot(xAxis,yAxis*1000, drawstyle='steps-post', label="RTT")
            colorNum += 1
            break
    axes.set_aspect('auto')
    axes.set_xlim([0,300])
    axes.grid(True)
    plt.xlabel('Time (s)')
    plt.ylabel('RTT (ms)')
    plt.legend(loc = "upper left")
    plt.title("RTT-" + plotTitle)
    plt.tight_layout(rect=[0, 0, 1, 1], pad=1.0)  
    plt.savefig('rtt.pdf')
    

