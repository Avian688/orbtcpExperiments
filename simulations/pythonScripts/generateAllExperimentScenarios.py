#!/usr/bin/env python

# Generates all scenarios
# generateAllExperimentScenarios
# Aiden Valentine

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import os
import subprocess
from itertools import combinations_with_replacement

def main():
    deleteFilesProc = subprocess.Popen("rm -R -- */", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd='../scenarios/')
    deleteFilesProc.wait()
    cores = 4
    currentProc = 0
    processList = []
    rtts = [1, 25,50,75,100]
    twoFlowsList = list(combinations_with_replacement(rtts, 2))
    tenFlowsList = [(1,1,1,1,1,25,25,75,75,100), (1,1,25,25,50,50,75,75,100,100), (1,1,50,50,50,50,75,75,100,100), (1,1,10,10,25,100,100,100,100,100)]
    twentyFiveFlowsList = [(1, 5, 10, 25, 25, 25, 25, 50, 50, 50, 50, 50, 50, 75, 75, 75, 75, 75, 75, 75, 75, 75, 100, 100, 100), (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 5, 5, 5, 5, 5, 5, 5, 10, 10, 25, 25, 25), (5, 9, 13, 17, 21, 25, 29, 33, 37, 41, 45, 49, 53, 57, 61, 65, 69, 73, 77, 81, 85, 89, 93, 97, 100)]
    
    print("------------ Generating all normal scenarios ------------")
    
    currentProc = 0
    processList = []
    for val in rtts:
        if(currentProc == cores):
            procCompleteNum = 0
            for proc in processList:
                proc.wait()
                procCompleteNum = procCompleteNum + 1
            currentProc = 0
            processList.clear()
            print(" ... Generating next batch of normal scenarios! ...\n")
        processList.append(subprocess.Popen("python3 generateScenario.py " + str(val) , shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))    
        currentProc = currentProc + 1
        
    currentProc = 0
    processList = []
    for tup in twoFlowsList + tenFlowsList + twentyFiveFlowsList:
        if(currentProc == cores):
            procCompleteNum = 0
            for proc in processList:
                proc.wait()
                procCompleteNum = procCompleteNum + 1
            currentProc = 0
            processList.clear()
            print(" ... Generating next batch of normal scenarios! ...\n")
        arguments = ""
        for val in tup:
            arguments += str(val) + " "
        processList.append(subprocess.Popen("python3 generateScenario.py " + arguments , shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))    
        print(arguments)
        currentProc = currentProc + 1
            
    print("------------ Generating all rtt change scenarios ------------")
    
    msChanges = [10,25,-10,-25]
    
    currentProc = 0
    processList = []
    for val in rtts:
        for msVal in msChanges:
            if(currentProc == cores):
                procCompleteNum = 0
                for proc in processList:
                    proc.wait()
                    procCompleteNum = procCompleteNum + 1
                currentProc = 0
                processList.clear()
                print(" ... Generating next batch of rtt change scenarios! ...\n")
            pathChangeVal = 0
            arguments = ""
            arguments += str(msVal) + " "
            if((val + msVal) <= 0):
                    val = val + (msVal*-1)
            arguments += str(val) + " "
            processList.append(subprocess.Popen("python3 generateRttChangeScenario.py " + arguments , shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))    
            print(arguments)
            currentProc = currentProc + 1
            
    currentProc = 0
    processList = []
    for tup in twoFlowsList + tenFlowsList + twentyFiveFlowsList:
        for msVal in msChanges:
            if(currentProc == cores):
                procCompleteNum = 0
                for proc in processList:
                    proc.wait()
                    procCompleteNum = procCompleteNum + 1
                currentProc = 0
                processList.clear()
                print(" ... Generating next batch of rtt change scenarios! ...\n")
            arguments = ""
            pathChangeVal = 0
            
            arguments += str(msVal) + " "
            for val in tup:
                if((val + msVal) <= 0):
                    val = val + (msVal*-1)
                arguments += str(val) + " "
            processList.append(subprocess.Popen("python3 generateRttChangeScenario.py " + arguments , shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))    
            print(arguments)
            currentProc = currentProc + 1
            
if __name__ == "__main__":
    main()