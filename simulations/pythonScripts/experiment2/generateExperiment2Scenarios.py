#!/usr/bin/env python

# Generates a scenario XML file given sender->receiver base propagation delays (ms)
# generateRttChangeScenario delayChangeNum delayNum1 delayNum2... delayNumX
# This will generate X flows for the use in the scenario manager
# Aiden Valentine

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import json

def int_to_word(num):
    d = { 0 : 'zero', 1 : 'one', 2 : 'two', 3 : 'three', 4 : 'four', 5 : 'five',
          6 : 'six', 7 : 'seven', 8 : 'eight', 9 : 'nine', 10 : 'ten',
          11 : 'eleven', 12 : 'twelve', 13 : 'thirteen', 14 : 'fourteen',
          15 : 'fifteen', 16 : 'sixteen', 17 : 'seventeen', 18 : 'eighteen',
          19 : 'nineteen', 20 : 'twenty',
          30 : 'thirty', 40 : 'forty', 50 : 'fifty', 60 : 'sixty',
          70 : 'seventy', 80 : 'eighty', 90 : 'ninety' }
    k = 1000
    m = k * 1000
    b = m * 1000
    t = b * 1000
    assert(0 <= num)
    if (num < 20):
        return d[num]
    if (num < 100):
        if num % 10 == 0: return d[num]
        else: return d[num // 10 * 10] + d[num % 10]
    if (num > 100): 
        raise AssertionError('num is too large: %s' % str(num))
           
if __name__ == "__main__":
    numOfClients = 1
    minBw = 50 #Mb
    maxBw = 100 #Mb
    minRtt = 5
    maxRtt = 100
    numOfRuns = 50
    simLength = 300 #s
    simSeed = 1
    intervalLength = 15
    currentBw = 0
    currentRtt = 0 
    for i in range(numOfRuns):
        baseRttDict = {}
        bwDict = {}
        currentBw = 75 #Mb
        currentRtt = 75 #ms
        currentInterval = 0
        random.seed(simSeed + i)
        folderName = '../../paperExperiments/scenarios/experiment2/'
        folderBaseRttsName = '../../paperExperiments/baseRtts/experiment2/'
        folderBwsName = '../../paperExperiments/bandwidths/experiment2/'
        Path(folderName).mkdir(parents=True, exist_ok=True)
        Path(folderBaseRttsName).mkdir(parents=True, exist_ok=True)
        Path(folderBwsName).mkdir(parents=True, exist_ok=True)
        fileName = 'run' + str(i+1)
        with open(folderName + '/' + fileName + '.xml', 'w') as f:
            f.write('<scenario>')
            clientNum = 0
            channelDelay = (currentRtt-(0.5*2))/4
            while(currentInterval <= simLength):
                f.write('\n    <at t="' + str(currentInterval) + '">')  
                currentBw = random.randint(minBw,maxBw) #Mbps
                currentRtt = random.randint(minRtt,maxRtt) #ms
                currentPer = round(random.uniform(0,0.01), 4) #PER 
                channelDelay = (currentRtt-(0.5*2))/4
                f.write('\n        <set-channel-param src-module="client[0]" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n        <set-channel-param src-module="router1" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
                f.write('\n        <set-channel-param src-module="server[0]" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>') 
                f.write('\n        <set-channel-param src-module="router2" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
                f.write('\n        <set-channel-param src-module="router1" src-gate="pppg$o[1]" par="datarate" value="'+ str(currentBw) +'Mbps"/>')
                f.write('\n        <set-channel-param src-module="router2" src-gate="pppg$o[1]" par="datarate" value="'+ str(currentBw) +'Mbps"/>')
                f.write('\n        <set-channel-param src-module="router1" src-gate="pppg$o[1]" par="per" value="'+ str(currentPer) +'"/>')
                f.write('\n    </at>')
                baseRttDict[currentInterval] = currentRtt
                bwDict[currentInterval] = currentBw
                currentInterval += intervalLength
            f.write('\n</scenario>')
            
        rttDictObj = json.dumps(baseRttDict, indent=len(baseRttDict))
        with open(folderBaseRttsName + fileName + ".json", "w") as o:
            o.write(rttDictObj)
            
        bwDictObj = json.dumps(bwDict, indent=len(bwDict))
        with open(folderBwsName + fileName + ".json", "w") as p:
            p.write(bwDictObj)
