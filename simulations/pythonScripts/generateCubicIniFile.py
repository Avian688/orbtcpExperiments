#!/usr/bin/env python

# Generates a INI file given the OrbTCP flavour folder. INI file will be filled using the scenarios folder
# generateIniFile orbtcp ... orbTcpFlavourN
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
    for arg in sys.argv[1:]:
        flavour = "Tcp" + arg[0].upper() + arg[1:]
        fileName =  '../'+ arg +'/omnetpp.ini'
        print('\nGenerating ini files for ' + arg + '...')
        with open(fileName, 'w') as f:
            f.write('[General]' + '\n')
            f.write('\n' + 'network = simplenetwork')
            f.write('\n' + 'sim-time-limit = 200s')
            f.write('\n' + 'record-eventlog=false')
            f.write('\n' + 'cmdenv-express-mode = true')
            f.write('\n' + 'cmdenv-redirect-output = false')
            f.write('\n' + 'cmdenv-output-file = dctcpLog.txt')
            f.write('\n' + '**.client*.tcp.conn-8.cmdenv-log-level = detail')
            f.write('\n' + 'cmdenv-log-prefix = %t | %m |\n\n')
            f.write('\n' + 'cmdenv-event-banners = false')
            f.write('\n' + '**.cmdenv-log-level = off\n')
            f.write('\n' + '**.**.tcp.conn-*.cwnd:vector.vector-recording = true')
            f.write('\n' + '**.**.tcp.conn-*.rtt:vector.vector-recording = true')
            f.write('\n' + '**.**.tcp.conn-*.lossRecovery:vector.vector-recording = true')
            f.write('\n' + '**.**.tcp.conn-*.srtt:vector.vector-recording = true')
            f.write('\n' + '**.**.tcp.conn-*.queueingDelay:vector.vector-recording = true')
            f.write('\n' + '**.**.tcp.conn-*.ssthresh:vector.vector-recording = true')
            f.write('\n' + '**.**.queue.queueLength:vector.vector-recording = true')
            f.write('\n' + '**.**.queue.queueingTime:vector.vector-recording = true')
            f.write('\n' + '**.**.ReceiverSideThroughput:vector.vector-recording = true')
            f.write('\n' + '**.**.persistentQueueingDelay:vector.vector-recording = true')
            f.write('\n' + '**.scalar-recording=false')
            f.write('\n' + '**.vector-recording=false')
            f.write('\n' + '**.bin-recording=false\n')
            f.write('\n' + '**.server[*].app[*].*.thrMeasurementInterval = 0.3s')
            f.write('\n' + '**.server[*].app[*].*.thrMeasurementBandwidth = 125000000\n')
            f.write('\n' + '**.tcp.typename = "PacedTcp"')
            f.write('\n' + '**.tcp.tcpAlgorithmClass = "TcpCubic"')
            f.write('\n' + '**.tcp.advertisedWindow = 200000000')
            f.write('\n' + '**.tcp.windowScalingSupport = true')
            f.write('\n' + '**.tcp.windowScalingFactor = -1')
            f.write('\n' + '**.tcp.increasedIWEnabled = true')
            f.write('\n' + '**.tcp.delayedAcksEnabled = false')
            f.write('\n' + '**.tcp.ecnWillingness = false')
            f.write('\n' + '**.tcp.nagleEnabled = true')
            f.write('\n' + '**.tcp.stopOperationTimeout = 4000s')
            f.write('\n' + '**.tcp.mss = 1460')
            f.write('\n' + '**.tcp.sackSupport = true')
            f.write('\n' + '**.tcp.initialSsthresh = 0\n')
            f.write('\n' + '**.client[*].numApps = 1')
            f.write('\n' + '**.client[*].app[*].typename  = "TcpSessionApp"')
            f.write('\n' + '*.client[*].app[0].tClose = -1s')
            f.write('\n' + '*.client[*].app[0].sendBytes = 2GB')
            f.write('\n' + '*.client[*].app[0].dataTransferMode = "bytecount"')
            f.write('\n' + '*.client[*].app[0].statistic-recording = true\n')
            f.write('\n' + '**.server[*].numApps = 1')
            f.write('\n' + '**.server[*].app[*].typename  = "TcpSinkApp"')
            f.write('\n' + '**.server[*].app[*].serverThreadModuleType = "orbtcp.applications.tcpapp.TcpThroughputSinkAppThread"\n')
            f.write('\n' + '**.ppp[*].queue.typename = "DropTailQueue"\n')
            
            scenarioDirectoriesList = ["oneFlows", "twoFlows", "fiveFlows", "tenFlows", "twentyfiveFlows"]
            for dirName in scenarioDirectoriesList: 
                dir = [f for f in os.listdir('../scenarios/'+ dirName +'/.')]
                for xmlFile in dir:
                    fileName = os.path.basename(xmlFile)[:-6]
                    flowsListString = fileName.split('-')
                    flowsList = [ int(x) for x in flowsListString ]
                    maxFlowSize = 0
                    configFlowNames = ''
                    for i in flowsList:
                        if i > maxFlowSize:
                            maxFlowSize = i
                        configFlowNames = configFlowNames + str(i) + 'ms'
                    queueLength = int(((maxFlowSize/1000)*18750000)/1460)
                    configName = ''
                    if(len(flowsList) == 1):
                        configName = (int_to_word(len(flowsList)) + 'Flow')
                    else:
                        configName = (int_to_word(len(flowsList)) + 'Flows')
                    configName = (configName + configFlowNames)
                    configName = configName[0].upper() + configName[1:]
                    f.write('\n' + '[Config ' + configName + ']')       
                    f.write('\n' + 'extends = General\n')
                    f.write('\n' + '**.numberOfFlows = ' + str(len(flowsList)) + '\n')  
                    f.write('\n' + '*.client[0].app[0].connectAddress = "server[0]"')
                    f.write('\n' + '*.client[0].app[0].tOpen = 0s')
                    f.write('\n' + '*.client[0].app[0].tSend = 0s\n')
                    f.write('\n' + '*.client[*].app[0].connectAddress = "server[" + string(parentIndex()) +"]"')
                    f.write('\n' + '*.client[*].app[0].tOpen = 0s')
                    f.write('\n' + '*.client[*].app[0].tSend = uniform(0s,100s)\n')
                    f.write('\n' + '**.ppp[*].queue.packetCapacity = ' + str(queueLength) + '\n')
                    f.write('\n' + '**.tcp.initialSsthresh = ' + str((queueLength*2)*1400) + '\n')
                    f.write('\n' + '*.scenarioManager.script = xmldoc("../scenarios/'+ dirName +'/' + fileName + 'ms.xml")\n')
    print('\nINI files generated!')            
                
                    
            
            
            
            

