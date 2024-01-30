#!/usr/bin/env python

# Plots results given the OrbTCP flavour folders
# plotResults orbtcp ... orbTcpFlavourN
# Aiden Valentine

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import os
import shutil
import subprocess
           
if __name__ == "__main__":
    cores = 4
    folders = ["OneFlow", "TwoFlows", "FiveFlows", "TenFlows"]
    for arg in sys.argv[1:]:
        folderLoc =  '../'+ arg +'/results/'
        print("------------ Plotting results for " + arg + "------------")
        #clear folders
        processNestedList = []
        processFolderNameList = []
        for fi in folders:
            dir = '../pythonResults/' + arg + '/' + fi
            if os.path.exists(dir):
                shutil.rmtree(dir)
            os.makedirs(dir)
        for file in os.listdir(folderLoc):
            if(file.endswith(".csv")):
                print(file)
                fileName = file[:-14]
                #make folder
                f = os.path.join(folderLoc, file)
                processList = []
                processList.append("python3 ../../../../pythonScripts/plotCwnd.py ../../../" + folderLoc + file)
                processList.append("python3 ../../../../pythonScripts/plotU.py ../../../" + folderLoc + file)
                processList.append("python3 ../../../../pythonScripts/plotUsmoothed.py ../../../" + folderLoc + file)
                processList.append("python3 ../../../../pythonScripts/plotAdditiveIncrease.py ../../../" + folderLoc + file)
                processList.append("python3 ../../../../pythonScripts/plotRtt.py ../../../" + folderLoc + file)
                processList.append("python3 ../../../../pythonScripts/plotAvgRtt.py ../../../" + folderLoc + file)
                processList.append("python3 ../../../../pythonScripts/plotEstimatedRtt.py ../../../" + folderLoc + file)
                processList.append("python3 ../../../../pythonScripts/plotThroughput.py ../../../" + folderLoc + file)
                processList.append("python3 ../../../../pythonScripts/plotQueueLength.py ../../../" + folderLoc + file)
                processNestedList.append(processList)
                processFolderNameList.append(fileName)
                
                for fil in folders:
                    if fil in fileName:
                        dir2 = '../pythonResults/' + arg + "/" + fil + "/" + fileName
                        if os.path.exists(dir2):
                            shutil.rmtree(dir2)
                        os.makedirs(dir2)
        currentProc = 1
        currProcList = []
        print("Generating python results for Run #" + str(currentProc) + ")")
        currentFolderIter = 0
        for procList in processNestedList:
            for proc in procList:
                if(currentProc < cores):
                    foldName = "Other"
                    for folderName in folders:
                        if folderName in processFolderNameList[currentFolderIter]:
                            foldName = folderName
                    currProcList.append(subprocess.Popen(proc , shell=True, cwd='../pythonResults/' + arg + "/" + foldName + "/" + processFolderNameList[currentFolderIter]))
                    currentProc = currentProc + 1
                else:
                    for p in currProcList:
                         p.wait()
                    print("     ... Running next batch! ...\n")     
                    currProcList.clear()
                    currentProc = 0     
            currentFolderIter = currentFolderIter + 1
        processNestedList.clear()
        processFolderNameList.clear()
        
        