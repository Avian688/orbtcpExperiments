#!/usr/bin/env python

# Generates a INI file given the congestion control algorithm. INI file will be filled using the scenarios folder
# generateIniFile congestionCongAlg ... congestionCongAlgN
# 

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
    simSeed = 1999
    bandwidth = 100
    queueLength = round(((bandwidth*125000)*0.05)/1448) #431 packets
    queueSizes = [1]
    numOfRuns = 5
    numOfConstClients = 2
    numOfMovingClients = 2
    algorithms = ["orbtcp", "bbr", "cubic", "bbr3"]
    for alg in algorithms:
        for qs in queueSizes:
            
            queueIniTitle = ""
            if(qs == 0.2):
                queueIniTitle = "smallbuffer"
            elif(qs == 1):
                queueIniTitle = "mediumbuffer"
            elif(qs == 4):
                queueIniTitle = "largebuffer"
                    
            fileName =  '../../paperExperiments/experiment3/experiment3' + '_' + alg + '_' + queueIniTitle + '.ini'
            print('\nGenerating ini files for ' + alg + '...')
            
            if(alg == "cubic"):
                algFlavour = "TcpCubic"
            elif(alg == "bbr"):
                algFlavour = "BbrFlavour"
            elif(alg == "bbr3"):
                algFlavour = "Bbr3Flavour"
            else:
                algFlavour = "OrbtcpFlavour"
                
            with open(fileName, 'w') as f:
                f.write('[General]' + '\n')
                f.write('\n' + 'network = doubledumbbellpathchange')
                f.write('\n' + 'sim-time-limit = 300s')
                f.write('\n' + 'record-eventlog=false')
                f.write('\n' + 'cmdenv-express-mode = true')
                f.write('\n' + 'cmdenv-redirect-output = false')
                f.write('\n' + 'cmdenv-output-file = dctcpLog.txt')
                f.write('\n' + '**.client*.tcp.conn-8.cmdenv-log-level = detail')
                f.write('\n' + 'cmdenv-log-prefix = %t | %m |\n\n')
                f.write('\n' + 'cmdenv-event-banners = false')
                f.write('\n' + '**.cmdenv-log-level = off\n')
                
                f.write('\n' + '**.**.tcp.conn-*.cwnd:vector(removeRepeats).vector-recording = true')
                #f.write('\n' + '**.**.tcp.conn-*.U:vector(removeRepeats).vector-recording = true')
                f.write('\n' + '**.**.tcp.conn-*.rtt:vector(removeRepeats).vector-recording = true')
                f.write('\n' + '**.**.tcp.conn-*.srtt:vector(removeRepeats).vector-recording = true')
                f.write('\n' + '**.**.tcp.conn-*.throughput:vector(removeRepeats).vector-recording = true')
                f.write('\n' + '**.**.tcp.conn-*.**.result-recording-modes = vector(removeRepeats)')
                
                f.write('\n' + '**.**.queue.queueLength:vector(removeRepeats).vector-recording = true')
                f.write('\n' + '**.**.queue.queueLength.result-recording-modes = vector(removeRepeats)')
                
                f.write('\n' + '**.**.goodput:vector(removeRepeats).vector-recording = true')
                f.write('\n' + '**.**.goodput.result-recording-modes = vector(removeRepeats)')
                
                f.write('\n' + '**.**.bandwidth:vector(removeRepeats).vector-recording = true')
                f.write('\n' + '**.**.bandwidth.result-recording-modes = vector(removeRepeats)')
                
                f.write('\n' + '**.**.mbytesInFlight:vector(removeRepeats).vector-recording = true')
                f.write('\n' + '**.**.mbytesInFlight.result-recording-modes = vector(removeRepeats)')
                
                
                f.write('\n' + '**.scalar-recording=false')
                f.write('\n' + '**.vector-recording=false')
                f.write('\n' + '**.bin-recording=false\n')
                
                f.write('\n' + '**.goodputInterval = 1s')
                f.write('\n' + '**.throughputInterval = 1s')
                
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
                    
                    f.write('\n' + '**.constantClient[*].numApps = 1')
                    f.write('\n' + '**.constantClient[*].app[*].typename  = "TcpGoodputSessionApp"')
                    f.write('\n' + '*.constantClient[*].app[0].tClose = -1s')
                    f.write('\n' + '*.constantClient[*].app[0].sendBytes = 2GB')
                    f.write('\n' + '*.constantClient[*].app[0].dataTransferMode = "bytecount"')
                    f.write('\n' + '*.constantClient[*].app[0].statistic-recording = true\n')
                    f.write('\n' + '**.constantServer[*].numApps = 1')
                    f.write('\n' + '**.constantServer[*].app[*].typename  = "TcpSinkApp"')
                    f.write('\n' + '**.constantServer[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    
                    f.write('\n' + '**.pathChangeClient[*].numApps = 1')
                    f.write('\n' + '**.pathChangeClient[*].app[*].typename  = "TcpGoodputSessionApp"')
                    f.write('\n' + '*.pathChangeClient[*].app[0].tClose = -1s')
                    f.write('\n' + '*.pathChangeClient[*].app[0].sendBytes = 2GB')
                    f.write('\n' + '*.pathChangeClient[*].app[0].dataTransferMode = "bytecount"')
                    f.write('\n' + '*.pathChangeClient[*].app[0].statistic-recording = true\n')
                    f.write('\n' + '**.pathChangeServer[*].numApps = 1')
                    f.write('\n' + '**.pathChangeServer[*].app[*].typename  = "TcpSinkApp"')
                    f.write('\n' + '**.pathChangeServer[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    
                    f.write('\n' + '**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"\n')
                    f.write('\n' + '**.tcp.initialSsthresh = ' + str(400*1448) + '\n')
                    
                    f.write('\n' + '*.configurator.config = xml("<config><interface hosts=\'**\' address=\'10.x.x.x\' netmask=\'255.x.x.x\'/><autoroute metric=\'weight\'/></config>")\n')
                    f.write('\n' + '*.configurator.updateInterval = 100.000001s\n')
                    f.write('\n' + '*.configurator.optimizeRoutes = false\n')
                    f.write('\n' + '*.*.forwarding = false\n')
                    
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
                    
                    f.write('\n' + '**.constantClient[*].numApps = 1')
                    f.write('\n' + '**.constantClient[*].app[*].typename  = "TcpGoodputSessionApp"')
                    f.write('\n' + '*.constantClient[*].app[0].tClose = -1s')
                    f.write('\n' + '*.constantClient[*].app[0].sendBytes = 2GB')
                    f.write('\n' + '*.constantClient[*].app[0].dataTransferMode = "bytecount"')
                    f.write('\n' + '*.constantClient[*].app[0].statistic-recording = true\n')
                    f.write('\n' + '**.constantServer[*].numApps = 1')
                    f.write('\n' + '**.constantServer[*].app[*].typename  = "TcpSinkApp"')
                    f.write('\n' + '**.constantServer[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    
                    f.write('\n' + '**.pathChangeClient[*].numApps = 1')
                    f.write('\n' + '**.pathChangeClient[*].app[*].typename  = "TcpGoodputSessionApp"')
                    f.write('\n' + '*.pathChangeClient[*].app[0].tClose = -1s')
                    f.write('\n' + '*.pathChangeClient[*].app[0].sendBytes = 2GB')
                    f.write('\n' + '*.pathChangeClient[*].app[0].dataTransferMode = "bytecount"')
                    f.write('\n' + '*.pathChangeClient[*].app[0].statistic-recording = true\n')
                    f.write('\n' + '**.pathChangeServer[*].numApps = 1')
                    f.write('\n' + '**.pathChangeServer[*].app[*].typename  = "TcpSinkApp"')
                    f.write('\n' + '**.pathChangeServer[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    
                    f.write('\n' + '**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"\n')
                    f.write('\n' + '**.tcp.initialSsthresh = ' + str(400*1448) + '\n')
                    
                    f.write('\n' + '*.configurator.config = xml("<config><interface hosts=\'**\' address=\'10.x.x.x\' netmask=\'255.x.x.x\'/><autoroute metric=\'weight\'/></config>")\n')
                    f.write('\n' + '*.configurator.updateInterval = 100.000001s\n')
                    f.write('\n' + '*.configurator.optimizeRoutes = false\n')
                    f.write('\n' + '*.*.forwarding = false\n')
                elif(algFlavour == "Bbr3Flavour"):
                    f.write('\n' + '**.tcp.typename = "Bbr"')
                    f.write('\n' + '**.tcp.tcpAlgorithmClass = "Bbr3Flavour"')
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
                    
                    f.write('\n' + '**.constantClient[*].numApps = 1')
                    f.write('\n' + '**.constantClient[*].app[*].typename  = "TcpGoodputSessionApp"')
                    f.write('\n' + '*.constantClient[*].app[0].tClose = -1s')
                    f.write('\n' + '*.constantClient[*].app[0].sendBytes = 2GB')
                    f.write('\n' + '*.constantClient[*].app[0].dataTransferMode = "bytecount"')
                    f.write('\n' + '*.constantClient[*].app[0].statistic-recording = true\n')
                    f.write('\n' + '**.constantServer[*].numApps = 1')
                    f.write('\n' + '**.constantServer[*].app[*].typename  = "TcpSinkApp"')
                    f.write('\n' + '**.constantServer[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    
                    f.write('\n' + '**.pathChangeClient[*].numApps = 1')
                    f.write('\n' + '**.pathChangeClient[*].app[*].typename  = "TcpGoodputSessionApp"')
                    f.write('\n' + '*.pathChangeClient[*].app[0].tClose = -1s')
                    f.write('\n' + '*.pathChangeClient[*].app[0].sendBytes = 2GB')
                    f.write('\n' + '*.pathChangeClient[*].app[0].dataTransferMode = "bytecount"')
                    f.write('\n' + '*.pathChangeClient[*].app[0].statistic-recording = true\n')
                    f.write('\n' + '**.pathChangeServer[*].numApps = 1')
                    f.write('\n' + '**.pathChangeServer[*].app[*].typename  = "TcpSinkApp"')
                    f.write('\n' + '**.pathChangeServer[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    
                    f.write('\n' + '**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"\n')
                    f.write('\n' + '**.tcp.initialSsthresh = ' + str(400*1448) + '\n')
                    
                    f.write('\n' + '*.configurator.config = xml("<config><interface hosts=\'**\' address=\'10.x.x.x\' netmask=\'255.x.x.x\'/><autoroute metric=\'weight\'/></config>")\n')
                    f.write('\n' + '*.configurator.updateInterval = 100.000001s\n')
                    f.write('\n' + '*.configurator.optimizeRoutes = false\n')
                    f.write('\n' + '*.*.forwarding = false\n')    
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
                    
                    f.write('\n' + '**.constantClient[*].numApps = 1')
                    f.write('\n' + '**.constantClient[*].app[*].typename  = "TcpGoodputSessionApp"')
                    f.write('\n' + '*.constantClient[*].app[0].tClose = -1s')
                    f.write('\n' + '*.constantClient[*].app[0].sendBytes = 2GB')
                    f.write('\n' + '*.constantClient[*].app[0].dataTransferMode = "bytecount"')
                    f.write('\n' + '*.constantClient[*].app[0].statistic-recording = true\n')
                    f.write('\n' + '**.constantServer[*].numApps = 1')
                    f.write('\n' + '**.constantServer[*].app[*].typename  = "TcpSinkApp"')
                    f.write('\n' + '**.constantServer[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    
                    f.write('\n' + '**.pathChangeClient[*].numApps = 1')
                    f.write('\n' + '**.pathChangeClient[*].app[*].typename  = "TcpGoodputSessionApp"')
                    f.write('\n' + '*.pathChangeClient[*].app[0].tClose = -1s')
                    f.write('\n' + '*.pathChangeClient[*].app[0].sendBytes = 2GB')
                    f.write('\n' + '*.pathChangeClient[*].app[0].dataTransferMode = "bytecount"')
                    f.write('\n' + '*.pathChangeClient[*].app[0].statistic-recording = true\n')
                    f.write('\n' + '**.pathChangeServer[*].numApps = 1')
                    f.write('\n' + '**.pathChangeServer[*].app[*].typename  = "TcpSinkApp"')
                    f.write('\n' + '**.pathChangeServer[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    
                    f.write('\n' + '**.constantRouter1.ppp[2].queue.typename = "IntQueue"\n')
                    f.write('\n' + '**.pathChangeRouter1.ppp[2].queue.typename = "IntQueue"\n')
                    f.write('\n' + '**.**.queue.typename = "DropTailQueue"\n')
                    f.write('\n' + '**.additiveIncreasePercent = 0.05')
                    f.write('\n' + '**.eta = 0.95\n')
                    f.write('\n' + '**.alpha = ' + str(0.01))
                    f.write('\n' + '**.fixedAvgRTTVal = '+ str(0) + '\n')
                    f.write('\n' + '**.tcp.initialSsthresh = ' + str(400*1448) + '\n')
                    
                    f.write('\n' + '*.configurator.config = xml("<config><interface hosts=\'**\' address=\'10.x.x.x\' netmask=\'255.x.x.x\'/><autoroute metric=\'weight\'/></config>")\n')
                    f.write('\n' + '*.configurator.updateInterval = 100.000001s\n')
                    f.write('\n' + '*.configurator.optimizeRoutes = false\n')
                    f.write('\n' + '*.*.forwarding = false\n')
                    
                    
                dir = [f for f in os.listdir('../../paperExperiments/scenarios/experiment3/.')]
                #TODO Generate Run x Buffer Size  = 5 * 3 = CubicRun1SmallBuffer/CubicRun1MediuBuffer
                for xmlFile in dir:
                    scenarioName = os.path.basename(xmlFile)[:-4]
                    for i in range(numOfRuns):
                        random.seed(simSeed + i)
                        configName = alg.title() + str(scenarioName) + queueIniTitle + "Run" + str(i+1)
                        print(configName)
                        f.write('\n' + '[Config ' + configName + ']')
                        f.write('\n' + 'extends = General \n')
                        
                        f.write('\n' + '**.numberOfConstantFlows = 2\n')
                        f.write('\n' + '**.numberOfPathChangeFlows = 2 \n')
                                                    
                        for constantClientNumb in range(numOfConstClients):
                            constantClientStart = random.randint(0,50)
                            f.write('\n' + '*.constantClient[' + str(constantClientNumb) + '].app[0].connectAddress =  "constantServer[" + string(parentIndex()) +"]"')
                            f.write('\n' + '*.constantClient[' + str(constantClientNumb) + '].app[0].tOpen = '+ str(constantClientStart) +'s')
                            f.write('\n' + '*.constantClient[' + str(constantClientNumb) + '].app[0].tSend = '+ str(constantClientStart) +'s\n')
                        
                        for movingClientNumb in range(numOfMovingClients):
                            movingClientStart = random.randint(0,50)
                            f.write('\n' + '*.pathChangeClient[' + str(movingClientNumb) + '].app[0].connectAddress =  "pathChangeServer[" + string(parentIndex()) +"]"')
                            f.write('\n' + '*.pathChangeClient[' + str(movingClientNumb) + '].app[0].tOpen = '+ str(movingClientStart) +'s')
                            f.write('\n' + '*.pathChangeClient[' + str(movingClientNumb) + '].app[0].tSend = '+ str(movingClientStart) +'s\n')
                        
                        f.write('\n' + '**.ppp[*].queue.packetCapacity = ' + str(int(queueLength*qs)) + '\n')
                        f.write('\n' + '*.scenarioManager.script = xmldoc("../scenarios/experiment3/'+ str(scenarioName) + '.xml")\n')
    print('\nINI files generated!')
                    
                        
                
                
                
                
    
