#!/usr/bin/env python

# Generates a path change scenario XML file given sender->receiver base propagation delays (ms)
# generatePathChangeScenario delayNum1 delayNum2... delayNumX
# This will generate X flows for the use in the scenario manager which will change path at 10s
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
    numOfRibFlows = 3
    simSeed = 1
    #queueSizes = [0.2,1,4] #OF AVERAGE BDP AFFECTS INI FILE
    clientsRtts = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200] #OF AVERAGE BDP
    random.seed(simSeed)
    for clientRtt in clientsRtts:
        baseRttDict = {}
        bwDict = {}
        folderName = '../../paperExperiments/scenarios/experiment6/'
        Path(folderName).mkdir(parents=True, exist_ok=True)
        fileName = str(clientRtt) + 'ms'
        with open(folderName + '/' + fileName + '.xml', 'w') as f:
            delay = int(clientRtt)      
            channelDelay = (delay)/4

            f.write('<scenario>')
            f.write('\n    <at t="0">')
            currClientInterface = numOfRibFlows+1

            f.write('\n        <set-channel-param src-module="spineClient" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
            f.write('\n        <set-channel-param src-module="router[0]" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')

            f.write('\n        <set-channel-param src-module="spineServer" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
            f.write('\n        <set-channel-param src-module="router[' + str(numOfRibFlows) + ']" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
            f.write('\n')

            for ribClientNum in range(numOfRibFlows):
                f.write('\n        <set-channel-param src-module="ribClient['+ str(ribClientNum) + ']" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n        <set-channel-param src-module="router[' + str(ribClientNum) + ']" src-gate="pppg$o[1]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
                f.write('\n        <set-channel-param src-module="ribServer['+ str(ribClientNum) + ']" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n        <set-channel-param src-module="router[' + str(ribClientNum+1) + ']" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
          
            f.write('\n    </at>')
            
            f.write('\n</scenario>')

