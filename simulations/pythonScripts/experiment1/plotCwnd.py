#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
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
    vec = vectors[vectors.name == 'cwnd:vector']
    return vec;

if __name__ == "__main__":
    plt.style.use('science')
    pd.set_option('display.max_rows', None)
    plt.rcParams['text.usetex'] = False
    
    results = []
    for arg in sys.argv[1:]:
        results.append(getResults(arg))
    i = 0
    plt.figure(figsize=(25,12))
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    for result in results:
        colorNum = 0
        #result.index = np.arange(1, len(result) + 1)
        for expNum in range(len(result.vecvalue.to_numpy())):
            yAxis = result.vecvalue.to_numpy()[expNum]
            #print(results.vecvalue)
            plt.plot(result.vectime.to_numpy()[expNum],yAxis
            , drawstyle='steps-post', linewidth=1)
            colorNum += 1
        
        axes = plt.gca()
        #axes.set_xlim([0, 40])
        #axes.set_ylim([0,150])
        plt.xlabel('Time (s)', fontsize=28)
        plt.ylabel('cwnd (bytes)', fontsize=28)
        plt.legend(loc = "upper right")
        plt.title("CWND", fontsize=35)
        #plt.xticks((np.arange(0, result["Goodput"].idxmax(), step=250)))
        plt.savefig('cwnd.png')
        i += 1
    

