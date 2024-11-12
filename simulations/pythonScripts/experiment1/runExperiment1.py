#!/usr/bin/env python

# Runs experiment 1
# runExperiment1
# Aiden Valentine

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import os
import subprocess
import time
           
if __name__ == "__main__":
    
    startStep = 1 
    endStep = 7
    currStep = 1
    cores = 4
    currentProc = 0
    processList = []
    congControlList = ["cubic","orbtcp"]
    experiments = ["experiment1","experiment2"]
    runs = 50
    runList = list(range(1,runs+1))
    
    if(currStep <= endStep and currStep >= startStep): #STEP 1
        subprocess.Popen("rm experiment1runTimes.txt", shell=True).communicate(timeout=30)
        subprocess.Popen("rm experiment2runTimes.txt", shell=True).communicate(timeout=30)
        
        with open('experiment1runTimes.txt', 'w') as f1:
            exp1RunNum = 1
            f1.write("--Experiment 1 Runtimes (s)--")
            for cc in congControlList:
                fileName =  '../../paperExperiments/experiment1/experiment1' + cc +'.ini'
                iniFile = open(fileName, 'r').readlines()
                print("----------experiment 1 " + cc + " simulations------------")
                for line in iniFile:
                    if line.find('[Config') != -1:
                        configName = (line[8:])[:-2]
                        progStart = time.time()
                        processList.append(subprocess.Popen("opp_run -r 0 -m -u Cmdenv -c " + configName +" -n ../..:../../../src:../../../../bbr/simulations:../../../../bbr/src:../../../../inet4.5/examples:../../../../inet4.5/showcases:../../../../inet4.5/src:../../../../inet4.5/tests/validation:../../../../inet4.5/tests/networks:../../../../inet4.5/tutorials:../../../../tcpPaced/src:../../../../tcpPaced/simulations:../../../../cubic/simulations:../../../../cubic/src:../../../../orbtcp/simulations:../../../../orbtcp/src:../../../../tcpGoodputApplications/simulations:../../../../tcpGoodputApplications/src --image-path=../../../../inet4.5/images -l ../../../src/orbtcpExperiments -l ../../../../bbr/src/bbr -l ../../../../inet4.5/src/INET -l ../../../../tcpPaced/src/tcpPaced -l ../../../../cubic/src/cubic -l ../../../../orbtcp/src/orbtcp -l ../../../../tcpGoodputApplications/src/tcpGoodputApplications experiment1" + cc + ".ini", shell=True, cwd='../../paperExperiments/experiment1', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                        currentProc = currentProc + 1
                        print("Running simulation [" + configName + "]... (Run #" + str(currentProc) + ")")
                        if(currentProc == cores):
                            procCompleteNum = 0
                            for proc in processList:
                                proc.wait()
                                now = time.time()
                                f1.write("Run "+ str(exp1RunNum) + ": " + str(now-progStart)) 
                                procCompleteNum = procCompleteNum + 1
                                print("\tRun #" + str(procCompleteNum) + " is complete!")
                                exp1RunNum += 1
                            currentProc = 0
                            processList.clear()
                            print(" ... Running next batch of simulations! ...\n")
        
        for proc in processList:
            proc.wait()
    
    currStep += 1
    currentProc = 0
    processList.clear()
    
    if(currStep <= endStep and currStep >= startStep): #STEP 2
        print("\nAll experiments in Experiment 1 has been run!\n")
        with open('experiment2runTimes.txt', 'w') as f2:
            f2.write("--Experiment 2 Runtimes (s)--")
            exp2RunNum = 1
            for cc in congControlList:
                fileName =  '../../paperExperiments/experiment2/experiment2' + cc +'.ini'
                iniFile = open(fileName, 'r').readlines()
                print("----------experiment 2 " + cc + " simulations------------")
                for line in iniFile:
                    if line.find('[Config') != -1:
                        configName = (line[8:])[:-2]
                        progStart = time.time()
                        processList.append(subprocess.Popen("opp_run -r 0 -m -u Cmdenv -c " + configName +" -n ../..:../../../src:../../../../bbr/simulations:../../../../bbr/src:../../../../inet4.5/examples:../../../../inet4.5/showcases:../../../../inet4.5/src:../../../../inet4.5/tests/validation:../../../../inet4.5/tests/networks:../../../../inet4.5/tutorials:../../../../tcpPaced/src:../../../../tcpPaced/simulations:../../../../cubic/simulations:../../../../cubic/src:../../../../orbtcp/simulations:../../../../orbtcp/src:../../../../tcpGoodputApplications/simulations:../../../../tcpGoodputApplications/src --image-path=../../../../inet4.5/images -l ../../../src/orbtcpExperiments -l ../../../../bbr/src/bbr -l ../../../../inet4.5/src/INET -l ../../../../tcpPaced/src/tcpPaced -l ../../../../cubic/src/cubic -l ../../../../orbtcp/src/orbtcp -l ../../../../tcpGoodputApplications/src/tcpGoodputApplications experiment2" + cc + ".ini", shell=True, cwd='../../paperExperiments/experiment2', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                        currentProc = currentProc + 1
                        print("Running simulation [" + configName + "]... (Run #" + str(currentProc) + ")")
                        if(currentProc == cores):
                            procCompleteNum = 0
                            for proc in processList:
                                proc.wait()
                                now = time.time()
                                f2.write("Run "+ str(exp2RunNum) + ": " + str(now-progStart)) 
                                procCompleteNum = procCompleteNum + 1
                                print("\tRun #" + str(procCompleteNum) + " is complete!")
                                exp2RunNum += 1
                            currentProc = 0
                            processList.clear()
                            print(" ... Running next batch of simulations! ...\n")
        
        for proc in processList:
            proc.wait()
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 3
        currentProc = 0
        print("\nAll experiments in Experiment 1 + 2 has been run!\n")
        folderLoc =  '../../paperExperiments/experiment1/results/'
        print("------------ Generating CSV Files for experiment 1 ------------")
        for file in os.listdir(folderLoc):
            if(file.endswith(".vec")):
                f = os.path.join(folderLoc, file)
                processList.append(subprocess.Popen("opp_scavetool export -o "+ "results/"+ file[:-7] + ".csv -F CSV-R " + "results/" + file , shell=True, cwd='../../paperExperiments/experiment1/'))
                currentProc = currentProc + 1
                print("Generating CSV file for [" + file + "]... (Run #" + str(currentProc) + ")")
                if(currentProc == cores):
                     for proc in processList:
                         proc.wait()
                     currentProc = 0
                     processList.clear()
                     print("     ... Running next batch! ...\n")
        
        for proc in processList:
            proc.wait()
        processList.clear()
        currentProc = 0
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 4    
        folderLoc =  '../../paperExperiments/experiment2/results/'
        print("------------ Generating CSV Files for experiment 2 ------------")
        for file in os.listdir(folderLoc):
            if(file.endswith(".vec")):
                f = os.path.join(folderLoc, file)
                processList.append(subprocess.Popen("opp_scavetool export -o "+ "results/"+ file[:-7] + ".csv -F CSV-R " + "results/" + file , shell=True, cwd='../../paperExperiments/experiment2/'))
                currentProc = currentProc + 1
                print("Generating CSV file for [" + file + "]... (Run #" + str(currentProc) + ")")
                if(currentProc == cores):
                     for proc in processList:
                         proc.wait()
                     currentProc = 0
                     processList.clear()
                     print("     ... Running next batch! ...\n")
        
        for proc in processList:
            proc.wait()
        
        processList.clear()
        currentProc = 0   
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 5
        subprocess.Popen("mkdir plots", shell=True).communicate(timeout=10) 
        subprocess.Popen("rm -r *", shell=True, cwd='plots/').communicate(timeout=10) 
        
        for exp in experiments:
            subprocess.Popen("mkdir " + exp, shell=True, cwd='plots/').communicate(timeout=10)
            for cc in congControlList:
                subprocess.Popen("mkdir " + cc, shell=True, cwd='plots/' + exp + '/').communicate(timeout=10)
                for run in runList:
                    subprocess.Popen("mkdir run" + str(run), shell=True, cwd='plots/' + exp + '/' + cc + '/' ).communicate(timeout=10)
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 6
        print("Plotting cumulative distribution!\n")
        subprocess.Popen("mkdir cumulativeGoodput", shell=True, cwd='plots/').communicate(timeout=10) 
        subprocess.Popen("python3 ../../plotGoodputCumulativeDistribution.py", shell=True, cwd='plots/cumulativeGoodput/').communicate(timeout=3600) 
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 7
        for exp in experiments:
            print("\n-----PLOTTING " + exp + "-----\n")
            for protocol in congControlList:
                print("\n-----PLOTTING " + protocol + "-----\n")
                for run in runList:
                    print("\nCurrently on Run#" + str(run) + " \n")
        
                    runTitle = "Run"
                    if(exp == "experiment2"):
                        runTitle = "LossRun"
        
                    filePath = '../../paperExperiments/' + exp +'/results/'+ protocol.title() + runTitle + str(run) + '.csv'
                    if os.path.exists(filePath):
                        subprocess.Popen("mkdir goodput", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/').communicate(timeout=10) 
                        subprocess.Popen("mkdir throughput", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/').communicate(timeout=10) 
                        subprocess.Popen("mkdir cwnd", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/').communicate(timeout=10) 
                        subprocess.Popen("mkdir queueLength", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/').communicate(timeout=10) 
                        subprocess.Popen("mkdir rtt", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/').communicate(timeout=10) 
                        
                        print("Plotting goodput...\n")
                        processList.append(subprocess.Popen("python3 ../../../../../plotGoodput.py " + "../../../../../" + filePath, shell=True, cwd='plots/' + exp + '/' + protocol + '/run' + str(run) + '/goodput/'))        
                        print("Plotting throughput...\n")
                        processList.append(subprocess.Popen("python3 ../../../../../plotThroughput.py " + "../../../../../" + filePath, shell=True, cwd='plots/' + exp + '/' + protocol + '/run' + str(run) + '/throughput/'))
                        print("Plotting cwnd...\n")
                        processList.append(subprocess.Popen("python3 ../../../../../plotCwnd.py " + "../../../../../" + filePath, shell=True, cwd='plots/' + exp + '/' + protocol + '/run' + str(run) + '/cwnd/'))
                        print("Plotting queue length...\n")
                        processList.append(subprocess.Popen("python3 ../../../../../plotQueueLength.py " + "../../../../../" + filePath, shell=True, cwd='plots/' + exp + '/' + protocol + '/run' + str(run) + '/queueLength/'))
                        print("Plotting rtt...\n")
                        processList.append(subprocess.Popen("python3 ../../../../../plotRtt.py " + "../../../../../" + filePath, shell=True, cwd='plots/' + exp + '/' + protocol + '/run' + str(run) + '/rtt/'))
                        currentProc += 5
                        if(currentProc >= cores):
                            for proc in processList:
                                proc.wait(timeout=300)
                            currentProc = 0
                            processList.clear()
    currStep += 1
        
