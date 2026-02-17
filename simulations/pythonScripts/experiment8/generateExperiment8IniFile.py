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
    bandwidth = 12500000
    numOfRuns = 5
    groundStationsCsv = 'ground_stations.csv'
    algorithms = ["orbtcp", "bbr", "cubic", "bbr3"]
    queueSizes = [0.2, 1, 4]
    cities_coordinates = {
        "San Diego": {"latitude": 32.7157, "longitude": -117.1611},
        "Seattle": {"latitude": 47.6062, "longitude": -122.3321},
        "New York": {"latitude": 40.7128, "longitude": -74.0060},
        "London": {"latitude": 51.5074, "longitude": -0.1278},
        "Shanghai": {"latitude": 31.2304, "longitude": 121.4737}
    }
    
    city_pairs = [
        ("San Diego", "Seattle", {
            "isl": 157,
            "bentpipe": 157
        }),
        ("Seattle", "New York", {
            "isl": 287,
            "bentpipe": 311
        }),
        ("San Diego", "New York", {
            "isl": 287,
            "bentpipe": 317
        }),
        ("New York", "London", {
            "isl": 371
        }),
        ("San Diego", "Shanghai", {
            "isl": 707
        })
    ]
    
    for alg in algorithms:
        fileName =  '../../paperExperiments/experiment8/experiment8_' + alg +'.ini'
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
            
            f.write('\n' + '**.**.queue.queueLength:vector(removeRepeats).vector-recording = false')
            f.write('\n' + '**.**.queue.queueLength.result-recording-modes = vector(removeRepeats)')
            
            f.write('\n' + '**.**.goodput:vector(removeRepeats).vector-recording = true')
            f.write('\n' + '**.**.goodput.result-recording-modes = vector(removeRepeats)')
            
            f.write('\n' + '**.**.bandwidth:vector(removeRepeats).vector-recording = true')
            f.write('\n' + '**.**.bandwidth.result-recording-modes = vector(removeRepeats)')
            
            f.write('\n' + '**.**.mbytesInFlight:vector(removeRepeats).vector-recording = false')
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
            f.write('\n' + '**.numOfGS = ' + str(len(entries)+len(cities_coordinates)))
            f.write('\n' + '**.dataRate = 100Mbps')
            f.write('\n' + '**.loadFiles = true')
            
            currentGsNum = 0
            for key, value in cities_coordinates.items():
                f.write('\n\n' + '# ' + key +' Ground Station')
                f.write('\n' + '**.groundStation['+ str(currentGsNum) +'].mobility.latitude = ' + str(value["latitude"]))
                f.write('\n' + '**.groundStation['+ str(currentGsNum) +'].mobility.longitude = ' + str(value["longitude"]))
                f.write('\n' + '**.groundStation['+ str(currentGsNum) +'].cityName = \"'+ key +'\"')
                currentGsNum = currentGsNum + 1
                            
            for i, entry in enumerate(entries):    
                latitude = entry['Latitude']
                longitude = entry['Longitude']
                gs_name = entry['Location Comment']
                
                f.write('\n\n' + f'# {gs_name} Ground Station')
                f.write('\n' + f'**.groundStation[{i+currentGsNum}].mobility.latitude = {latitude}')
                f.write('\n' + f'**.groundStation[{i+currentGsNum}].mobility.longitude = {longitude}')
                f.write('\n' + f'**.groundStation[{i+currentGsNum}].cityName = \"{gs_name}\"')
            f.write('\n')    
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
                f.write('\n' + '**.tcp.initialSsthresh = ' + str(4000*1448) + '\n')  
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
                    f.write('\n' + '**.tcp.initialSsthresh = ' + str(4000*1448) + '\n')  
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
                f.write('\n' + '**.**.ppp[*].queue.typename = "IntQueue"\n')
                f.write('\n' + '**.**.queue.typename = "DropTailQueue"\n')
                f.write('\n' + '**.additiveIncreasePercent = 0.05')
                f.write('\n' + '**.eta = 0.95\n')
                f.write('\n' + '**.alpha = ' + str(0.01))
                f.write('\n' + '**.fixedAvgRTTVal = '+ str(0) + '\n')
                f.write('\n' + '**.tcp.initialSsthresh = ' + str(4000*1448) + '\n')
            
            for i in range(numOfRuns):
                for qs in queueSizes:
                    queueIniTitle = ""
                    if qs == 0.2:
                        queueIniTitle = "smallbuffer"
                    elif qs == 1:
                        queueIniTitle = "mediumbuffer"
                    elif qs == 4:
                        queueIniTitle = "largebuffer"
            
                    for pair in city_pairs:
                        sourceName = pair[0]
                        destinationName = pair[1]
                        mode_to_buffer = pair[2]  # Now a dictionary like {"isl": 173, "bentpipe": 173}
                        
                        source = sourceName.replace(" ", "")
                        destination = destinationName.replace(" ", "")
            
                        for mode, bs in mode_to_buffer.items():
                            random.seed(simSeed + i)
                            configName = f"{alg.title()}_{source}To{destination}_{mode}_{queueIniTitle}"
                            
                            groundStationStart = random.uniform(0, 1)
            
                            f.write('\n' + f'[Config {configName}_Run{i+1}]')
                            f.write('\n' + 'extends = General \n')
            
                            f.write('\n' + '**.numberOfFlows = 1 \n')
                            if mode == "isl":
                                f.write('\n' + '**.enableInterSatelliteLinks = true\n')
                            else:
                                f.write('\n' + '**.enableInterSatelliteLinks = false\n')
            
                            # Resolve indices
                            sourceNum = 0
                            sourceNumFound = False
                            destNum = 0
                            destNumFound = False
                            for key in cities_coordinates:
                                if sourceName == key:
                                    sourceNumFound = True
                                elif destinationName == key:
                                    destNumFound = True
                                if not sourceNumFound:
                                    sourceNum += 1
                                if not destNumFound:
                                    destNum += 1
                            
                            bufferSize = math.ceil(bs * qs)     
                            # Set buffer size (this is the key part you’re adding)
                            f.write('\n' + f'**.groundStation[{sourceNum}].app[0].packetBufferSize = {bufferSize} \n')
                            f.write('\n' + f'**.queueSize = {bufferSize}')

                            f.write('\n' + f'**.groundStation[{sourceNum}].numApps = 1')
                            f.write('\n' + f'**.groundStation[{sourceNum}].app[0].typename  = "TcpGoodputSessionApp"')
                            f.write('\n' + f'*.groundStation[{sourceNum}].app[0].tClose = -1s')
                            f.write('\n' + f'*.groundStation[{sourceNum}].app[0].sendBytes = 2GB')
                            f.write('\n' + f'*.groundStation[{sourceNum}].app[0].dataTransferMode = "bytecount"')
                            f.write('\n' + f'*.groundStation[{sourceNum}].app[0].statistic-recording = true\n')
            
                            f.write('\n' + f'**.groundStation[{destNum}].numApps = 1')
                            f.write('\n' + f'**.groundStation[{destNum}].app[0].typename  = "TcpSinkApp"')
                            f.write('\n' + f'**.groundStation[{destNum}].app[0].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')
            
                            f.write('\n' + f'*.groundStation[{sourceNum}].app[0].connectAddress = "groundStation[{destNum}]"')
                            f.write('\n' + f'*.groundStation[{sourceNum}].app[0].tOpen  = {groundStationStart}s')
                            f.write('\n' + f'*.groundStation[{sourceNum}].app[0].tSend = {groundStationStart}s\n')
    print('\nINI files generated!')
                
                    
            
            
            
            


