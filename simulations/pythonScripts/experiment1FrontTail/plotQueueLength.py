#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import re

if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    plt.rcParams['text.usetex'] = False
    
    results = []
    for arg in sys.argv[1:]:
        time, data = np.genfromtxt(arg, delimiter=',',skip_header=1).transpose()
        results.append((time, data))
    i = 0
    
    plt.figure(figsize=(17, 5))
    for result in results:
        colorNum = 0
        # queueName = "singledumbbell.router1.ppp["
        # lastQueue = 0
        # moduleList = result.module.to_numpy()
        # extractedList = [s for s in moduleList if queueName in s]
        # for exWord in extractedList:
        #     pppNumb = re.search(r"\[([A-Za-z0-9_]+)\]", exWord)
        #     if(int(pppNumb.group(1)) > lastQueue):
        #         lastQueue = int(pppNumb.group(1))
        # numpyIndex = 0
        # for mod in result.module.to_numpy():
        #     if(mod == "singledumbbell.router1.ppp[" + str(lastQueue) + "]"+".queue"):
        #         break
        #     numpyIndex = numpyIndex + 1
            
        #print(results.vecvalue)
        plt.plot(result[0],result[1], drawstyle='steps-post', label="Queue Length")
        colorNum += 1
        
        axes = plt.gca()
        axes.grid(True)
                #axes.set_xlim([5, 5.2])
        #axes.set_ylim([0,150])
        plt.xlabel('Time (s)')
        plt.ylabel('Queue Length (pkts)')
        plt.legend(loc = "upper left")
        plt.title("Queue Length")
        #plt.xticks((np.arange(0, result["Goodput"].idxmax(), step=250)))
        plt.tight_layout(rect=[0, 0, 1, 1], pad=1.0) 
        plt.savefig('queueLength.pdf')
        i += 1
    

