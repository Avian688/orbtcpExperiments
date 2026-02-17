#!/usr/bin/env python

# Generates INI files for OMNeT++ experiments using fixed client-server paths.
# Each path uses a different fixed buffer size.
# 

import sys
import csv
import random
import math

if __name__ == "__main__":
    simSeed = 1999
    numOfRuns = 5
    numOfClients = 2
    groundStationsCsv = 'ground_stations.csv'
    algorithms = ["orbtcp", "bbr", "cubic", "bbr3"]
    cities_coordinates = {
        "San Diego": {"latitude": 32.7157, "longitude": -117.1611},
        "Seattle": {"latitude": 47.6062, "longitude": -122.3321},
        "New York": {"latitude": 40.7128, "longitude": -74.0060},
        "London": {"latitude": 51.5074, "longitude": -0.1278},
        "Shanghai": {"latitude": 31.2304, "longitude": 121.4737}
    }

    custom_city_paths = [
        [  # Path 1
            {"source": "New York", "sourceIndex": 2, "destination": "London", "destIndex": 3},
            {"source": "New York", "sourceIndex": 2, "destination": "St John's Developmental", "destIndex": 56}
        ],
        [  # Path 2
            {"source": "London", "sourceIndex": 3, "destination": "Lacchiarella", "destIndex": 93},
            {"source": "London", "sourceIndex": 3, "destination": "Foggia Apulia", "destIndex": 94}
        ],
        [  # Path 3
            {"source": "San Diego", "sourceIndex": 0, "destination": "New York", "destIndex": 2},
            {"source": "Lawrence", "sourceIndex": 29, "destination": "New York", "destIndex": 2}
        ]
    ]

    fixed_buffer_sizes = {
        0: 372,  # Exp 1
        1: 128,  # Exp 2
        2: 288   # Exp3
    }

    for alg in algorithms:
        fileName = f'../../paperExperiments/experiment10/experiment10_{alg}.ini'
        print(f'\nGenerating ini files for {alg}...')

        if alg == "cubic":
            algFlavour = "TcpCubic"
        elif alg == "bbr":
            algFlavour = "BbrFlavour"
        elif alg == "bbr3":
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
            f.write('\n' + '*.configurator.configLocation = "../experiment8/"')
            
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
                for pathNum, path in enumerate(custom_city_paths):
                    configName = f"{alg.title()}_Pair{pathNum+1}_Run{i+1}"

                    f.write(f'\n[Config {configName}]')
                    f.write('\nextends = General')
                    f.write(f'\n**.numOfClients = {numOfClients}')
                    f.write(f'\n**.numberOfFlows = {numOfClients}')

                    bufferSize = fixed_buffer_sizes[pathNum]
                    f.write(f'\n**.queueSize = {bufferSize}\n')

                    for clientNum, route in enumerate(path):
                        sourceIndex = route["sourceIndex"]
                        destIndex = route["destIndex"]
                        groundStationStart = random.uniform(0, 1.5)

                        f.write(f'\n**.client[{clientNum}].connectModule = "groundStation[{sourceIndex}]"')
                        f.write(f'\n**.client[{clientNum}].numApps = 1')
                        f.write(f'\n**.client[{clientNum}].app[0].typename = "TcpGoodputSessionApp"')
                        f.write(f'\n*.client[{clientNum}].app[0].tClose = -1s')
                        f.write(f'\n*.client[{clientNum}].app[0].sendBytes = 2GB')
                        f.write(f'\n*.client[{clientNum}].app[0].dataTransferMode = "bytecount"')
                        f.write(f'\n*.client[{clientNum}].app[0].statistic-recording = true\n')

                        f.write(f'\n**.server[{clientNum}].connectModule = "groundStation[{destIndex}]"')
                        f.write(f'\n**.server[{clientNum}].numApps = 1')
                        f.write(f'\n**.server[{clientNum}].app[0].typename = "TcpSinkApp"')
                        f.write(f'\n**.server[{clientNum}].app[0].serverThreadModuleType = "tcpgoodputapplications.applications.tcpapp.TcpGoodputSinkAppThread"\n')

                        f.write(f'\n*.client[{clientNum}].app[0].connectAddress = "server[{clientNum}]"')
                        f.write(f'\n*.client[{clientNum}].app[0].tOpen = {groundStationStart}s')
                        f.write(f'\n*.client[{clientNum}].app[0].tSend = {groundStationStart}s\n')

        print(f"INI file written to {fileName}")
