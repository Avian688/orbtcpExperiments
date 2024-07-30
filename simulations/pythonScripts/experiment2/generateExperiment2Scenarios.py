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
    numOfRuns = 50
    currentRtt = 75 #ms
    currentBw = 75 #Mb
    currentPer = 0
    currentInterval = 15
    simLength = 300 #s
    simSeed = 1999
    for i in range(numOfRuns):
        random.seed(simSeed + i)
        folderName = '../../scenarios/experiment2/'
        Path(folderName).mkdir(parents=True, exist_ok=True)
        fileName = 'lossRun' + str(i+1)
        with open(folderName + '/' +  fileName + '.xml', 'w') as f:
            f.write('<scenario>')
            f.write('\n    <at t="0">')
            clientNum = 0
            channelDelay = (currentRtt-(0.5*2))/4
            f.write('\n        <set-channel-param src-module="client[0]" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
            f.write('\n        <set-channel-param src-module="router1" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
            f.write('\n')
            f.write('\n        <set-channel-param src-module="server[0]" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>') 
            f.write('\n        <set-channel-param src-module="router2" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
            f.write('\n')
            f.write('\n        <set-channel-param src-module="router1" src-gate="pppg$o[1]" par="datarate" value="'+ str(currentBw) +'Mbps"/>')
            f.write('\n        <set-channel-param src-module="router2" src-gate="pppg$o[1]" par="datarate" value="'+ str(currentBw) +'Mbps"/>')
            f.write('\n    </at>')
            while(currentInterval < simLength):
                f.write('\n    <at t="' + str(currentInterval) + '">')  
                currentRtt = random.randint(5,100) #ms
                currentBw = random.randint(50,100) #Mbps
                currentPer = random.uniform(0,0.01) #PER
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
                currentInterval += 15
            f.write('\n</scenario>')
        currentInterval = 10
        currentRtt = 110
        currentBw = 50
