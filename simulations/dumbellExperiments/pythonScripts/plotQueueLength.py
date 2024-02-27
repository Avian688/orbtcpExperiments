#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
import re

def parse_if_number(s):
    try: return float(s)
    except: return True if s=="true" else False if s=="false" else s if s else None

def parse_ndarray(s):
    return np.fromstring(s, sep=' ') if s else None

def parse(s):
    return s;
    
def getResults(file):
    resultsFile = pd.read_csv(file, converters = {
    'module' : parse,
    'attrvalue': parse_if_number,
    'binedges': parse_ndarray,
    'binvalues': parse_ndarray,
    'vectime': parse_ndarray,
    'vecvalue': parse_ndarray})
    vectors = resultsFile[resultsFile.type=='vector']
    vec = vectors[vectors.name == 'queueLength:vector']
    return vec;

if __name__ == "__main__":
    results = []
    for arg in sys.argv[1:]:
        results.append(getResults(arg))
    i = 0
    plt.figure(figsize=(25,12))
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    for result in results:
        colorNum = 0
        queueName = "simplenetwork.router1.ppp["
        lastQueue = 0
        moduleList = result.module.to_numpy()
        extractedList = [s for s in moduleList if queueName in s]
        for exWord in extractedList:
            pppNumb = re.search(r"\[([A-Za-z0-9_]+)\]", exWord)
            if(int(pppNumb.group(1)) > lastQueue):
                lastQueue = int(pppNumb.group(1))
        numpyIndex = 0
        for mod in result.module.to_numpy():
            if(mod == "simplenetwork.router1.ppp[" + str(lastQueue) + "]"+".queue"):
                break
            numpyIndex = numpyIndex + 1
            
        yAxis = result.vecvalue.to_numpy()[numpyIndex]
        #print(results.vecvalue)
        plt.plot(result.vectime.to_numpy()[numpyIndex],yAxis
        , drawstyle='steps-post', linewidth=1)
        colorNum += 1
        
        axes = plt.gca()
                #axes.set_xlim([5, 5.2])
        #axes.set_ylim([0,150])
        plt.xlabel('Time (s)', fontsize=28)
        plt.ylabel('Queue Length (packets)', fontsize=28)
        plt.legend(loc = "upper right")
        plt.title("Queue Length", fontsize=35)
        #plt.xticks((np.arange(0, result["Goodput"].idxmax(), step=250)))
        plt.savefig('QueueLength.png')
        i += 1
    

