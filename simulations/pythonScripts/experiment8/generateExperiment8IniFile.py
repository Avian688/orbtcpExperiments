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
import re
import math
import csv

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
    #numOfClients = int_to_word(len(sys.argv)-1)
    #folderName = '../scenarios/' + numOfClients + 'Flows'
    useIsls = ["true", "false"]
    bandwidth = 12500000
    numOfRuns = 5
    groundStationsCsv = 'ground_stations.csv'
    algorithms = ["orbtcp", "bbr", "cubic", "bbr3"]
    for alg in algorithms:
        for isl in useIsls:
            islName = ""
            if(isl == "true"):
                islName = "isls"
            elif(isl == "false"):
                islName = "bentpipe"
            fileName =  '../../paperExperiments/experiment8/experiment8_' + alg + "_" + islName +'.ini'
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
                f.write('\n' + 'network = leoconstellation')
                f.write('\n' + 'sim-time-limit = 300s')
                f.write('\n' + 'record-eventlog=false')
                f.write('\n' + 'cmdenv-express-mode = true')
                f.write('\n' + 'cmdenv-redirect-output = false')
                f.write('\n' + 'cmdenv-output-file = dctcpLog.txt')
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
                
                f.write('\n' + '**.constraintAreaMinX = 0m')
                f.write('\n' + '**.constraintAreaMaxX = 2160m')
                f.write('\n' + '**.constraintAreaMinY = 0m')
                f.write('\n' + '**.constraintAreaMaxY = 1080m')
                f.write('\n' + '**.constraintAreaMinZ = 0m')
                f.write('\n' + '**.constraintAreaMaxZ = 0m\n')
                
                f.write('\n' + '*.*.ipv4.typename = "LeoIpv4NetworkLayer"')
                f.write('\n' + '**.ipv4.configurator.typename = "LeoIpv4NodeConfigurator"')
                f.write('\n' + '*.*.ipv4.arp.typename = "GlobalArp"')
                f.write('\n' + '*.*.ipv4.routingTable.netmaskRoutes = ""')
                f.write('\n' + '**.groundStation[*].mobility.typename = "GroundStationMobility"')
                f.write('\n' + '*.groundStation[*].mobility.initFromDisplayString = false')
                f.write('\n' + '*.groundStation[*].mobility.updateFromDisplayString  = false\n')
                
                f.write('\n' + '*.configurator.config = xml("<config><interface hosts=\'**\' address=\'10.x.x.x\' netmask=\'255.x.x.x\'/><autoroute metric=\'delay\'/></config>")')
                f.write('\n' + '*.configurator.addStaticRoutes = true')
                f.write('\n' + '*.configurator.optimizeRoutes = false')
                f.write('\n' + '**.configurator.updateInterval = 100.00001ms')
                f.write('\n' + '*.*.forwarding = true\n')
                
                f.write('\n' + '*.visualizer.dataLinkVisualizer.packetFilter = "*"')
                f.write('\n' + '*.visualizer.networkRouteVisualizer.displayRoutes = true')
                f.write('\n' + '*.visualizer.networkRouteVisualizer.packetFilter = "*"')
                f.write('\n' + '*.visualizer.routingTableVisualizer.destinationFilter = "*"')
                f.write('\n' + '*.visualizer.statisticVisualizer.sourceFilter = "**.app[*]"')
                f.write('\n' + '*.visualizer.statisticVisualizer.signalName = "rtt"')
                f.write('\n' + '*.visualizer.statisticVisualizer.unit = "s"\n')
                
                f.write('\n' + '**.ppp[*].ppp.queue.typename = "DropTailQueue"')
                f.write('\n' + '**.ppp[*].ppp.queue.packetCapacity = 300\n')
                
                f.write('\n' + '**.satellite[*].NoradModule.satIndex = parentIndex()')
                f.write('\n' + '**.satellite[*].NoradModule.satName = "Starlink Satellite"')
                f.write('\n' + '**.satellite[*].**.bitrate = 100Mbps')
                f.write('\n' + '**.satellite[*].mobility.typename = "SatelliteMobility"')
                f.write('\n' + '**.satellite[*].mobility.updateInterval = 100ms\n')
                
                with open(groundStationsCsv, mode='r', newline='', encoding='utf-8') as gscsvfile:
                    reader = csv.DictReader(gscsvfile)
                    entries = list(reader)
                    
                f.write('\n' + '**.numOfSats = 1584')
                f.write('\n' + '**.satsPerPlane = 22')
                f.write('\n' + '**.numOfPlanes = 72')
                f.write('\n' + '**.incl = 53')
                f.write('\n' + '**.satellite[*].NoradModule.inclination = 53*0.0174533')
                f.write('\n' + '**.alt = 550')
                f.write('\n' + '**.satellite[*].NoradModule.altitude = 550')
                f.write('\n' + '**.numOfGS = ' + str(len(entries)))
                f.write('\n' + '**.dataRate = 100Mbps')
                f.write('\n' + '**.queueSize = 300')
                f.write('\n' + '**.loadFiles = false')
                f.write('\n' + '*.configurator.enableInterSatelliteLinks = ' + isl + '\n')
                
                for i, entry in enumerate(entries):    
                    latitude = entry['Latitude']
                    longitude = entry['Longitude']
                    gs_name = entry['Location Comment']
                    
                    f.write('\n' + f'# {gs_name} Ground Station')
                    f.write('\n' + f'**.groundStation[{i}].mobility.latitude = {latitude}')
                    f.write('\n' + f'**.groundStation[{i}].mobility.longitude = {longitude}')
                    f.write('\n' + f'**.groundStation[{i}].cityName = \"{gs_name}\"\n')
                    
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
                    # f.write('\n' + '**.client[*].numApps = 1')
                    # f.write('\n' + '**.client[*].app[*].typename  = "TcpGoodputSessionApp"')
                    # f.write('\n' + '*.client[*].app[0].tClose = -1s')
                    # f.write('\n' + '*.client[*].app[0].sendBytes = 2GB')
                    # f.write('\n' + '*.client[*].app[0].dataTransferMode = "bytecount"')
                    # f.write('\n' + '*.client[*].app[0].statistic-recording = true\n')
                    # f.write('\n' + '**.server[*].numApps = 1')
                    # f.write('\n' + '**.server[*].app[*].typename  = "TcpSinkApp"')
                    # f.write('\n' + '**.server[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    # f.write('\n' + '**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"\n')
                    # f.write('\n' + '**.tcp.initialSsthresh = ' + str(400*1448) + '\n')
                    
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
    
                    # f.write('\n' + '**.groundStation[*].numApps = 1')
                    # f.write('\n' + '**.groundStation[*].app[*].typename  = "TcpGoodputSessionApp"')
                    # f.write('\n' + '*.groundStation[*].app[0].tClose = -1s')
                    # f.write('\n' + '*.groundStation[*].app[0].sendBytes = 2GB')
                    # f.write('\n' + '*.groundStation[*].app[0].dataTransferMode = "bytecount"')
                    # f.write('\n' + '*.groundStation[*].app[0].statistic-recording = true\n')
                    # f.write('\n' + '**.server[*].numApps = 1')
                    # f.write('\n' + '**.server[*].app[*].typename  = "TcpSinkApp"')
                    # f.write('\n' + '**.server[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                    # f.write('\n' + '**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"\n')
                    # f.write('\n' + '**.tcp.initialSsthresh = ' + str(4000*1448) + '\n')
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
                        
                        # f.write('\n' + '**.groundStation[*].numApps = 1')
                        # f.write('\n' + '**.groundStation[*].app[*].typename  = "TcpGoodputSessionApp"')
                        # f.write('\n' + '*.groundStation[*].app[0].tClose = -1s')
                        # f.write('\n' + '*.groundStation[*].app[0].sendBytes = 2GB')
                        # f.write('\n' + '*.groundStation[*].app[0].dataTransferMode = "bytecount"')
                        # f.write('\n' + '*.groundStation[*].app[0].statistic-recording = true\n')
                        # f.write('\n' + '**.server[*].numApps = 1')
                        # f.write('\n' + '**.server[*].app[*].typename  = "TcpSinkApp"')
                        # f.write('\n' + '**.server[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
                        # f.write('\n' + '**.ppp[*].queue.typename = "BandwidthRecorderDropTailQueue"\n')
                        # f.write('\n' + '**.tcp.initialSsthresh = ' + str(4000*1448) + '\n')  
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
                    f.write('\n' + '**.interfaceType = "orbtcp.linklayer.ppp.IntInterface"')
                    #f.write('\n' + '**.tcp.initialSsthresh = 0\n')
                    
                    # f.write('\n' + '**.groundStation[*].numApps = 1')
                    # f.write('\n' + '**.groundStation[*].app[*].typename  = "TcpGoodputSessionApp"')
                    # f.write('\n' + '*.groundStation[*].app[0].tClose = -1s')
                    # f.write('\n' + '*.groundStation[*].app[0].sendBytes = 2GB')
                    # f.write('\n' + '*.groundStation[*].app[0].dataTransferMode = "bytecount"')
                    # f.write('\n' + '*.groundStation[*].app[0].statistic-recording = true\n')
                    # f.write('\n' + '**.server[*].numApps = 1')
                    # f.write('\n' + '**.server[*].app[*].typename  = "TcpSinkApp"')
                    # f.write('\n' + '**.server[*].app[*].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
    
                    f.write('\n' + '**.router1.ppp[1].queue.typename = "IntQueue"\n')
                    f.write('\n' + '**.**.queue.typename = "DropTailQueue"\n')
                    f.write('\n' + '**.additiveIncreasePercent = 0.05')
                    f.write('\n' + '**.eta = 0.95\n')
                    f.write('\n' + '**.alpha = ' + str(0.01))
                    f.write('\n' + '**.fixedAvgRTTVal = '+ str(0) + '\n')
                    f.write('\n' + '**.tcp.initialSsthresh = ' + str(4000*1448) + '\n')
                    
                    for i in range(numOfRuns):
                        random.seed(simSeed + i)
                        configName = alg.title() + '_' + islName + '_' + str(i)
                        groundStationStart = random.uniform(0,0.5)
                        f.write('\n' + '[Config ' + configName + '_Run' + str(i+1) + ']')
                        f.write('\n' + 'extends = General \n')
                        f.write('\n' + '**.numberOfFlows = 1 \n')
                        # f.write('\n' + '*.groundStation[0].app[0].connectAddress = "server[0]"')
                        # f.write('\n' + '*.groundStation[0].app[0].tOpen  = '+ str(groundStationStart) +'s')
                        # f.write('\n' + '*.groundStation[0].app[0].tSend = '+ str(groundStationStart) +'s\n')
                        #f.write('\n' + '**.ppp[*].queue.packetCapacity = ' + str(math.ceil((((rtt/1000)*bandwidth)/1448)*qs)) + '\n')
    print('\nINI files generated!')
                
                    
            
            
            
            


