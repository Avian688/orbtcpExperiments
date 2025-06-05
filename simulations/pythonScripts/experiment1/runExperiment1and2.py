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
    endStep = 8
    currStep = 1
    cores = 30
    currentProc = 0
    processList = []
    congControlList = ["bbr3","bbr", "orbtcp", "cubic"]
    experiments = ["experiment1", "experiment2"]
    runs = 50
    runList = list(range(1,runs+1))

    if(currStep <= endStep and currStep >= startStep and "experiment1" in experiments): #STEP 1
        subprocess.Popen("python3 generateExperiment1Scenarios.py", shell=True).communicate(timeout=30)
        subprocess.Popen("python3 generateExperiment1IniFile.py", shell=True).communicate(timeout=30)
        subprocess.Popen("python3 ../experiment2/generateExperiment2Scenarios.py", shell=True).communicate(timeout=30)
        subprocess.Popen("python3 ../experiment2/generateExperiment2IniFile.py", shell=True).communicate(timeout=30)

        subprocess.Popen("rm experiment1runTimes.txt", shell=True).communicate(timeout=30)
        subprocess.Popen("rm experiment2runTimes.txt", shell=True).communicate(timeout=30)
        for c in congControlList:
            subprocess.Popen("rm -r ../../paperExperiments/experiment1/csvs/" + c, shell=True).communicate(timeout=30)
            subprocess.Popen("rm -r ../../paperExperiments/experiment2/csvs/" + c, shell=True).communicate(timeout=30)
            
        #subprocess.Popen("rm ../../paperExperiments/experiment1/results/*", shell=True).communicate(timeout=30)
        #subprocess.Popen("rm ../../paperExperiments/experiment2/results/*", shell=True).communicate(timeout=30)
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
                        processList.append(subprocess.Popen("opp_run -r 0 -m -u Cmdenv -c " + configName +" -n ../..:../../../src:../../../../bbr/src:../../../../inet4.5/src:../../../../tcpPaced/src:../../../../cubic/src:../../../../orbtcp/src::../../../../tcpGoodputApplications/src --image-path=../../../../inet4.5/images -l ../../../src/orbtcpExperiments -l ../../../../bbr/src/bbr -l ../../../../inet4.5/src/INET -l ../../../../tcpPaced/src/tcpPaced -l ../../../../cubic/src/cubic -l ../../../../orbtcp/src/orbtcp -l ../../../../tcpGoodputApplications/src/tcpGoodputApplications experiment1_" + cc + ".ini", shell=True, cwd='../../paperExperiments/experiment1', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
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
        time.sleep(5)
    currStep += 1
    currentProc = 0
    processList.clear()

    
    if(currStep <= endStep and currStep >= startStep and "experiment2" in experiments): #STEP 2
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
                        processList.append(subprocess.Popen("opp_run -r 0 -m -u Cmdenv -c " + configName +" -n ../..:../../../src:../../../../bbr/simulations:../../../../bbr/src:../../../../inet4.5/examples:../../../../inet4.5/showcases:../../../../inet4.5/src:../../../../inet4.5/tests/validation:../../../../inet4.5/tests/networks:../../../../inet4.5/tutorials:../../../../tcpPaced/src:../../../../tcpPaced/simulations:../../../../cubic/simulations:../../../../cubic/src:../../../../orbtcp/simulations:../../../../orbtcp/src:../../../../tcpGoodputApplications/simulations:../../../../tcpGoodputApplications/src --image-path=../../../../inet4.5/images -l ../../../src/orbtcpExperiments -l ../../../../bbr/src/bbr -l ../../../../inet4.5/src/INET -l ../../../../tcpPaced/src/tcpPaced -l ../../../../cubic/src/cubic -l ../../../../orbtcp/src/orbtcp -l ../../../../tcpGoodputApplications/src/tcpGoodputApplications experiment2_" + cc + ".ini", shell=True, cwd='../../paperExperiments/experiment2', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
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
        time.sleep(5)
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
        time.sleep(5)
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
        time.sleep(5)
        
        processList.clear()
        currentProc = 0   
    currStep += 1
    
    print("CSVs created for experiments 1 and 2!\n")
        
    if(currStep <= endStep and currStep >= startStep): #STEP 5
        currentProc = 0
        print("Extracting CSV data!!\n")
        print("------------ Extracting CSV Files for experiment 1 + 2 ------------")
        processListStr = []
        for exp in experiments:
            if(exp == "experiment1"):
                runNam = "Run"   
            else:
                runNam = "LossRun" 
            for protocol in congControlList:
                for run in runList:
                    filePath = '../../paperExperiments/' + exp +'/results/'+ protocol.title() + runNam + str(run) + '.csv'
                    if os.path.exists(filePath):
                         processListStr.append("python3 extractSingleCsvFile.py " + filePath + " " + exp + " " + protocol + " " + str(run))
        
        currentProc = 0
        while(len(processListStr) > 0):
            process = processListStr.pop()
            print(process + "\n")
            processList.append(subprocess.Popen(process, shell=True))
            currentProc += 1
            if(currentProc >= cores):
                for proc in processList:
                    proc.wait(timeout=300)
                currentProc = 0
                print("Csv Extraction batch complete!\n")
                print("Extracting next batch!\n")
                processList.clear()
        time.sleep(5)
    currStep += 1
    
        
    if(currStep <= endStep and currStep >= startStep): #STEP 6
        print("Plotting cumulative distribution!\n")
        subprocess.Popen("mkdir experiment1and2Cumulative", shell=True, cwd='../../plots/').communicate(timeout=10)
        time.sleep(3)
        p = subprocess.Popen("python3 ../../pythonScripts/experiment1/plotGoodputCumulativeDistribution.py", shell=True, cwd='../../plots/experiment1and2Cumulative/')
        p.wait(timeout=3600)
        time.sleep(1)
    currStep += 1
    
        
    if(currStep <= endStep and currStep >= startStep): #STEP 7
        subprocess.Popen("mkdir ../../plots/experiment1", shell=True).communicate(timeout=10)
        subprocess.Popen("mkdir ../../plots/experiment2", shell=True).communicate(timeout=10)
        for exp in experiments:
            subprocess.Popen("rm -r " + exp + "../", shell=True, cwd='../../plots/experiment1').communicate(timeout=10)
            subprocess.Popen("rm -r " + exp + "../", shell=True, cwd='../../plots/experiment2').communicate(timeout=10)
            print("\n-----Making plot diretories for " + exp + "-----\n")
            subprocess.Popen("mkdir " + exp, shell=True, cwd='../../plots/').communicate(timeout=10)
            for cc in congControlList:
                print("\n-----Making plot directories for " + cc + "-----\n")
                subprocess.Popen("mkdir " + cc, shell=True, cwd='../../plots/' + exp + '/').communicate(timeout=10)
                for run in runList:
                    subprocess.Popen("mkdir run" + str(run), shell=True, cwd='../../plots/' + exp + '/' + cc + '/' ).communicate(timeout=10)
        time.sleep(5)
    currStep += 1
    
    
    if(currStep <= endStep and currStep >= startStep): #STEP 8
        print("\nPlotting!")
        processListStr = []
        processListMerge = []
        for exp in experiments:
            for protocol in congControlList:
                for run in runList:
                    #print("\nCurrently on Run#" + str(run) + " \n")
        
                    runTitle = "run"
                       
                    goodputFilePath = '../../paperExperiments/' + exp + '/csvs/'+ protocol + '/' + runTitle + str(run) + '/singledumbbell.server[0].app[0]/goodput.csv'
                    throughputFilePath = '../../paperExperiments/' + exp + '/csvs/'+ protocol + '/' + runTitle + str(run) + '/singledumbbell.server[0].tcp.conn/throughput.csv'
                    cwndFilePath = '../../paperExperiments/' + exp + '/csvs/'+ protocol + '/' + runTitle + str(run) + '/singledumbbell.client[0].tcp.conn/cwnd.csv'
                    queueLengthFilePath = '../../paperExperiments/' + exp + '/csvs/'+ protocol + '/' + runTitle + str(run) + '/singledumbbell.router1.ppp[1].queue/queueLength.csv'
                    rttFilePath = '../../paperExperiments/' + exp + '/csvs/'+ protocol + '/' + runTitle + str(run) + '/singledumbbell.client[0].tcp.conn/rtt.csv'
                    inflightFilePath = '../../paperExperiments/' + exp + '/csvs/'+ protocol + '/' + runTitle + str(run) + '/singledumbbell.client[0].tcp.conn/mbytesInFlight.csv'
                    if os.path.exists(cwndFilePath) or os.path.exists(goodputFilePath) or os.path.exists(throughputFilePath) or os.path.exists(queueLengthFilePath):
                        #subprocess.Popen("mkdir goodput", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10)
                        #subprocess.Popen("mkdir throughput", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
                        #subprocess.Popen("mkdir cwnd", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
                        #subprocess.Popen("mkdir queueLength", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
                        #subprocess.Popen("mkdir rtt", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
                        processListStr.append(("python3 ../../../../pythonScripts/experiment1/plotGoodput.py " + "../../" + goodputFilePath, '../../plots/' + exp + '/' + protocol + '/run' + str(run)))
                        processListStr.append(("python3 ../../../../pythonScripts/experiment1/plotThroughput.py " + "../../" + throughputFilePath, '../../plots/' + exp + '/' + protocol + '/run' + str(run)))
                        processListStr.append(("python3 ../../../../pythonScripts/experiment1/plotCwnd.py " + "../../" + cwndFilePath, '../../plots/' + exp + '/' + protocol + '/run' + str(run)))
                        processListStr.append(("python3 ../../../../pythonScripts/experiment1/plotQueueLength.py " + "../../" + queueLengthFilePath, '../../plots/' + exp + '/' + protocol + '/run' + str(run)))
                        processListStr.append(("python3 ../../../../pythonScripts/experiment1/plotRtt.py " + "../../" + rttFilePath, '../../plots/' + exp + '/' + protocol + '/run' + str(run)))
                        processListStr.append(("python3 ../../../../pythonScripts/experiment1/plotBytesInFlight.py " + "../../" + inflightFilePath, '../../plots/' + exp + '/' + protocol + '/run' + str(run)))
                        processListMerge.append(("python3 ../../../../pythonScripts/experiment1/mergePdfs.py" , '../../plots/' + exp + '/' + protocol + '/run' + str(run)))
                    else:
                        print("CSV Entries do not exist! \n")
        print("Plotting current batch!\n")
        while(len(processListStr) > 0):
            processTup = processListStr.pop()
            print(processTup[0] + "\n")
            processList.append(subprocess.Popen(processTup[0], shell=True, cwd=processTup[1]))
            currentProc += 1
            if(currentProc >= cores):
                for proc in processList:
                    proc.wait(timeout=300)
                currentProc = 0
                print("Plot batch complete!\n")
                print("Plotting next batch!\n")
                processList.clear()
                
        print("Plotting merging batch!\n")
        while(len(processListMerge) > 0):
            processTup = processListMerge.pop()
            print(processTup[0] + "\n")
            processList.append(subprocess.Popen(processTup[0], shell=True, cwd=processTup[1]))
            currentProc += 1
            if(currentProc >= cores):
                for proc in processList:
                    proc.wait(timeout=300)
                currentProc = 0
                print("Merge batch complete!\n")
                print("Merging next batch!\n")
                processList.clear()
    currStep += 1
        
