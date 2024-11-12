#!/usr/bin/env python

# Generates a INI file given the congestion control algorithm. INI file will be filled using the scenarios folder
# generateIniFile congestionCongAlg ... congestionCongAlgN
# Aiden Valentine

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import os

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
    #numOfClients = int_to_word(len(sys.argv)-1)
    #folderName = '../scenarios/' + numOfClients + 'Flows'
    queueLength = 340 #Average BDP
    algorithms = ["orbtcp", "bbr", "cubic"]
    for alg in algorithms:
        fileName =  '../../paperExperiments/experiment1/experiment1' + alg + '.ini'
        print('\nGenerating ini files for ' + alg + '...')
        
        if(alg == "cubic"):
            algFlavour = "TcpCubic"
        elif(alg == "bbr"):
            algFlavour = "BbrFlavour"
        else:
            algFlavour = "OrbtcpFlavour"
            
        with open(fileName, 'w') as f:
            f.write('[General]' + '\n')
            f.write('\n' + 'network = singledumbbell')
            f.write('\n' + 'sim-time-limit = 300s')
            f.write('\n' + 'record-eventlog=false')
            f.write('\n' + 'cmdenv-express-mode = true')
            f.write('\n' + 'cmdenv-redirect-output = false')
            f.write('\n' + 'cmdenv-output-file = dctcpLog.txt')
            f.write('\n' + '**.client*.tcp.conn-8.cmdenv-log-level = detail')
            f.write('\n' + 'cmdenv-log-prefix = %t | %m |\n\n')
            f.write('\n' + 'cmdenv-event-banners = false')
            f.write('\n' + '**.cmdenv-log-level = off\n')
            f.write('\n' + '**.**.tcp.conn-*.cwnd:vector.vector-recording = true')
            f.write('\n' + '**.**.tcp.conn-*.U:vector.vector-recording = true')
            f.write('\n' + '**.**.tcp.conn-*.rtt:vector.vector-recording = true')
            f.write('\n' + '**.**.tcp.conn-*.srtt:vector.vector-recording = true') 
            f.write('\n' + '**.**.tcp.conn-*.lossRecovery:vector.vector-recording = true')
            f.write('\n' + '**.**.queue.queueLength:vector.vector-recording = true')
            f.write('\n' + '**.**.goodput:vector.vector-recording = true')
            f.write('\n' + '**.**.throughput:vector.vector-recording = true')
            f.write('\n' + '**.**.bandwidth:vector.vector-recording = true')
            f.write('\n' + '**.**.mbytesInFlight:vector.vector-recording = true')
            f.write('\n' + '**.scalar-recording=false')
            f.write('\n' + '**.vector-recording=false')
            f.write('\n' + '**.bin-recording=false\n')
            f.write('\n' + '**.server[*].app[*].*.thrMeasurementInterval = 1s')
            
            if(algFlavour == "TcpCubic"):
                f.write('\n' + '**.tcp.typename = "TcpPaced"')
                f.write('\n' + '**.tcp.tcpAlgorithmClass = "TcpCubic"')
                f.write('\n' + '**.tcp.advertisedWindow = 200000000')
                f.write('\n' + '**.tcp.windowScalingSupport = true')
                f.write('\n' + '**.tcp.windowScalingFactor = -1')
                f.write('\n' + '**.tcp.increasedIWEnabled = true')
                f.write('\n' + '**.tcp.delayedAcksEnabled = false')
                f.write('\n' + '**.tcp.timestampSupport = true')
                f.write('\n' + '**.tcp.ecnWillingness = false')
                f.write('\n' + '**.tcp.nagleEnabled = true')
                f.write('\n' + '**.tcp.stopOperationTimeout = 4000s')
                f.write('\n' + '**.tcp.mss = 1448')
                f.write('\n' + '**.tcp.sackSupport = true')
                #f.write('\n' + '**.tcp.initialSsthresh = 0\n')
                f.write('\n' + '**.client[*].numApps = 1')
                f.write('\n' + '**.client[*].app[*].typename  = "TcpGoodputSessionApp"')
                f.write('\n' + '*.client[*].app[0].tClose = -1s')
                f.write('\n' + '*.client[*].app[0].sendBytes = 2GB')
                f.write('\n' + '*.client[*].app[0].dataTransferMode = "bytecount"')
                f.write('\n' + '*.client[*].app[0].statistic-recording = true\n')
                f.write('\n' + '**.server[*].numApps = 1')
                f.write('\n' + '**.server[*].app[*].typename  = "TcpSinkApp"')
                f.write('\n' + '**.server[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                f.write('\n' + '**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"\n')
                f.write('\n' + '**.tcp.initialSsthresh = ' + str(400*1448) + '\n')
                
            elif(algFlavour == "BbrFlavour"):
                f.write('\n' + '**.tcp.typename = "Bbr"')
                f.write('\n' + '**.tcp.tcpAlgorithmClass = "BbrFlavour"')
                f.write('\n' + '**.tcp.advertisedWindow = 200000000')
                f.write('\n' + '**.tcp.windowScalingSupport = true')
                f.write('\n' + '**.tcp.windowScalingFactor = -1')
                f.write('\n' + '**.tcp.increasedIWEnabled = true')
                f.write('\n' + '**.tcp.delayedAcksEnabled = false')
                f.write('\n' + '**.tcp.timestampSupport = true')
                f.write('\n' + '**.tcp.ecnWillingness = false')
                f.write('\n' + '**.tcp.nagleEnabled = true')
                f.write('\n' + '**.tcp.stopOperationTimeout = 4000s')
                f.write('\n' + '**.tcp.mss = 1448')
                f.write('\n' + '**.tcp.sackSupport = true')
                f.write('\n' + '**.client[*].numApps = 1')
                f.write('\n' + '**.client[*].app[*].typename  = "TcpGoodputSessionApp"')
                f.write('\n' + '*.client[*].app[0].tClose = -1s')
                f.write('\n' + '*.client[*].app[0].sendBytes = 2GB')
                f.write('\n' + '*.client[*].app[0].dataTransferMode = "bytecount"')
                f.write('\n' + '*.client[*].app[0].statistic-recording = true\n')
                f.write('\n' + '**.server[*].numApps = 1')
                f.write('\n' + '**.server[*].app[*].typename  = "TcpSinkApp"')
                f.write('\n' + '**.server[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                f.write('\n' + '**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"\n')
                f.write('\n' + '**.tcp.initialSsthresh = ' + str(500*1448) + '\n')
            else:
                f.write('\n' + '**.tcp.typename = "Orbtcp"')
                f.write('\n' + '**.tcp.tcpAlgorithmClass = "OrbtcpFlavour"')
                f.write('\n' + '**.tcp.advertisedWindow = 200000000')
                f.write('\n' + '**.tcp.windowScalingSupport = true')
                f.write('\n' + '**.tcp.windowScalingFactor = -1')
                f.write('\n' + '**.tcp.increasedIWEnabled = true')
                f.write('\n' + '**.tcp.delayedAcksEnabled = false')
                f.write('\n' + '**.tcp.timestampSupport = true')
                f.write('\n' + '**.tcp.ecnWillingness = false')
                f.write('\n' + '**.tcp.nagleEnabled = true')
                f.write('\n' + '**.tcp.stopOperationTimeout = 4000s')
                f.write('\n' + '**.tcp.mss = 1448')
                f.write('\n' + '**.tcp.sackSupport = true')
                #f.write('\n' + '**.tcp.initialSsthresh = 0\n')
                
                f.write('\n' + '**.client[*].numApps = 1')
                f.write('\n' + '**.client[*].app[*].typename  = "TcpGoodputSessionApp"')
                f.write('\n' + '*.client[*].app[0].tClose = -1s')
                f.write('\n' + '*.client[*].app[0].sendBytes = 2GB')
                f.write('\n' + '*.client[*].app[0].dataTransferMode = "bytecount"')
                f.write('\n' + '*.client[*].app[0].statistic-recording = true\n')
                f.write('\n' + '**.server[*].numApps = 1')
                f.write('\n' + '**.server[*].app[*].typename  = "TcpSinkApp"')
                f.write('\n' + '**.server[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                f.write('\n' + '**.ppp[*].queue.typename = "IntQueue"\n')
                f.write('\n' + '**.additiveIncreasePercent = 0.05')
                f.write('\n' + '**.eta = 0.95\n')
                f.write('\n' + '**.alpha = ' + str(0.01))
                f.write('\n' + '**.fixedAvgRTTVal = '+ str(0) + '\n')
                f.write('\n' + '**.tcp.initialSsthresh = ' + str(400*1448) + '\n')
                
            dir = [f for f in os.listdir('../../paperExperiments/scenarios/experiment1/.')]
            for xmlFile in dir:
                runNum = int(os.path.basename(xmlFile)[3:-4])                          
                configName = alg.title() + "Run" + str(runNum)
                f.write('\n' + '[Config ' + configName + ']')       
                f.write('\n' + 'extends = General \n')
                f.write('\n' + '**.numberOfFlows = 1 \n')  
                f.write('\n' + '*.client[0].app[0].connectAddress = "server[0]"')
                f.write('\n' + '*.client[0].app[0].tOpen = 0s')
                f.write('\n' + '*.client[0].app[0].tSend = 0s\n')
                f.write('\n' + '**.ppp[*].queue.packetCapacity = ' + str(queueLength) + '\n')
                f.write('\n' + '*.scenarioManager.script = xmldoc("../scenarios/experiment1/run' + str(runNum) + '.xml")\n')
    print('\nINI files generated!')            
                
                    
            
            
            
            


