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
    firstChangeTime = 100
    changeBackTime = 200
    numOfConstClients = 2
    numOfMovingClients = 2
    simSeed = 1
    #queueSizes = [0.2,1,4] #OF AVERAGE BDP AFFECTS INI FILE
    constantClientRtt = 50
    movingClientsRtts = [20, 40, 60, 80, 100, 120, 140, 160, 180, 200] #OF AVERAGE BDP
    random.seed(simSeed)
    for movClientRtt in movingClientsRtts:
        baseRttDict = {}
        bwDict = {}
        folderName = '../../paperExperiments/scenarios/experiment3/'
        Path(folderName).mkdir(parents=True, exist_ok=True)
        fileName = str(movClientRtt) + 'ms'
        with open(folderName + '/' + fileName + '.xml', 'w') as f:
            f.write('<scenario>')
            f.write('\n    <at t="0">')
            currConstantClientInterface = numOfConstClients+1
            for constClientNum in range(numOfConstClients):
                delay = int(constantClientRtt)
                channelDelay = (delay-(0.5*2))/4
                f.write('\n        <set-channel-param src-module="constantClient['+ str(constClientNum) + ']" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n        <set-channel-param src-module="constantRouter1" src-gate="pppg$o['+ str(constClientNum) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
                f.write('\n        <set-channel-param src-module="constantServer['+ str(constClientNum) + ']" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n        <set-channel-param src-module="constantRouter2" src-gate="pppg$o['+ str(constClientNum) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n\n')
                
            for movingClientNum in range(numOfMovingClients):
                delay = int(movClientRtt)
                channelDelay = (delay-(0.5*2))/4
                f.write('\n        <set-channel-param src-module="pathChangeRouter1" src-gate="pppg$o['+ str(movingClientNum) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n        <set-channel-param src-module="pathChangeRouter2" src-gate="pppg$o['+ str(movingClientNum) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
                f.write('\n        <set-channel-param src-module="constantRouter1" src-gate="pppg$o['+ str(currConstantClientInterface) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n        <set-channel-param src-module="constantRouter2" src-gate="pppg$o['+ str(currConstantClientInterface) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
                currConstantClientInterface += 1
                
            for movingClientNum in range(numOfMovingClients):
                delay = int(movClientRtt)
                channelDelay = (delay-(0.5*2))/4
                for i in range(2):
                    f.write('\n        <set-channel-param src-module="pathChangeClient['+ str(movingClientNum) + ']" src-gate="pppg$o['+ str(i) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                    f.write('\n        <set-channel-param src-module="pathChangeServer['+ str(movingClientNum) + ']" src-gate="pppg$o['+ str(i) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
            f.write('\n    </at>')
            #Disconnect old paths, update weights of new paths. This shifts traffic onto constant routers at 100s
            
            f.write('\n    <at t="'+ str(firstChangeTime)+ '">')
            
            clientNum = 0
            for movingClientNum in range(numOfMovingClients):
                delay = int(movClientRtt)
                channelDelay = (delay-(0.5*2))/4
                for j in range(2):
                    weight = 1
                    if(j == 0):
                        weight = 2
                    f.write('\n        <set-channel-param src-module="pathChangeClient['+ str(movingClientNum) + ']" src-gate="pppg$o['+ str(j) + ']" par="weight" value="'+ str(weight) +'"/>')
                    f.write('\n        <set-channel-param src-module="pathChangeServer['+ str(movingClientNum) + ']" src-gate="pppg$o['+ str(j) + ']" par="weight" value="'+ str(weight) +'"/>')
                f.write('\n')
                clientNum += 1
                
            routerNum = 0

            currConstantClientInterface = numOfConstClients+1
            for movingClientNum in range(numOfMovingClients):
                delay = int(movClientRtt)
                channelDelay = (delay-(0.5*2))/4
                f.write('\n        <set-channel-param src-module="pathChangeRouter1" src-gate="pppg$o['+ str(movingClientNum) + ']" par="weight" value="'+ str(2) +'"/>')
                f.write('\n        <set-channel-param src-module="pathChangeRouter2" src-gate="pppg$o['+ str(movingClientNum) + ']" par="weight" value="'+ str(2) +'"/>')
                f.write('\n')
                f.write('\n        <set-channel-param src-module="constantRouter1" src-gate="pppg$o['+ str(currConstantClientInterface) + ']" par="weight" value="'+ str(1) +'"/>')
                f.write('\n        <set-channel-param src-module="constantRouter2" src-gate="pppg$o['+ str(currConstantClientInterface) + ']" par="weight" value="'+ str(1) +'"/>')
                f.write('\n')
                currConstantClientInterface += 1
            f.write('\n    </at>')
            
            #SECOND CHANGE - REVERT WEIGHTS BACK
            f.write('\n    <at t="'+ str(changeBackTime)+ '">')
            
            clientNum = 0
            for movingClientNum in range(numOfMovingClients):
                delay = int(movClientRtt)
                channelDelay = (delay-(0.5*2))/4
                for j in range(2):
                    weight = 2
                    if(j == 0):
                        weight = 1
                    f.write('\n        <set-channel-param src-module="pathChangeClient['+ str(movingClientNum) + ']" src-gate="pppg$o['+ str(j) + ']" par="weight" value="'+ str(weight) +'"/>')
                    f.write('\n        <set-channel-param src-module="pathChangeServer['+ str(movingClientNum) + ']" src-gate="pppg$o['+ str(j) + ']" par="weight" value="'+ str(weight) +'"/>')
                f.write('\n')
                clientNum += 1
                
            routerNum = 0

            currConstantClientInterface = numOfConstClients+1
            for movingClientNum in range(numOfMovingClients):
                delay = int(movClientRtt)
                channelDelay = (delay-(0.5*2))/4
                f.write('\n        <set-channel-param src-module="pathChangeRouter1" src-gate="pppg$o['+ str(movingClientNum) + ']" par="weight" value="'+ str(1) +'"/>')
                f.write('\n        <set-channel-param src-module="pathChangeRouter2" src-gate="pppg$o['+ str(movingClientNum) + ']" par="weight" value="'+ str(1) +'"/>')
                f.write('\n')
                f.write('\n        <set-channel-param src-module="constantRouter1" src-gate="pppg$o['+ str(currConstantClientInterface) + ']" par="weight" value="'+ str(2) +'"/>')
                f.write('\n        <set-channel-param src-module="constantRouter2" src-gate="pppg$o['+ str(currConstantClientInterface) + ']" par="weight" value="'+ str(2) +'"/>')
                f.write('\n')
                currConstantClientInterface += 1
            f.write('\n    </at>')
            
            f.write('\n</scenario>')

