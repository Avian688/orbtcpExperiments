#!/usr/bin/env python

# Generates a INI file given the OrbTCP flavour folder. INI file will be filled using the scenarios folder
# generateAlphaIniFileExtension orbtcp 
# Aiden Valentine

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import os
import re

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
        flavour = arg[0].upper() + arg[1:] + "Flavour"
        fileName =  '../'+ arg +'/omnetpp.ini'
        print('\nGenerating ini files for ' + arg + '...')
        with open(fileName, 'a') as f:
            alphaValues = [0.01, 0.03, 0.05, 0.07, 0.09, 0.001, 0.003, 0.005, 0.007, 0.009]
            scenarioDirectoriesList = ["oneFlows", "twoFlows", "tenFlows", "twentyfiveFlows"]
            for dirName in scenarioDirectoriesList: 
                dir = [f for f in os.listdir('../scenarios/'+ dirName +'/.')]
                
                writeConfig = True
                for xmlFile in dir:
                    for alphaVal in alphaValues:
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
                            
                        if(len(flowsList) < 10):
                            writeConfig = False
                            continue
                            
                        configName = (configName + configFlowNames)
                        configName = configName[0].upper() + configName[1:]
                        alphaValStr = re.sub(r'(?<=\d)\.(?=\d)',r"dot", str(alphaVal))
                        f.write('\n' + '[Config ' + configName + "AlphaVal" + alphaValStr + ']')       
                        f.write('\n' + 'extends = General\n')
                        f.write('\n' + '**.numberOfFlows = ' + str(len(flowsList)) + '\n')  
                        f.write('\n' + '*.client[0].app[0].connectAddress = "server[0]"')
                        f.write('\n' + '*.client[0].app[0].tOpen = 0s')
                        f.write('\n' + '*.client[0].app[0].tSend = 0s\n')
                        f.write('\n' + '*.client[*].app[0].connectAddress = "server[" + string(parentIndex()) +"]"')
                        f.write('\n' + '*.client[*].app[0].tOpen = 0s')
                        f.write('\n' + '*.client[*].app[0].tSend = uniform(0s,5s)\n')
                        f.write('\n' + '**.ppp[*].queue.packetCapacity = ' + str(queueLength) + '\n')
                        f.write('\n' + '**.alpha = ' + str(alphaVal) + '\n')
                        f.write('\n' + '*.scenarioManager.script = xmldoc("../scenarios/'+ dirName +'/' + fileName + 'ms.xml")\n')
                
            for dirName in scenarioDirectoriesList:
                pathChangeFolder = ""
                for num in range(100):
                    positive = True
                    for j in range(2):
                        if(j == 1):
                            positive = False
                        pathChangeFolder = int_to_word(num) + "MsPathChange"
                        pathChangeFolder = pathChangeFolder[0].upper() + pathChangeFolder[1:]
                        if (not positive):
                            pathChangeFolder = "Minus" + pathChangeFolder
                        if os.path.exists('../scenarios/' + pathChangeFolder +'/'+ dirName):
                            dir = [f for f in os.listdir('../scenarios/' + pathChangeFolder +'/'+ dirName +'/.')]
                            for xmlFile in dir:
                                for alphaVal in alphaValues:
                                    fileName = os.path.basename(xmlFile)[:-6]
                                    flowsListString = fileName.split('-')
                                    flowsList = [ int(x) for x in flowsListString ]
                                    maxFlowSize = 0
                                    configFlowNames = ''
                                    for i in flowsList:
                                        if i > maxFlowSize:
                                            maxFlowSize = i
                                        configFlowNames = configFlowNames + str(i) + 'ms'
                                    queueLength = int((((maxFlowSize/1000)*18750000)/1460)*1.1)
                                    configName = ''
                                    if(len(flowsList) == 1):
                                        configName = (int_to_word(len(flowsList)) + 'Flow')
                                    else:
                                        configName = (int_to_word(len(flowsList)) + 'Flows')
                                        
                                    if(len(flowsList) < 10):
                                        continue
                                    configName = (configName + configFlowNames)
                                    configName = configName[0].upper() + configName[1:] + pathChangeFolder
                                    alphaValStr = re.sub(r'(?<=\d)\.(?=\d)',r"dot", str(alphaVal))
                                    f.write('\n' + '[Config ' + configName + "AlphaVal" + alphaValStr + ']')       
                                    f.write('\n' + 'extends = General\n')
                                    f.write('\n' + '**.numberOfFlows = ' + str(len(flowsList)) + '\n')  
                                    f.write('\n' + '*.client[0].app[0].connectAddress = "server[0]"')
                                    f.write('\n' + '*.client[0].app[0].tOpen = 0s')
                                    f.write('\n' + '*.client[0].app[0].tSend = 0s\n')
                                    f.write('\n' + '*.client[*].app[0].connectAddress = "server[" + string(parentIndex()) +"]"')
                                    f.write('\n' + '*.client[*].app[0].tOpen = 0s')
                                    f.write('\n' + '*.client[*].app[0].tSend = uniform(0s,5s)\n')
                                    f.write('\n' + '**.ppp[*].queue.packetCapacity = ' + str(queueLength) + '\n')
                                    f.write('\n' + '**.alpha = ' + str(alphaVal) + '\n')
                                    f.write('\n' + '*.scenarioManager.script = xmldoc("../scenarios/'+ pathChangeFolder[0].lower() + pathChangeFolder[1:] +'/'+ dirName +'/' + fileName + 'ms.xml")\n')
    print('\nINI files generated!')            
                
                    
            
            
            
            


