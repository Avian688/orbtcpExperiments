#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import scienceplots
import re

if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    plt.rcParams['text.usetex'] = False
    results = []
    plotTitle = ""
    for arg in sys.argv[1:]:
        match = re.search(r'([a-zA-Z_]+\[\d+\])', arg)
        module_name = match.group(1) if match else ""
        if(plotTitle == ""):
            plotTitle = module_name
        else:
            plotTitle = plotTitle + "_" + module_name
        time, data = np.genfromtxt(arg, delimiter=',',skip_header=1).transpose()
        results.append((time, data))
        
    i = 0
    plt.figure(figsize=(17, 5))
    for result in results:
        colorNum = 0
        plt.plot(result[0],((result[1])/1448), drawstyle='steps-post', label="CWND")
        colorNum += 1
        
    axes = plt.gca()
    axes.grid(True)
    plt.xlabel('Time (s)')
    plt.ylabel('CWND (MSS)')
    plt.legend(loc = "upper left")
    plt.title("CWND-" + plotTitle)
    plt.tight_layout(rect=[0, 0, 1, 1], pad=1.0) 
    plt.savefig('cwnd.pdf')
    i += 1
    

