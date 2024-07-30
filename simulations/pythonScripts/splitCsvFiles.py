#!/usr/bin/env python

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import os
import subprocess
import re
import shutil

def parse_if_number(s):
    try: return float(s)
    except: return True if s=="true" else False if s=="false" else s if s else None

def parse_ndarray(s):
    return np.fromstring(s, sep=' ') if s else None
    
def getResults(file, vecname):
    resultsFile = pd.read_csv(file, converters = {
    'attrvalue': parse_if_number,
    'binedges': parse_ndarray,
    'binvalues': parse_ndarray,
    'vectime': parse_ndarray,
    'vecvalue': parse_ndarray})
    vectors = resultsFile[resultsFile.type=='vector']
    vec = vectors[vectors.name == vecname + ':vector']
    return vec;

if __name__ == "__main__":
    measurements = ["rtt", "cwnd", "ReceiverSideThroughput", "bandwidth"]
    for arg in sys.argv[1:]:
        folderLoc =  '../paperExperiments/'+ arg +'/results/'
        for file in os.listdir(folderLoc):
            if(file.endswith(".csv")):
                f = os.path.join(folderLoc, file)
                fileName = str(Path(folderLoc + file).stem)
                initDir = '../paperExperiments/'+ arg +'/results/' + fileName + "/"
                print(initDir)
                if os.path.exists(initDir):
                    shutil.rmtree(initDir)
                os.makedirs(initDir)
                for m in measurements:
                    result = getResults(folderLoc + file, m)
                    for mod in range(len(result.vecvalue.to_numpy())):
                        yAxis = result.vecvalue.to_numpy()[mod] #VALUE
                        xAxis = result.vectime.to_numpy()[mod] #TIME
                        modName = result.module.to_numpy()[mod] #TIME
                        modName = re.sub('[!@#$.\-\[\]]', '', modName)
                        if(len(yAxis) > 2):
                            npXAxis = np.array(xAxis)
                            npYAxis = np.array(yAxis)
                            df = pd.DataFrame({"time" : xAxis, "value" : yAxis})
                            dir = initDir + modName + "/"
                            if not(os.path.exists(dir)):
                                os.makedirs(dir)
                            df.to_csv(initDir + modName + "/" + m + ".csv", index=False)   
    

