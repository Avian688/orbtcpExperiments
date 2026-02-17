#!/usr/bin/env python

# Runs experiment 1
# runExperiment1
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
        
        for buffer in os.listdir(protocol_path):
            buffer_path = os.path.join(protocol_path, buffer)
            if not os.path.isdir(buffer_path):
                continue
            
            for rtt in os.listdir(buffer_path):
                rtt_path = os.path.join(buffer_path, rtt)
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
    
    startStep = 8
    endStep = 8
    currStep = 1
    cores = 5
    currentProc = 0
    processList = []
    congControlList = ["orbtcp", "cubic", "bbr", "bbr3"]
    experiment = "experiment10"
    runs = 5
    runList = list(range(1,runs+1))

    listPairs = ["Pair1", "Pair2", "Pair3"]
    
    if(currStep <= endStep and currStep >= startStep): #STEP 1
        subprocess.Popen("python3 generateexperiment10IniFile.py", shell=True).communicate(timeout=30)
        exp1RunNum = 1
        for cc in congControlList:
            fileName =  '../../paperExperiments/experiment10/experiment10_' + cc + '.ini'
            iniFile = open(fileName, 'r').readlines()
            print("----------experiment 10 " + cc + " simulations------------")
            for line in iniFile:
                if line.find('[Config') != -1:
                    match = re.search(r'Run(\d{1,5})\]', line)
                    if match and int(match.group(1)) in runList:
                        configName = (line[8:])[:-2]
                        print(configName)
                        progStart = time.time()
                        processList.append(subprocess.Popen("opp_run -r 0 -m -u Cmdenv -c " + configName +" -n ../..:../../../src:../../../../bbr/simulations:../../../../bbr/src:../../../../inet4.5/examples:../../../../inet4.5/showcases:../../../../inet4.5/src:../../../../inet4.5/tests/validation:../../../../inet4.5/tests/networks:../../../../inet4.5/tutorials:../../../../tcpGoodputApplications/simulations:../../../../tcpGoodputApplications/src:../../../../tcpPaced/src:../../../../tcpPaced/simulations:../../../../cubic/simulations:../../../../cubic/src:../../../../leosatellites/src:../../../../leosatellites/simulations:../../../../os3/simulations:../../../../os3/src:../../../../orbtcp/simulations:../../../../orbtcp/src --image-path=../../../../inet4.5/images:../../../../os3/images -l ../../../src/orbtcpExperiments -l ../../../../bbr/src/bbr -l ../../../../inet4.5/src/INET -l ../../../../tcpGoodputApplications/src/tcpGoodputApplications -l ../../../../tcpPaced/src/tcpPaced -l ../../../../cubic/src/cubic -l ../../../../leosatellites/src/leosatellites -l ../../../../os3/src/os3 -l ../../../../orbtcp/src/orbtcp  experiment10_" + cc + ".ini", shell=True, cwd='../../paperExperiments/experiment10', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                        
                        currentProc = currentProc + 1
                        print("Running simulation [" + configName + "]... (Run #" + str(currentProc) + ")")
                        if(currentProc == cores):
                            procCompleteNum = 0
                            for proc in processList:
                                proc.wait()
                                now = time.time()
                                procCompleteNum = procCompleteNum + 1
                                print("\tRun #" + str(procCompleteNum) + " is complete!")
                                exp1RunNum += 1
                            currentProc = 0
                            processList.clear()
                            print(" ... Running next batch of simulations! ...\n")
                    else:
                        continue
    
        for proc in processList:
            proc.wait()
    
    currStep += 1
    currentProc = 0
    processList.clear()
    
    if(currStep <= endStep and currStep >= startStep): #STEP 2
        currentProc = 0
        print("\nAll experiments in experiment 10 has been run!\n")
        folderLoc =  '../../paperExperiments/experiment10/results/'
        print("------------ Generating CSV Files for experiment 10 ------------")
        
        fileList = []
        for file in os.listdir(folderLoc):
            if(file.endswith(".vec")):
                f = os.path.join(folderLoc, file)
                processList.append(subprocess.Popen("opp_scavetool export -o "+ "results/"+ file[:-7] + ".csv -F CSV-R " + "results/" + file , shell=True, cwd='../../paperExperiments/experiment10/'))
                currentProc = currentProc + 1
                print("Generating CSV file for [" + file + "]... (Run #" + str(currentProc) + ")")
                fileList.append(file)
                if(currentProc == cores):
                     for proc in processList:
                         proc.wait()
                     currentProc = 0
                    #  for fil in fileList:
                    #     subprocess.Popen("rm results/" + fil , shell=True, cwd='../../paperExperiments/experiment10/').communicate(timeout=10) #Remove VEC
                    #     subprocess.Popen("rm results/" + fil[:-4] + ".vci" , shell=True, cwd='../../paperExperiments/experiment10/').communicate(timeout=10) #Remove VCI
                    #     subprocess.Popen("rm results/" + fil[:-4] + ".sca" , shell=True, cwd='../../paperExperiments/experiment10/').communicate(timeout=10) #Remove VCI
                     fileList.clear()
                     processList.clear()
                     print("     ... Running next batch! ...\n")
        
        for proc in processList:
            proc.wait()
        processList.clear()
        currentProc = 0

        print("CSVs created for experiment 10!\n")

    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 3
        currentProc = 0
        print("Extracting CSV data!!\n")
        print("------------ Extracting CSV Files for experiment 10------------")
        processListStr = []
        for protocol in congControlList:
            for pair in listPairs:
                for run in runList:
                    filePath = '../../paperExperiments/experiment10/results/'+ protocol.title() + '_' + pair + '_Run' + str(run) + '.csv'
                    if os.path.exists(filePath):
                        print("Extracting CSV file for " + experiment + " " + protocol.title() + '_' + pair + '_Run' + str(run))

                        processListStr.append("python3 extractSingleCsvFile.py " + filePath + " " + experiment + " " + protocol.title() + ' ' + pair + " " + str(run))
        time.sleep(10)
        currentProc = 0
        while(len(processListStr) > 0):
            process = processListStr.pop()
            print(process + "\n")
            processList.append(subprocess.Popen(process, shell=True))
            currentProc += 1
            if(currentProc >= cores):
                for proc in processList:
                    proc.wait(timeout=4000)
                currentProc = 0
                print("Csv Extraction batch complete!\n")
                print("Extracting next batch!\n")
                processList.clear()               
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 4
        currentProc = 0
        print("Extracting CSV data!!\n")
        print("------------ Extracting Ping CSV Files for experiment 8------------")
        processListStr = []
        filePath = '../../paperExperiments/experiment10/results/ping_isl.csv'
        if os.path.exists(filePath):
            print("Extracting CSV file for " + experiment + " Ping" )
            processListStr.append("python3 extractSingleCsvFilePing.py " + filePath + " " + experiment + " " + "isl" + " ")
        time.sleep(10)
        currentProc = 0
        while(len(processListStr) > 0):
            process = processListStr.pop()
            print(process + "\n")
            processList.append(subprocess.Popen(process, shell=True))
            currentProc += 1
            if(currentProc >= cores):
                for proc in processList:
                    proc.wait(timeout=4000)
                currentProc = 0
                print("Csv Extraction batch complete!\n")
                print("Extracting next batch!\n")
                processList.clear()               
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 4
    #     subprocess.Popen("mkdir ../../plots/experiment10", shell=True).communicate(timeout=10) 
         print("\n-----Making plot directories for " + experiment + "-----\n")
         subprocess.Popen("mkdir " + experiment, shell=True, cwd='../../plots/').communicate(timeout=10)
    #     for cc in congControlList:
    #         print("\n-----Making plot directories for " + cc + "-----\n")
    #         subprocess.Popen("mkdir " + cc, shell=True, cwd='../../plots/' + experiment + '/').communicate(timeout=10)
            
    #         for buf in buffersizes:
    #             for rtt in rtts:
    #                 for di in disruptionIntervals:
    #                     for run in runList:
    #                         subprocess.Popen("mkdir " + str(buf), shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' ).communicate(timeout=10)
    #                         subprocess.Popen("mkdir " + str(rtt) + 'ms', shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + buf).communicate(timeout=10)
    #                         subprocess.Popen("mkdir DI" + str(di) + 'ms', shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms').communicate(timeout=10)
    #                         subprocess.Popen("mkdir run" + str(run), shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms' + '/DI' + str(di) + 'ms').communicate(timeout=10)
                            
    #                         subprocess.Popen("mkdir client", shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/DI ' + str(di) + 'ms/run' + str(run)).communicate(timeout=10)
    #                         subprocess.Popen("mkdir server", shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/DI ' + str(di) + 'ms/run' + str(run)).communicate(timeout=10)
    #                         subprocess.Popen("mkdir router1", shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/DI ' + str(di) + 'ms/run' + str(run)).communicate(timeout=10)
    #                         subprocess.Popen("mkdir router2", shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/DI ' + str(di) + 'ms/run' + str(run)).communicate(timeout=10)
    #                         subprocess.Popen("mkdir aggPlots", shell=True, cwd='../../plots/' + experiment + '/' + cc + '/' + buf + '/' + str(rtt) + 'ms/DI ' + str(di) + 'ms/run' + str(run)).communicate(timeout=10)
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 5
        print("Plotting Heatmap!\n")
        subprocess.Popen("mkdir cumulative", shell=True, cwd='../../plots/experiment10/').communicate(timeout=10)
        time.sleep(3)
        p = subprocess.Popen("python3 ../../../pythonScripts/experiment10/plotHeatmapGoodputRatio.py", shell=True, cwd='../../plots/experiment10/cumulative')
        p.wait(timeout=3600)
        time.sleep(1)
    currStep += 1

    if(currStep <= endStep and currStep >= startStep): #STEP 6
        print("Plotting Goodput evolution!\n")
        subprocess.Popen("mkdir cumulative", shell=True, cwd='../../plots/experiment10/').communicate(timeout=10)
        time.sleep(3)
        p = subprocess.Popen("python3 ../../../pythonScripts/experiment10/plotGoodputEvolution.py", shell=True, cwd='../../plots/experiment10/cumulative')
        p.wait(timeout=3600)
        time.sleep(1)
    currStep += 1

    if(currStep <= endStep and currStep >= startStep): #STEP 7
        print("Printing average RTT!\n")
        subprocess.Popen("mkdir cumulative", shell=True, cwd='../../plots/experiment10/').communicate(timeout=10)
        time.sleep(3)
        p = subprocess.Popen("python3 ../../../pythonScripts/experiment10/plotHeatmapDelay.py", shell=True, cwd='../../plots/experiment10/cumulative')
        p.wait(timeout=3600)
        time.sleep(1)
    currStep += 1
    
    #if(currStep <= endStep and currStep >= startStep): #STEP 7
    #     print("\nPlotting!")
    #     processListStr = []
    #     for protocol in congControlList:
    #         for buf in buffersizes:
    #             for rtt in rtts:
    #                 for di in disruptionIntervals:
    #                     for run in runList:
    #                         #print("\nCurrently on Run#" + str(run) + " \n")
    #                         dirPath = '../../plots/experiment10/' + protocol + '/' + buf + '/' + str(rtt) + 'ms/DI' + str(di) +'ms/run' + str(run) + '/'
                            
    #                         runTitle = "run"
    #                         fileBeg = 'paperExperiments/'+ experiment + '/csvs/'+ protocol + '/' + buf + '/' + str(rtt) + 'ms/DI' + str(di) +'ms/run' + str(run) + '/'
    #                         fileStart = "../../../../../../../" + fileBeg
    #                         cwndFileList = []
    #                         rttFileList = []
    #                         tauFileList = []
    #                         UFileList = []
    #                         goodputFileList = []
    #                         throughputFileList = []
    #                         queueLengthFileList = []
    #                         aggrPlotsFileList = []
    #                         aggrPlotsGoodputFileList = []
                            
    #                         file_mappings = [
    #                             ("client", "server", "router")
    #                         ]
    
    #                         for client_type, server_type, router_type in file_mappings:
    #                             prefix = f"{fileStart}/singledumbbell.{client_type}[0].tcp.conn"
    #                             label = f"{client_type}"
                                
    #                             cwndFileList.append((f"{prefix}/cwnd.csv", label))
    #                             rttFileList.append((f"{prefix}/rtt.csv", label))
                                
    #                             #if(protocol == "orbtcp"):
    #                                 #UFileList.append((f"{prefix}/U.csv", label))
                                
    #                             goodputFileList.append((f"{fileStart}/singledumbbell.{server_type}[{i}].app[0]/goodput.csv", label))
                                
    #                             queueLengthFileList.append((f"{fileStart}/singledumbbell.{router_type}1.ppp[1].queue/queueLength.csv", router_type))
    
                            
                            
    #                         aggrPlotsFileList.append((fileStart + '/singledumbbell.client[0].tcp.conn/cwnd.csv', "aggPlots"))
                            
    #                         aggrPlotsGoodputFileList.append((fileStart + '/singledumbbell.server[0].app[0]/goodput.csv', "aggPlots"))
                            
    #                         for cwndFile in cwndFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment10/plotCwnd.py " + cwndFile[0], dirPath + cwndFile[1]))
                            
    #                         for rttFile in rttFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment10/plotRtt.py " + rttFile[0], dirPath + rttFile[1]))
                                    
    #                         for UFile in UFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment10/plotU.py " + UFile[0], dirPath + UFile[1]))
                                    
    #                         for goodputFile in goodputFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment10/plotGoodput.py " + goodputFile[0], dirPath + goodputFile[1]))
                                    
    #                         for queueLengthFile in queueLengthFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment10/plotQueueLength.py " + queueLengthFile[0], dirPath + queueLengthFile[1]))
                                    
    #                         for aggrePlotFile in aggrPlotsFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment10/plotCwnd.py " + aggrePlotFile[0], dirPath + aggrePlotFile[1]))
                                
    #                         for aggreGpPlotFile in aggrPlotsGoodputFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment10/plotGoodput.py " + aggreGpPlotFile[0], dirPath + aggreGpPlotFile[1]))
    #                         # goodputFilePath = '../../paperExperiments/' + experiment + '/csvs/'+ protocol.title() + '/' + buf + '/' + str(rtt) + 'ms/'+ runTitle + str(run) + '/singledumbbell.server[0].app[0].thread_9/goodput.csv'
    #                         # throughputFilePath = '../../paperExperiments/' + experiment + '/csvs/'+ protocol.title() + '/' + buf + '/' + str(rtt) + 'ms/'+ runTitle + str(run) + '/singledumbbell.server[0].tcp.conn-9/throughput.csv'
    #                         # queueLengthFilePath = '../../paperExperiments/' + experiment + '/csvs/'+ protocol.title() + '/' + buf + '/' + str(rtt) + 'ms/'+ runTitle + str(run) + '/singledumbbell.router1.ppp[1].queue/queueLength.csv'
    #                         # if os.path.exists(cwndFilePath) and os.path.exists(goodputFilePath) and os.path.exists(throughputFilePath) and os.path.exists(queueLengthFilePath):
    #                         #     #subprocess.Popen("mkdir goodput", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
    #                         #     #subprocess.Popen("mkdir throughput", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
    #                         #     #subprocess.Popen("mkdir cwnd", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
    #                         #     #subprocess.Popen("mkdir queueLength", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
    #                         #     #subprocess.Popen("mkdir rtt", shell=True, cwd='plots/'+ exp + '/' + protocol +'/run' + str(run) + '/', stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT).communicate(timeout=10) 
    #                         #     dirPath = 'plots/' + experiment + '/' + protocol + '/' + buf + '/' + str(rtt) + 'ms' + '/run' + str(run) 
    #                         #     processListStr.append(("python3 ../../../../plotGoodput.py " + "../../../../" + goodputFilePath, dirPath))
    #                         #     processListStr.append(("python3 ../../../../plotThroughput.py " + "../../../../" + throughputFilePath, dirPath))
    #                         #     processListStr.append(("python3 ../../../../plotQueueLength.py " + "../../../../" + queueLengthFilePath, dirPath))
    #                         # else:
    #                         #     prnt("CSV Entries do not exist! \n")
    #     print("Plotting current batch!\n")
    #     while(len(processListStr) > 0):
    #         processTup = processListStr.pop()
    #         processList.append(subprocess.Popen(processTup[0], shell=True, cwd=processTup[1]))
    #         procName = processTup[0]
    #         #print(procName)
    #         if "csvs/" in procName:
    #             procName = procName.split("csvs/")[-1]
    #         parts = procName.strip().split("/")
    #         # Extract key details
    #         protocol = parts[0]
    #         queue_size = parts[1]
    #         rtt = parts[2]
    #         disruption_interval = parts[3]
    #         run_number = parts[4]
    #         module = parts[5].split(".")[0]  # Get module name before '.'
    #         metric = parts[-1]  # Last part is the recorded value
    #         # Format the output
    #         formatted_output = f"Plotting {protocol} {queue_size} {rtt} {disruption_interval} {run_number} {module} {metric}"
    #         print(formatted_output)
        
    #         #print("Plotting " + formatted_output)
            
    #         currentProc += 1
    #         if(currentProc >= cores):
    #             for proc in processList:
    #                 proc.wait(timeout=500)
    #             currentProc = 0
    #             print("Plot batch complete!\n")
    #             print("Plotting next batch!\n")
    #             processList.clear()
    # currStep += 1

    # if(currStep <= endStep and currStep >= startStep): #STEP 8
    #     print("\n Attempting to merge PDFs!\n")
    #     merge_pdfs_in_folders("../../plots/experiment10")

    # currStep += 1
        
