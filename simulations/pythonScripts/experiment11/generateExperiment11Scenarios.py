#!/usr/bin/env python

# Generates scenario XML files for experiment 11 where all flows have the same RTT
# This will generate batches for 5, 10 and 20 flows for use in the scenario manager
# Adds hard handovers on the bottleneck every 15s:
#   disconnect + crash, then reconnect after random 45-120ms,
#   start PPP modules, and update configurator.
# Reconnect uses the same bottleneck link characteristics as before.

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
    simSeed = 1
    clientRtt = 50
    batchSizes = [5,10,20]
    random.seed(simSeed)

    handoverEvery = 15
    minHandoverMs = 45
    maxHandoverMs = 120
    simLength = 250

    # These should match your experiment 11 bottleneck settings
    bottleneckDelayMs = 0.5
    bottleneckDataRate = "200Mbps"

    for numOfClients in batchSizes:
        folderName = '../../paperExperiments/scenarios/experiment11/' + str(numOfClients) + 'flows'
        Path(folderName).mkdir(parents=True, exist_ok=True)

        fileName = str(clientRtt) + 'ms'

        with open(folderName + '/' + fileName + '.xml', 'w') as f:
            f.write('<scenario>')

            # Initial link delay setup only (topology is already connected by NED)
            f.write('\n    <at t="0">')
            currClientInterface = numOfClients+1
            for clientNum in range(numOfClients):
                delay = int(clientRtt)
                    
                channelDelay = (delay-(0.5*2))/4
                f.write('\n        <set-channel-param src-module="client['+ str(clientNum) + ']" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n        <set-channel-param src-module="router1" src-gate="pppg$o['+ str(clientNum) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
                f.write('\n        <set-channel-param src-module="server['+ str(clientNum) + ']" src-gate="pppg$o[0]" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n        <set-channel-param src-module="router2" src-gate="pppg$o['+ str(clientNum) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
          
            f.write('\n    </at>')

            # Hard handovers on bottleneck every 15s.
            # Bottleneck interface on router1/router2 is ppp[numOfClients] because:
            # client links consume ppp[0..numOfClients-1], bottleneck is connected afterwards.
            bottleneckIf = numOfClients
            t = handoverEvery
            while t <= simLength:
                handoverMs = random.randint(minHandoverMs, maxHandoverMs)
                reconnectT = t + (handoverMs / 1000.0)

                # Disconnect and crash bottleneck PPPs
                f.write('\n    <at t="' + str(t) + '">')
                f.write('\n        <disconnect src-module="router1" src-gate="pppg$o[' + str(bottleneckIf) + ']"/>')
                f.write('\n        <disconnect src-module="router2" src-gate="pppg$o[' + str(bottleneckIf) + ']"/>')
                f.write('\n        <crash module="router1.ppp[' + str(bottleneckIf) + ']"/>')
                f.write('\n        <crash module="router2.ppp[' + str(bottleneckIf) + ']"/>')
                f.write('\n    </at>')

                # Reconnect with SAME characteristics as before, then start and update configurator
                f.write('\n    <at t="' + str(reconnectT) + '">')
                f.write('\n        <connect src-module="router1" src-gate="pppg$o[' + str(bottleneckIf) + ']"')
                f.write('\n                 dest-module="router2" dest-gate="pppg$i[' + str(bottleneckIf) + ']"')
                f.write('\n                 channel-type="ned.DatarateChannel">')
                f.write('\n                 <param name="datarate" value="' + str(bottleneckDataRate) + '" />')
                f.write('\n                 <param name="delay" value="' + str(bottleneckDelayMs) + 'ms" />')
                f.write('\n        </connect>')
                f.write('\n        <connect src-module="router2" src-gate="pppg$o[' + str(bottleneckIf) + ']"')
                f.write('\n                 dest-module="router1" dest-gate="pppg$i[' + str(bottleneckIf) + ']"')
                f.write('\n                 channel-type="ned.DatarateChannel">')
                f.write('\n                 <param name="datarate" value="' + str(bottleneckDataRate) + '" />')
                f.write('\n                 <param name="delay" value="' + str(bottleneckDelayMs) + 'ms" />')
                f.write('\n        </connect>')
                f.write('\n        <start module="router1.ppp[' + str(bottleneckIf) + ']"/>')
                f.write('\n        <start module="router2.ppp[' + str(bottleneckIf) + ']"/>')
                f.write('\n        <update module="configurator" />')
                f.write('\n    </at>')

                t += handoverEvery
            
            f.write('\n</scenario>')