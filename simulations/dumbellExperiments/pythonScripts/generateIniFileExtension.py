#!/usr/bin/env python

# Generates a INI file given the OrbTCP flavour folder. INI file will be filled using the scenarios folder
# generateIniFileExtension orbtcp ... orbTcpFlavourN
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
        else: return d[num // 10 * 10] + '-' + d[num % 10]
    if (num > 100): 
        raise AssertionError('num is too large: %s' % str(num))
           
if __name__ == "__main__":
    #numOfClients = int_to_word(len(sys.argv)-1)
    #folderName = '../scenarios/' + numOfClients + 'Flows'
    flowList = ['twoFlows/1-100ms.xml','twoFlows/50-100ms.xml', 'twoFlows/1-50ms.xml', 'fiveFlows/1-100-100-100-100ms.xml', 'fiveFlows/1-25-50-75-100ms.xml', 'tenFlows/1-1-1-1-1-25-75-75-100-100ms.xml', 'tenFlows/1-1-25-25-50-50-75-75-100-100ms.xml']
    flowTitle = ['TwoFlows1ms100ms', 'TwoFlows50ms100ms', 'TwoFlows1ms50ms', 'FiveFlows1ms100ms100ms100ms100ms', 'FiveFlows1ms25ms50ms75ms100ms', 'TenFlows1ms1ms1ms1ms1ms25ms75ms75ms100ms100ms', 'TenFlows1ms1ms25ms25ms50ms50ms75ms75ms100ms100ms']
    numOfFlowsList = [2,2,2,5,5,10,10]
    alphaValues = [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09]
    fixedAvgRTTValues = [0.0]
    for arg in sys.argv[1:]:
        flavour = arg[0].upper() + arg[1:] + "Flavour"
        fileName =  '../'+ arg +'/omnetpp.ini'
        print('\nGenerating ini files for ' + arg + '...')
        with open(fileName, 'a') as f:
            flowNum = 0
            for flow in flowList:    
                for avgRttVal in fixedAvgRTTValues:    
                    for alphaVal in alphaValues:
                        alpha_str = str(alphaVal)
                        point_index = alpha_str.index(".")
                        f.write('\n' + '[Config ' + flowTitle[flowNum] + 'AvgRTTVal' + str(int(avgRttVal*1000)) + 'ms' + 'AlphaVal'+ alpha_str[:point_index] + '_' + alpha_str[point_index+1:] +']')       
                        f.write('\n' + 'extends = General\n')
                        f.write('\n' + '**.numberOfFlows = ' + str(numOfFlowsList[flowNum]) + '\n')  
                        f.write('\n' + '*.client[0].app[0].connectAddress = "server[0]"')
                        f.write('\n' + '*.client[0].app[0].tOpen = 0s')
                        f.write('\n' + '*.client[0].app[0].tSend = 0s\n')
                        f.write('\n' + '*.client[*].app[0].connectAddress = "server[" + string(parentIndex()) +"]"')
                        f.write('\n' + '*.client[*].app[0].tOpen = 0s')
                        f.write('\n' + '*.client[*].app[0].tSend = uniform(0s,5s)\n')
                        f.write('\n' + '**.ppp[*].queue.packetCapacity = 1284\n')
                        f.write('\n' + '**.alpha = ' + str(alphaVal))
                        f.write('\n' + '**.fixedAvgRTTVal = '+ str(avgRttVal) + '\n')
                        f.write('\n' + '*.scenarioManager.script = xmldoc("../scenarios/'+ flowList[flowNum] +'")\n')
                flowNum = flowNum + 1        
    print('\nINI files generated!')            
                
                    
            
            
            
            

