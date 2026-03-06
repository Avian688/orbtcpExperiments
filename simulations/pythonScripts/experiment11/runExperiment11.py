#!/usr/bin/env python

# Runs experiment 11
# runExperiment11
# 

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import os
import subprocess
import time
import re
from PyPDF2 import PdfMerger

def merge_pdfs_in_folders(root_folder):
    for protocol in os.listdir(root_folder):
        protocol_path = os.path.join(root_folder, protocol)
        if not os.path.isdir(protocol_path):
            continue
        
        for flowBatch in os.listdir(protocol_path):
            flowBatch_path = os.path.join(protocol_path, flowBatch)
            if not os.path.isdir(flowBatch_path):
                continue
            
            for rtt in os.listdir(flowBatch_path):
                rtt_path = os.path.join(flowBatch_path, rtt)
                if not os.path.isdir(rtt_path):
                    continue
                
                for run in os.listdir(rtt_path):
                    run_path = os.path.join(rtt_path, run)
                    if not os.path.isdir(run_path):
                        continue
                    
                    merger = PdfMerger()
                    module_found = False
                    
                    for module in os.listdir(run_path):
                        module_path = os.path.join(run_path, module)
                        if not os.path.isdir(module_path):
                            continue
                        
                        pdf_files = sorted(Path(module_path).glob("*.pdf"))
                        if not pdf_files:
                            continue
                        
                        module_found = True
                        for pdf_file in pdf_files:
                            merger.append(str(pdf_file))
                    
                    if module_found:
                        output_pdf = os.path.join(run_path, "merged_plots.pdf")
                        merger.write(output_pdf)
                        merger.close()
                        print(f"Merged PDFs into {output_pdf}")

if __name__ == "__main__":
    
    startStep = 5
    endStep = 5
    currStep = 1
    cores = 1
    currentProc = 0
    processList = []
    congControlList = ["orbtcp", "cubic","bbr3", "bbr", "satcp", "leocc"]
    experiment = "experiment11"
    flowBatches = [5, 10, 20]
    clientsRtts = [50]
    runs = 5
    runList = list(range(1,runs+1))

    if(currStep <= endStep and currStep >= startStep): #STEP 1
        subprocess.Popen("python3 generateExperiment11Scenarios.py", shell=True).communicate(timeout=60)
        subprocess.Popen("python3 generateExperiment11IniFile.py", shell=True).communicate(timeout=60)

        subprocess.Popen("rm experiment11runTimes.txt", shell=True).communicate(timeout=30)
        for c in congControlList:
            subprocess.Popen("rm -r ../../paperExperiments/experiment11/csvs/" + c, shell=True).communicate(timeout=30)
            
        with open('experiment11runTimes.txt', 'w') as f1:
            expRunNum = 1
            f1.write("--Experiment 11 Runtimes (s)--")
            for cc in congControlList:
                fileName =  '../../paperExperiments/experiment11/experiment11_' + cc + '.ini'
                if not os.path.exists(fileName):
                    print("Missing ini file " + fileName + ", skipping...")
                    continue
                iniFile = open(fileName, 'r').readlines()
                print("----------experiment 11 " + cc + " simulations------------")
                for line in iniFile:
                    if line.find('[Config') != -1:
                        match = re.search(r'Run(\d{1,5})\]', line)
                        if match and int(match.group(1)) in runList:
                            configName = (line[8:])[:-2]
                            progStart = time.time()
                            processList.append(subprocess.Popen("opp_run -r 0 -m -u Cmdenv -c " + configName +" -n ../..:../../../src:../../../../bbr/simulations:../../../../bbr/src:../../../../inet4.5/examples:../../../../inet4.5/showcases:../../../../inet4.5/src:../../../../inet4.5/tests/validation:../../../../inet4.5/tests/networks:../../../../inet4.5/tutorials:../../../../tcpPaced/src:../../../../tcpPaced/simulations:../../../../cubic/simulations:../../../../cubic/src:../../../../orbtcp/simulations:../../../../orbtcp/src:../../../../satcp/simulations:../../../../satcp/src:../../../../leocc/simulations:../../../../leocc/src:../../../../tcpGoodputApplications/simulations:../../../../tcpGoodputApplications/src --image-path=../../../../inet4.5/images -l ../../../src/orbtcpExperiments -l ../../../../bbr/src/bbr -l ../../../../inet4.5/src/INET -l ../../../../tcpPaced/src/tcpPaced -l ../../../../cubic/src/cubic -l ../../../../orbtcp/src/orbtcp -l ../../../../satcp/src/satcp -l ../../../../leocc/src/leocc -l ../../../../tcpGoodputApplications/src/tcpGoodputApplications experiment11_" + cc + ".ini", shell=True, cwd='../../paperExperiments/experiment11', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                            currentProc = currentProc + 1
                            print("Running simulation [" + configName + "]... (Run #" + str(currentProc) + ")")
                            if(currentProc == cores):
                                procCompleteNum = 0
                                for proc in processList:
                                    proc.wait()
                                    now = time.time()
                                    f1.write("Run "+ str(expRunNum) + ": " + str(now-progStart))
                                    procCompleteNum = procCompleteNum + 1
                                    print("\tRun #" + str(procCompleteNum) + " is complete!")
                                    expRunNum += 1
                                currentProc = 0
                                processList.clear()
                                print(" ... Running next batch of simulations! ...\n")
                        else:
                            continue
        
        for proc in processList:
            proc.wait()
        time.sleep(5)
    currStep += 1
    currentProc = 0
    processList.clear()
    
    if(currStep <= endStep and currStep >= startStep): #STEP 2
        currentProc = 0
        print("\nAll experiments in Experiment 11 has been run!\n")
        folderLoc =  '../../paperExperiments/experiment11/results/'
        print("------------ Generating CSV Files for experiment 11 ------------")
        
        fileList = []
        for file in os.listdir(folderLoc):
            if(file.endswith(".vec")):
                f = os.path.join(folderLoc, file)
                processList.append(subprocess.Popen("opp_scavetool export -o "+ "results/"+ file[:-7] + ".csv -F CSV-R " + "results/" + file , shell=True, cwd='../../paperExperiments/experiment11/'))
                currentProc = currentProc + 1
                print("Generating CSV file for [" + file + "]... (Run #" + str(currentProc) + ")")
                fileList.append(file)
                if(currentProc == cores):
                     for proc in processList:
                         proc.wait()
                     currentProc = 0
                     fileList.clear()
                     processList.clear()
                     print("     ... Running next batch! ...\n")
        
        for proc in processList:
            proc.wait()
        processList.clear()
        currentProc = 0
        time.sleep(5)
    print("CSVs created for experiments 11!\n")
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 3
        currentProc = 0
        print("Extracting CSV data!!\n")
        print("------------ Extracting CSV Files for experiment 11------------")
        processListStr = []
        for protocol in congControlList:
            for flowBatch in flowBatches:
                for rtt in clientsRtts:
                    for run in runList:
                        filePath = '../../paperExperiments/experiment11/results/'+ protocol.title() + '_' + str(flowBatch) + 'flows_' + str(rtt) + 'ms_Run' + str(run) + '.csv'
                        print(filePath)
                        if os.path.exists(filePath):
                             print("Extracting CSV file for " + experiment + " " + protocol + " " + str(flowBatch) + "flows " + str(rtt) + " " + str(run))
                             processListStr.append("python3 extractSingleCsvFile.py " + filePath + " " + experiment + " " + protocol + " " + str(flowBatch) + "flows " + str(rtt) + " " + str(run))
        
        currentProc = 0
        time.sleep(5)
        while(len(processListStr) > 0):
            process = processListStr.pop()
            print(process + "\n")
            processList.append(subprocess.Popen(process, shell=True))
            currentProc += 1
            if(currentProc >= cores):
                for proc in processList:
                    proc.wait(timeout=1800)
                currentProc = 0
                print("Csv Extraction batch complete!\n")
                print("Extracting next batch!\n")
                processList.clear()
        for proc in processList:
            proc.wait(timeout=1800)
        processList.clear()
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 4
        subprocess.Popen("mkdir ../../plots/experiment11", shell=True).communicate(timeout=10) 
        subprocess.Popen("rm -r *", shell=True, cwd='../../plots/experiment11').communicate(timeout=200) 
        
        print("\n-----Making plot directories for " + experiment + "-----\n")
        subprocess.Popen("mkdir " + experiment, shell=True, cwd='../../plots/').communicate(timeout=10)
        for cc in congControlList:
            print("\n-----Making plot directories for " + cc + "-----\n")
            subprocess.Popen("mkdir " + cc, shell=True, cwd='../../plots/' + experiment + '/').communicate(timeout=10)
            
            for flowBatch in flowBatches:
                batchFolder = str(flowBatch) + "flows"
                for rtt in clientsRtts:
                    for run in runList:
                        subprocess.Popen("mkdir " + str(batchFolder), shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' ).communicate(timeout=10)
                        subprocess.Popen("mkdir " + str(rtt) + 'ms', shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + batchFolder).communicate(timeout=10)
                        subprocess.Popen("mkdir run" + str(run), shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + batchFolder + '/' + str(rtt) + 'ms').communicate(timeout=10)
                        
                        for i in range(flowBatch):
                            subprocess.Popen("mkdir client" + str(i+1), shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + batchFolder + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
                        subprocess.Popen("mkdir router", shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + batchFolder + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
                        subprocess.Popen("mkdir aggPlots", shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + batchFolder + '/' + str(rtt) + 'ms/run' + str(run)).communicate(timeout=10)
        time.sleep(5)
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 5
        print("Plotting Scatter Util vs Delay!\n")
        subprocess.Popen("mkdir cumulative", shell=True, cwd='../../plots/experiment11/').communicate(timeout=10)
        time.sleep(3)
        p = subprocess.Popen("python3 ../../../pythonScripts/experiment11/plotScatterUtilDelay.py", shell=True, cwd='../../plots/experiment11/cumulative')
        p.wait(timeout=3600)
        time.sleep(1)
    currStep += 1

    if(currStep <= endStep and currStep >= startStep): #STEP 6
        print("\nPlotting!")
        processListStr = []
        for protocol in congControlList:
            for flowBatch in flowBatches:
                batchFolder = str(flowBatch) + "flows"
                for rtt in clientsRtts:
                    for run in runList:
                        dirPath = '../../plots/experiment11/' + protocol + '/' + batchFolder + '/' + str(rtt) + 'ms' + '/run' + str(run) + '/'
                        
                        runTitle = "run"
                        goodputFileList = []
                        throughputFileList = []
                        cwndFileList = []
                        queueLengthFileList = []
                        rttFileList = []
                        inflightFileList = []
                        aggrCwndFileList = []
                        aggrGoodputFileList = []
                        
                        fileBeg = 'paperExperiments/'+ experiment + '/csvs/'+ protocol + '/' + batchFolder + '/' + str(rtt) + 'ms/'+ runTitle + str(run)
                        fileStart = "../../../../../../../" + fileBeg

                        for i in range(flowBatch):
                            goodputFileList.append((fileStart + '/singledumbbell.server[' + str(i) + '].app[0]/goodput.csv', 'client' + str(i+1)))
                            throughputFileList.append((fileStart + '/singledumbbell.client[' + str(i) + '].tcp.conn/throughput.csv', 'client' + str(i+1)))
                            cwndFileList.append((fileStart + '/singledumbbell.client[' + str(i) + '].tcp.conn/cwnd.csv', 'client' + str(i+1)))
                            rttFileList.append((fileStart + '/singledumbbell.client[' + str(i) + '].tcp.conn/rtt.csv', 'client' + str(i+1)))
                            inflightFileList.append((fileStart + '/singledumbbell.client[' + str(i) + '].tcp.conn/mbytesInFlight.csv', 'client' + str(i+1)))

                        queueLengthFileList.append((fileStart + '/singledumbbell.router1.ppp[' + str(flowBatch) + '].queue/queueLength.csv', 'router'))

                        aggCwnd = ""
                        aggGoodput = ""
                        for i in range(flowBatch):
                            aggCwnd = aggCwnd + fileStart + '/singledumbbell.client[' + str(i) + '].tcp.conn/cwnd.csv'
                            aggGoodput = aggGoodput + fileStart + '/singledumbbell.server[' + str(i) + '].app[0]/goodput.csv'
                            if(i < flowBatch-1):
                                aggCwnd = aggCwnd + " "
                                aggGoodput = aggGoodput + " "
                        aggrCwndFileList.append((aggCwnd, "aggPlots"))
                        aggrGoodputFileList.append((aggGoodput, "aggPlots"))
                        
                        for goodputFile in goodputFileList:
                            processListStr.append(("python3 ../../../../../../../pythonScripts/experiment11/plotGoodput.py " + goodputFile[0], dirPath + goodputFile[1]))
                        
                        for throughputFile in throughputFileList:
                            if os.path.exists("../../../pythonScripts/experiment11/plotThroughput.py"):
                                processListStr.append(("python3 ../../../../../../../pythonScripts/experiment11/plotThroughput.py " + throughputFile[0], dirPath + throughputFile[1]))
                                
                        for cwndFile in cwndFileList:
                            processListStr.append(("python3 ../../../../../../../pythonScripts/experiment11/plotCwnd.py " + cwndFile[0], dirPath + cwndFile[1]))
                        
                        for queueLengthFile in queueLengthFileList:
                            processListStr.append(("python3 ../../../../../../../pythonScripts/experiment11/plotQueueLength.py " + queueLengthFile[0], dirPath + queueLengthFile[1]))
                        
                        for rttFile in rttFileList:
                            processListStr.append(("python3 ../../../../../../../pythonScripts/experiment11/plotRtt.py " + rttFile[0], dirPath + rttFile[1]))
                        
                        for inflightFile in inflightFileList:
                            if os.path.exists("../../../pythonScripts/experiment11/plotBytesInFlight.py"):
                                processListStr.append(("python3 ../../../../../../../pythonScripts/experiment11/plotBytesInFlight.py " + inflightFile[0], dirPath + inflightFile[1]))
                        
                        for aggrePlotFile in aggrCwndFileList:
                            processListStr.append(("python3 ../../../../../../../pythonScripts/experiment11/plotCwnd.py " + aggrePlotFile[0], dirPath + aggrePlotFile[1]))
                        
                        for aggreGpPlotFile in aggrGoodputFileList:
                            processListStr.append(("python3 ../../../../../../../pythonScripts/experiment11/plotGoodput.py " + aggreGpPlotFile[0], dirPath + aggreGpPlotFile[1]))

        print("Plotting current batch!\n")
        while(len(processListStr) > 0):
            processTup = processListStr.pop()
            print(processTup[0] + "\n")
            processList.append(subprocess.Popen(processTup[0], shell=True, cwd=processTup[1]))
            currentProc += 1
            if(currentProc >= cores):
                for proc in processList:
                    proc.wait(timeout=1200)
                currentProc = 0
                print("Plot batch complete!\n")
                print("Plotting next batch!\n")
                processList.clear()
        for proc in processList:
            proc.wait(timeout=1200)
        processList.clear()
    currStep += 1
    

    if(currStep <= endStep and currStep >= startStep): #STEP 7
        print("\n Attempting to merge PDFs!\n")
        merge_pdfs_in_folders("../../plots/experiment11")

    currStep += 1

    if(currStep <= endStep and currStep >= startStep): #STEP 8
        print("\nExperiment 11 complete!\n")
        print("Protocols: " + str(congControlList))
        print("Flow batches: " + str(flowBatches))
        print("RTTs: " + str(clientsRtts))
        print("Runs: " + str(runs))