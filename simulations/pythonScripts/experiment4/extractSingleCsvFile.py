#!/usr/bin/env python

# Generates a single csv file for given experiment name
# generateSingleCsvFile experimentName protocolName runNumber
# Aiden Valentine

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import os
import subprocess
import re

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
    return vectors;

if __name__ == "__main__":
    filePath = ""
    exp = ""
    protocol = ""
    bufferName = ""
    rtt = ""
    run = 0
    argNum = 0
    vectorsToExtract = ["goodput", "rtt", "cwnd", "queueLength", "throughput"]
    extracted = False
    
    for arg in sys.argv[1:]:
        if(argNum == 0):
            filePath = str(arg)
        elif(argNum == 1):
            exp = str(arg)
        elif(argNum == 2):
            protocol = str(arg)
        elif(argNum == 3):
            bufferName = str(arg)
        elif(argNum == 4):
            rtt = str(arg)
        elif(argNum == 5):
            run = int(arg)
        argNum = argNum + 1
    
    rawResults = getResults(filePath)
    for vec in vectorsToExtract:    
        results = rawResults.loc[rawResults['name'] == str(vec)+":vector(removeRepeats)"]
        for mod in range(len(results.vecvalue.to_numpy())):
            if(not results.vecvalue.to_numpy()[mod] is None):
                val = results.vecvalue.to_numpy()[mod] #VALUE
                time = results.vectime.to_numpy()[mod] #TIME
                modName = results.module.to_numpy()[mod]
                if 'thread' in modName:
                    modName = re.sub(r'\.thread_\d+', '', modName)
                modName = re.sub(r'(conn)-\d+', r'\1', modName)
                
                finallist = pd.DataFrame({'time': time, str(vec): val})
                subprocess.Popen("mkdir ../../paperExperiments/" + exp + "/csvs", shell=True).communicate(timeout=10) 
                subprocess.Popen("mkdir ../../paperExperiments/" + exp + "/csvs/" + protocol, shell=True).communicate(timeout=10) 
                subprocess.Popen("mkdir ../../paperExperiments/" + exp + "/csvs/" + protocol + '/' + bufferName, shell=True).communicate(timeout=10) 
                subprocess.Popen("mkdir ../../paperExperiments/" + exp + "/csvs/" + protocol + '/' + bufferName + '/' + rtt + 'ms', shell=True).communicate(timeout=10) 
                subprocess.Popen("mkdir ../../paperExperiments/" + exp + "/csvs/" + protocol + '/' + bufferName + '/' + rtt + 'ms' + '/run'+ str(run), shell=True).communicate(timeout=10)
                subprocess.Popen("mkdir ../../paperExperiments/" + exp + "/csvs/" + protocol + '/' + bufferName + '/' + rtt + 'ms' + '/run'+ str(run) + "/" + str(modName), shell=True).communicate(timeout=10)
                
                
                finallist.to_csv('../../paperExperiments/'+ exp +'/csvs/' + protocol + '/' + bufferName + '/'+ rtt + 'ms' + '/run'+ str(run) + '/' + str(modName) + '/' + vec + '.csv', index=False)
                extracted = True
            else:
                print("\n None data found! Not extracting \n")
                
    if(extracted):
        subprocess.Popen("rm " + filePath, shell=True).communicate(timeout=60)
        subprocess.Popen("rm  ../../paperExperiments/experiment4/results/*.vec", shell=True).communicate(timeout=60)
        subprocess.Popen("rm  ../../paperExperiments/experiment4/results/*.vci", shell=True).communicate(timeout=60)
        subprocess.Popen("rm  ../../paperExperiments/experiment4/results/*.sca", shell=True).communicate(timeout=60)
    
        
    
