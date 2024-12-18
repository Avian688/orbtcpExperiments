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
    
    startStep = 2
    endStep = 5
    currStep = 1
    cores = 4
    currentProc = 0
    processList = []
    congControlList = ["cubic","orbtcp"]
    experiment = "experiment3"
    buffersizes = ["smallbuffer", "mediumbuffer", "largebuffer"]
    movingClientsRtts = [15,30,45,60,75,90] #OF AVERAGE BDP
    runs = 5
    runList = list(range(1,runs+1))
    
    if(currStep <= endStep and currStep >= startStep): #STEP 1
        subprocess.Popen("rm experiment3runTimes.txt", shell=True).communicate(timeout=30)
        
        with open('experiment3runTimes.txt', 'w') as f1:
            exp1RunNum = 1
            f1.write("--Experiment 3 Runtimes (s)--")
            for cc in congControlList:
                for bs in buffersizes:
                    fileName =  '../../paperExperiments/experiment3/experiment3' + cc + bs + '.ini'
                    iniFile = open(fileName, 'r').readlines()
                    print("----------experiment 3 " + cc + " " + bs + " simulations------------")
                    for line in iniFile:
                        if line.find('[Config') != -1:
                            configName = (line[8:])[:-2]
                            progStart = time.time()
                            processList.append(subprocess.Popen("opp_run -r 0 -m -u Cmdenv -c " + configName +" -n ../..:../../../src:../../../../bbr/simulations:../../../../bbr/src:../../../../inet4.5/examples:../../../../inet4.5/showcases:../../../../inet4.5/src:../../../../inet4.5/tests/validation:../../../../inet4.5/tests/networks:../../../../inet4.5/tutorials:../../../../tcpPaced/src:../../../../tcpPaced/simulations:../../../../cubic/simulations:../../../../cubic/src:../../../../orbtcp/simulations:../../../../orbtcp/src:../../../../tcpGoodputApplications/simulations:../../../../tcpGoodputApplications/src --image-path=../../../../inet4.5/images -l ../../../src/orbtcpExperiments -l ../../../../bbr/src/bbr -l ../../../../inet4.5/src/INET -l ../../../../tcpPaced/src/tcpPaced -l ../../../../cubic/src/cubic -l ../../../../orbtcp/src/orbtcp -l ../../../../tcpGoodputApplications/src/tcpGoodputApplications experiment3" + cc + bs + ".ini", shell=True, cwd='../../paperExperiments/experiment3', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
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
        currentProc = 0
        print("\nAll experiments in Experiment 3 has been run!\n")
        folderLoc =  '../../paperExperiments/experiment3/results/'
        print("------------ Generating CSV Files for experiment 3 ------------")
        for file in os.listdir(folderLoc):
            if(file.endswith(".vec")):
                f = os.path.join(folderLoc, file)
                processList.append(subprocess.Popen("opp_scavetool export -o "+ "results/"+ file[:-7] + ".csv -F CSV-R " + "results/" + file , shell=True, cwd='../../paperExperiments/experiment3/'))
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
    
    print("CSVs created for experiments 3!\n")
    
    if(currStep <= endStep and currStep >= startStep): #STEP 3
        currentProc = 0
        print("Extracting CSV data!!\n")
        print("------------ Extracting CSV Files for experiment 3------------")
        processListStr = []
        for protocol in congControlList:
            for buf in buffersizes:
                for rtt in movingClientsRtts:
                    for run in runList:
                        filePath = '../../paperExperiments/' + experiment +'/results/'+ protocol.title() + str(rtt) + 'ms' + buf + 'Run' + str(run) + '.csv'
                        if os.path.exists(filePath):
                             processListStr.append("python3 extractSingleCsvFile.py " + filePath + " " + experiment + " " + protocol + " " + buf + " " + str(rtt) + " " + str(run))
        
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
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 4
        subprocess.Popen("mkdir plots", shell=True).communicate(timeout=10) 
        subprocess.Popen("rm -r *", shell=True, cwd='plots/').communicate(timeout=10) 
        
        print("\n-----Making plot diretories for " + experiment + "-----\n")
        subprocess.Popen("mkdir " + experiment, shell=True, cwd='plots/').communicate(timeout=10)
        for cc in congControlList:
            print("\n-----Making plot directories for " + cc + "-----\n")
            subprocess.Popen("mkdir " + cc, shell=True, cwd='plots/' + experiment + '/').communicate(timeout=10)
            
            for buf in buffersizes:
                for rtt in movingClientsRtts:
                    for run in runList:
                        subprocess.Popen("mkdir " + str(buf), shell=True, cwd='plots/' + experiment + '/' + cc + '/' ).communicate(timeout=10)
                        subprocess.Popen("mkdir " + str(rtt) + 'ms', shell=True, cwd='plots/' + experiment + '/' + cc + '/' + buf).communicate(timeout=10)
                        subprocess.Popen("mkdir run" + str(run), shell=True, cwd='plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms').communicate(timeout=10)
                        
                        subprocess.Popen("mkdir constantClient0", shell=True, cwd='plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
                        subprocess.Popen("mkdir constantClient1", shell=True, cwd='plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
                        subprocess.Popen("mkdir pathChangeClient0", shell=True, cwd='plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
                        subprocess.Popen("mkdir pathChangeClient1", shell=True, cwd='plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
                        subprocess.Popen("mkdir constantBottlneckRouter", shell=True, cwd='plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
                        subprocess.Popen("mkdir pathChangeBottlneckRouter", shell=True, cwd='plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
                        subprocess.Popen("mkdir aggPlots", shell=True, cwd='plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 5
        print("\nPlotting!")
        processListStr = []
        for protocol in congControlList:
            for buf in buffersizes:
                for rtt in movingClientsRtts:
                    for run in runList:
                        #print("\nCurrently on Run#" + str(run) + " \n")
                        
                        dirPath = 'plots/' + experiment + '/' + protocol + '/' + buf + '/' + str(rtt) + 'ms' + '/run' + str(run) + '/' 
                        
                        runTitle = "run"
                        fileBeg = '../../paperExperiments/'+ experiment + '/csvs/'+ protocol.title() + '/' + buf + '/' + str(rtt) + 'ms/'+ runTitle + str(run)
                        fileStart = "../../../../../../../" + fileBeg
                        cwndFileList = []
                        rttFileList = []
                        tauFileList = []
                        UFileList = []
                        goodputFileList = []
                        queueLengthFileList = []
                        aggrPlotsFileList = []
                        
                        cwndFileList.append((fileStart + '/doubledumbbellpathchange.constantClient[0].tcp.conn-36/cwnd.csv', "constantClient0"))
                        rttFileList.append((fileStart + '/doubledumbbellpathchange.constantClient[0].tcp.conn-36/rtt.csv', "constantClient0"))
                        tauFileList.append((fileStart + '/doubledumbbellpathchange.constantClient[0].tcp.conn-36/tau.csv', "constantClient0"))
                        UFileList.append((fileStart + '/doubledumbbellpathchange.constantClient[0].tcp.conn-36/U.csv', "constantClient0"))
                        goodputFileList.append((fileStart + '/doubledumbbellpathchange.constantServer[0].app[0].thread_38/goodput.csv', "constantClient0"))
                        
                        cwndFileList.append((fileStart + '/doubledumbbellpathchange.constantClient[1].tcp.conn-37/cwnd.csv', "constantClient1"))
                        rttFileList.append((fileStart + '/doubledumbbellpathchange.constantClient[1].tcp.conn-37/rtt.csv', "constantClient1"))
                        tauFileList.append((fileStart + '/doubledumbbellpathchange.constantClient[1].tcp.conn-37/tau.csv', "constantClient1"))
                        UFileList.append((fileStart + '/doubledumbbellpathchange.constantClient[1].tcp.conn-37/U.csv', "constantClient1"))
                        goodputFileList.append((fileStart + '/doubledumbbellpathchange.constantServer[1].app[0].thread_39/goodput.csv', "constantClient1"))
                        
                        queueLengthFileList.append((fileStart + '/doubledumbbellpathchange.constantRouter1.ppp[2].queue/queueLength.csv', "constantBottlneckRouter"))
                        
                        cwndFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeClient[0].tcp.conn-40/cwnd.csv', "pathChangeClient0"))
                        rttFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeClient[0].tcp.conn-40/rtt.csv', "pathChangeClient0"))
                        tauFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeClient[0].tcp.conn-40/tau.csv', "pathChangeClient0"))
                        UFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeClient[0].tcp.conn-40/U.csv', "pathChangeClient0"))
                        goodputFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeServer[0].app[0].thread_41/goodput.csv', "pathChangeClient0"))
                        
                        cwndFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeClient[1].tcp.conn-42/cwnd.csv', "pathChangeClient1"))
                        rttFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeClient[1].tcp.conn-42/rtt.csv', "pathChangeClient1"))
                        tauFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeClient[1].tcp.conn-42/tau.csv', "pathChangeClient1"))
                        UFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeClient[1].tcp.conn-42/U.csv', "pathChangeClient1"))
                        goodputFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeServer[1].app[0].thread_43/goodput.csv', "pathChangeClient1"))
                        
                        queueLengthFileList.append((fileStart + '/doubledumbbellpathchange.pathChangeRouter1.ppp[2].queue/queueLength.csv', "pathChangeBottlneckRouter"))
                        
                        
                        aggrPlotsFileList.append((fileStart + '/doubledumbbellpathchange.constantClient[0].tcp.conn-36/cwnd.csv '+ fileStart +'/doubledumbbellpathchange.constantClient[1].tcp.conn-37/cwnd.csv '+ fileStart +'/doubledumbbellpathchange.pathChangeClient[0].tcp.conn-40/cwnd.csv '+ fileStart +'/doubledumbbellpathchange.pathChangeClient[1].tcp.conn-42/cwnd.csv', "aggPlots"))
                        
                        for cwndFile in cwndFileList:
                            processListStr.append(("python3 ../../../../../../../plotCwnd.py " + cwndFile[0], dirPath + cwndFile[1]))
                        
                        for rttFile in rttFileList:
                            processListStr.append(("python3 ../../../../../../../plotRtt.py " + rttFile[0], dirPath + rttFile[1]))
                                
                        for tauFile in tauFileList:
                            processListStr.append(("python3 ../../../../../../../plotTau.py " + tauFile[0], dirPath + tauFile[1]))
                                
                        for UFile in UFileList:
                            processListStr.append(("python3 ../../../../../../../plotU.py " + UFile[0], dirPath + UFile[1]))
                                
                        for goodputFile in goodputFileList:
                            processListStr.append(("python3 ../../../../../../../plotGoodput.py " + goodputFile[0], dirPath + goodputFile[1]))
                                
                        for queueLengthFile in queueLengthFileList:
                            processListStr.append(("python3 ../../../../../../../plotQueueLength.py " + queueLengthFile[0], dirPath + queueLengthFile[1]))
                                
                        for aggrePlotFile in aggrPlotsFileList:
                            processListStr.append(("python3 ../../../../../../../plotCwnd.py " + aggrePlotFile[0], dirPath + aggrePlotFile[1]))
                        # goodputFilePath = '../../paperExperiments/' + experiment + '/csvs/'+ protocol.title() + '/' + buf + '/' + str(rtt) + 'ms/'+ runTitle + str(run) + '/singledumbbell.server[0].app[0].thread_9/goodput.csv'
                        # throughputFilePath = '../../paperExperiments/' + experiment + '/csvs/'+ protocol.title() + '/' + buf + '/' + str(rtt) + 'ms/'+ runTitle + str(run) + '/singledumbbell.server[0].tcp.conn-9/throughput.csv'
                        # queueLengthFilePath = '../../paperExperiments/' + experiment + '/csvs/'+ protocol.title() + '/' + buf + '/' + str(rtt) + 'ms/'+ runTitle + str(run) + '/singledumbbell.router1.ppp[1].queue/queueLength.csv'
                        # if os.path.exists(cwndFilePath) and os.path.exists(goodputFilePath) and os.path.exists(throughputFilePath) and os.path.exists(queueLengthFilePath):
                        #     #subprocess.Popen("mkdir goodput", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
                        #     #subprocess.Popen("mkdir throughput", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
                        #     #subprocess.Popen("mkdir cwnd", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
                        #     #subprocess.Popen("mkdir queueLength", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
                        #     #subprocess.Popen("mkdir rtt", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
                        #     dirPath = 'plots/' + experiment + '/' + protocol + '/' + buf + '/' + str(rtt) + 'ms' + '/run' + str(run) 
                        #     processListStr.append(("python3 ../../../../plotGoodput.py " + "../../../../" + goodputFilePath, dirPath))
                        #     processListStr.append(("python3 ../../../../plotThroughput.py " + "../../../../" + throughputFilePath, dirPath))
                        #     processListStr.append(("python3 ../../../../plotQueueLength.py " + "../../../../" + queueLengthFilePath, dirPath))
                        # else:
                        #     prnt("CSV Entries do not exist! \n")
        print("Plotting current batch!\n")
        while(len(processListStr) > 0):
            processTup = processListStr.pop()
            print(processTup[0] + "\n")
            processList.append(subprocess.Popen(processTup[0], shell=True, cwd=processTup[1], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT))
            currentProc += 1
            if(currentProc >= cores):
                for proc in processList:
                    proc.wait(timeout=300)
                currentProc = 0
                print("Plot batch complete!\n")
                print("Plotting next batch!\n")
                processList.clear()
    currStep += 1
        
