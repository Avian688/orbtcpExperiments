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
    simLength = 300
    intervalLength = 5
    simSeed = 1
    #queueSizes = [0.2,1,4] #OF AVERAGE BDP AFFECTS INI FILE
    rtts = [50]
    disruptionIntervals = [20,40,60,80,100,120,140,160,180,200]
    random.seed(simSeed)
    for rtt in rtts:
        for disruptionInterval in disruptionIntervals:
            folderName = '../../paperExperiments/scenarios/experiment7/'
            Path(folderName).mkdir(parents=True, exist_ok=True)
            fileName = 'RTT' + str(rtt) + 'ms_Disruption' + str(disruptionInterval) + "ms"
            with open(folderName + '/' + fileName + '.xml', 'w') as f:
                f.write('<scenario>')
                channelDelay = (rtt-(0.5*2))/4
                currentInterval = 0
                while(currentInterval <= simLength):
                    if(currentInterval == 0):
                        f.write('\n    <at t="' + str(currentInterval) + '">')    
                        f.write('\n        <set-channel-param src-module="client[0]" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                        f.write('\n        <set-channel-param src-module="router1" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                        f.write('\n')
                        f.write('\n        <set-channel-param src-module="server[0]" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>') 
                        f.write('\n        <set-channel-param src-module="router2" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                        f.write('\n')
                        f.write('\n        <set-channel-param src-module="router1" src-gate="pppg$o[1]" par="datarate" value="100Mbps"/>')
                        f.write('\n        <set-channel-param src-module="router2" src-gate="pppg$o[1]" par="datarate" value="100Mbps"/>')
                        f.write('\n    </at>')
                    else:
                        f.write('\n    <at t="' + str(currentInterval) + '">') 
                        f.write('\n        <disconnect src-module="router1" src-gate="pppg$o[1]"/>')
                        f.write('\n        <disconnect src-module="router2" src-gate="pppg$o[1]"/>')
                        f.write('\n        <crash module="router1.ppp[1]"/>')   
                        f.write('\n        <crash module="router2.ppp[1]"/>') 
                        #f.write('\n        <update module="configurator" />')
                        f.write('\n    </at>')
                        
                        f.write('\n    <at t="' + str(currentInterval+(disruptionInterval/1000)) + '">')    
                        f.write('\n        <connect src-module="router1" src-gate="pppg$o[1]"')
                        f.write('\n                 dest-module="router2" dest-gate="pppg$i[1]"')
                        f.write('\n                 channel-type="ned.DatarateChannel">')
                        f.write('\n                 <param name="datarate" value="100Mbps" />')
                        f.write('\n                 <param name="delay" value="0.5ms" />')
                        f.write('\n        </connect>')
                        f.write('\n        <connect src-module="router2" src-gate="pppg$o[1]"')
                        f.write('\n                 dest-module="router1" dest-gate="pppg$i[1]"')
                        f.write('\n                 channel-type="ned.DatarateChannel">')
                        f.write('\n                 <param name="datarate" value="100Mbps" />')
                        f.write('\n                 <param name="delay" value="0.5ms" />')
                        f.write('\n        </connect>')
                        f.write('\n        <start module="router1.ppp[1]"/>')   
                        f.write('\n        <start module="router2.ppp[1]"/>')  
                        f.write('\n        <update module="configurator" />')
                        # f.write('\n        <initiate module="client[0].ipv4.routingTable" operation="4"/>')
                        # f.write('\n        <initiate module="router1.ipv4.routingTable" operation="4"/>')
                        f.write('\n    </at>')
                        
                        
                    currentInterval += intervalLength
                f.write('\n</scenario>')
                

