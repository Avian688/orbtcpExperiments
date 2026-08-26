#!/usr/bin/env python

# Generates a path change scenario XML file given sender->receiver base propagation delays (ms)
# generatePathChangeScenario delayNum1 delayNum2... delayNumX
# This will generate X flows for use in the scenario manager and add periodic
# hard reconfigurations on the parking-lot bottleneck links.
# 

import sys
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
    numOfRibFlows = 3
    simSeed = 1
    handoverEvery = 15
    minHandoverMs = 45
    maxHandoverMs = 120
    bottleneckDelayMs = 0
    bottleneckDataRate = "100Mbps"
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
                # The final router allocates gate 0 to spineServer and gate 1
                # to the final rib server; intermediate routers use gate 0.
                ribServerRouterGate = 1 if ribClientNum == numOfRibFlows - 1 else 0
                f.write('\n        <set-channel-param src-module="router[' + str(ribClientNum+1) + ']" src-gate="pppg$o[' + str(ribServerRouterGate) + ']" par="delay" value="'+ str(channelDelay) +'ms"/>')
                f.write('\n')
          
            f.write('\n    </at>')

            # Hard reconfiguration on every router-router bottleneck every 15s.
            # The ini files run each RTT case for RTT*2000 seconds, i.e.
            # 2*RTT_ms seconds.
            simLength = int(clientRtt) * 2
            t = handoverEvery
            while t <= simLength:
                handoverMs = random.randint(minHandoverMs, maxHandoverMs)
                reconnectT = t + (handoverMs / 1000.0)

                f.write('\n    <at t="' + str(t) + '">')
                for linkNum in range(numOfRibFlows):
                    leftRouter = 'router[' + str(linkNum) + ']'
                    rightRouter = 'router[' + str(linkNum + 1) + ']'
                    leftGate = 2 if linkNum == 0 else 3
                    rightGate = 2
                    f.write('\n        <disconnect src-module="' + leftRouter + '" src-gate="pppg$o[' + str(leftGate) + ']"/>')
                    f.write('\n        <disconnect src-module="' + rightRouter + '" src-gate="pppg$o[' + str(rightGate) + ']"/>')
                    f.write('\n        <crash module="' + leftRouter + '.ppp[' + str(leftGate) + ']"/>')
                    f.write('\n        <crash module="' + rightRouter + '.ppp[' + str(rightGate) + ']"/>')
                f.write('\n    </at>')

                f.write('\n    <at t="' + str(reconnectT) + '">')
                for linkNum in range(numOfRibFlows):
                    leftRouter = 'router[' + str(linkNum) + ']'
                    rightRouter = 'router[' + str(linkNum + 1) + ']'
                    leftGate = 2 if linkNum == 0 else 3
                    rightGate = 2
                    f.write('\n        <connect src-module="' + leftRouter + '" src-gate="pppg$o[' + str(leftGate) + ']"')
                    f.write('\n                 dest-module="' + rightRouter + '" dest-gate="pppg$i[' + str(rightGate) + ']"')
                    f.write('\n                 channel-type="ned.DatarateChannel">')
                    f.write('\n                 <param name="datarate" value="' + str(bottleneckDataRate) + '" />')
                    f.write('\n                 <param name="delay" value="' + str(bottleneckDelayMs) + 'ms" />')
                    f.write('\n        </connect>')
                    f.write('\n        <connect src-module="' + rightRouter + '" src-gate="pppg$o[' + str(rightGate) + ']"')
                    f.write('\n                 dest-module="' + leftRouter + '" dest-gate="pppg$i[' + str(leftGate) + ']"')
                    f.write('\n                 channel-type="ned.DatarateChannel">')
                    f.write('\n                 <param name="datarate" value="' + str(bottleneckDataRate) + '" />')
                    f.write('\n                 <param name="delay" value="' + str(bottleneckDelayMs) + 'ms" />')
                    f.write('\n        </connect>')
                    f.write('\n        <start module="' + leftRouter + '.ppp[' + str(leftGate) + ']"/>')
                    f.write('\n        <start module="' + rightRouter + '.ppp[' + str(rightGate) + ']"/>')
                f.write('\n        <update module="configurator" />')
                f.write('\n    </at>')

                t += handoverEvery
            
            f.write('\n</scenario>')
