#!/usr/bin/env python

# Runs experiment 9
# runExperiment9
# 

import sys
import random
from pathlib import Path
import os
import subprocess
import time
import re
from PyPDF2 import PdfMerger

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from raynetExperimentSupport import build_simulation_command, simulation_output_kwargs, with_raynet_protocols

def collect_config_entries(paperExperimentDir, congControlList, runList):
    configEntries = []

    for cc in congControlList:
        fileName = paperExperimentDir / ("experiment9_" + cc + ".ini")
        iniFile = open(fileName, 'r').readlines()
        for line in iniFile:
            if line.find('[Config') != -1:
                match = re.search(r'Run(\d{1,5})\]', line)
                if match and int(match.group(1)) in runList:
                    configName = (line[8:])[:-2]
                    configEntries.append((cc, configName))

    return configEntries

def has_expected_vec_file(resultsDir, configName):
    expectedFiles = list(resultsDir.glob(configName + "*.vec"))
    return len(expectedFiles) > 0

def run_config_batch(configEntries, cores, paperExperimentDir):
    currentProc = 0
    processList = []
    failedConfigs = []

    for cc, configName in configEntries:
        resultsDir = paperExperimentDir / "results"
        for staleFile in resultsDir.glob(configName + "*"):
            staleFile.unlink(missing_ok=True)

        processList.append((subprocess.Popen(
            build_simulation_command(cc, "experiment9_" + cc + ".ini", configName, include_leo=True),
            cwd=str(paperExperimentDir), **simulation_output_kwargs(cc)), (cc, configName)))

        currentProc = currentProc + 1
        print("Running simulation [" + configName + "]... (Run #" + str(currentProc) + ")")
        if(currentProc == cores):
            procCompleteNum = 0
            for proc, entry in processList:
                if proc.wait() != 0:
                    failedConfigs.append(entry)
                procCompleteNum = procCompleteNum + 1
                print("\tRun #" + str(procCompleteNum) + " is complete!")
            currentProc = 0
            processList.clear()
            print(" ... Running next batch of simulations! ...\n")

    for proc, entry in processList:
        if proc.wait() != 0:
            failedConfigs.append(entry)

    return failedConfigs

def configs_needing_retry(configEntries, failedConfigs, resultsDir):
    missingConfigs = [entry for entry in configEntries if not has_expected_vec_file(resultsDir, entry[1])]
    for entry in failedConfigs:
        if entry not in missingConfigs:
            missingConfigs.append(entry)
    return missingConfigs

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
    
    startStep = 1
    endStep = 6
    currStep = 1
    cores = int(os.environ.get("EXPERIMENT_CORES", "1"))
    currentProc = 0
    processList = []
    congControlList = with_raynet_protocols(["orbtcp", "cubic", "bbr", "bbr3", "satcp", "leocc"])
    experiment = "experiment9"
    buffersizes = ["mediumbuffer"]
    runs = 5
    runList = list(range(1,runs+1))
    scriptDir = Path(__file__).resolve().parent
    paperExperimentDir = (scriptDir / "../../paperExperiments/experiment9").resolve()
    plotsExperimentDir = (scriptDir / "../../plots/experiment9").resolve()

    city_pairs = [
        ("San Diego", "Seattle", ["isl", "bentpipe"]),
        ("Seattle", "New York", ["isl", "bentpipe"]),
        ("San Diego", "New York", ["isl", "bentpipe"]),
        ("New York", "London", ["isl"]),
        ("San Diego", "Shanghai", ["isl"])
    ]
    
    if(currStep <= endStep and currStep >= startStep): #STEP 1
        subprocess.Popen("python3 generateExperiment9IniFile.py", shell=True).communicate(timeout=30)
        resultsDir = paperExperimentDir / "results"
        os.makedirs(resultsDir, exist_ok=True)

        configEntries = collect_config_entries(paperExperimentDir, congControlList, runList)
        failedConfigs = run_config_batch(configEntries, cores, paperExperimentDir)

        maxRetryRounds = 3
        retryRound = 1
        missingConfigs = configs_needing_retry(configEntries, failedConfigs, resultsDir)

        while(len(missingConfigs) > 0 and retryRound <= maxRetryRounds):
            print("\nMissing vec files for " + str(len(missingConfigs)) + " configs after batch run. Retrying missing configs (attempt " + str(retryRound) + "/" + str(maxRetryRounds) + ")...\n")
            for _, configName in missingConfigs:
                print("Missing vec for [" + configName + "]")

            failedConfigs = run_config_batch(missingConfigs, cores, paperExperimentDir)
            missingConfigs = configs_needing_retry(configEntries, failedConfigs, resultsDir)
            retryRound += 1

        if(len(missingConfigs) > 0):
            missingText = "\n".join("  " + configName for _, configName in missingConfigs)
            raise RuntimeError("The following experiment 9 configs are still missing vec files after retries:\n" + missingText)
    
    currStep += 1
    currentProc = 0
    processList.clear()
    
    if(currStep <= endStep and currStep >= startStep): #STEP 2
        currentProc = 0
        print("\nAll experiments in experiment 9 has been run!\n")
        folderLoc =  '../../paperExperiments/experiment9/results/'
        print("------------ Generating CSV Files for experiment 9 ------------")
        
        fileList = []
        for file in os.listdir(folderLoc):
            if(file.endswith(".vec")):
                f = os.path.join(folderLoc, file)
                processList.append(subprocess.Popen("opp_scavetool export -o "+ "results/"+ file[:-7] + ".csv -F CSV-R " + "results/" + file , shell=True, cwd='../../paperExperiments/experiment9/'))
                currentProc = currentProc + 1
                print("Generating CSV file for [" + file + "]... (Run #" + str(currentProc) + ")")
                fileList.append(file)
                if(currentProc == cores):
                     for proc in processList:
                         proc.wait()
                     currentProc = 0
                    #  for fil in fileList:
                    #     subprocess.Popen("rm results/" + fil , shell=True, cwd='../../paperExperiments/experiment9/').communicate(timeout=10) #Remove VEC
                    #     subprocess.Popen("rm results/" + fil[:-4] + ".vci" , shell=True, cwd='../../paperExperiments/experiment9/').communicate(timeout=10) #Remove VCI
                    #     subprocess.Popen("rm results/" + fil[:-4] + ".sca" , shell=True, cwd='../../paperExperiments/experiment9/').communicate(timeout=10) #Remove VCI
                     fileList.clear()
                     processList.clear()
                     print("     ... Running next batch! ...\n")
        
        for proc in processList:
            proc.wait()
        processList.clear()
        currentProc = 0

        print("CSVs created for experiment 9!\n")

    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 3
        currentProc = 0
        print("Extracting CSV data!!\n")
        print("------------ Extracting CSV Files for experiment 9 ------------")
        processListStr = []
        for protocol in congControlList:
            for buf in buffersizes:
                for city1, city2, modes in city_pairs:
                    city1NoSpace = city1.replace(" ", "")
                    city2NoSpace = city2.replace(" ", "")
                    for mode in modes:
                        for run in runList:
                            filePath = '../../paperExperiments/experiment9/results/'+ protocol.title() + '_' + city1NoSpace + "To" + city2NoSpace + "_" + mode + '_' + buf +'_Run' + str(run) + '.csv'
                            if os.path.exists(filePath):
                                print("Extracting CSV file for " + experiment + " " + protocol.title() + '_' + city1NoSpace + "To" + city2NoSpace + "_" + mode + '_' + buf +'_Run' + str(run))
    
                                processListStr.append("python3 extractSingleCsvFile.py " + filePath + " " + experiment + " " + protocol.title() + ' ' + city1NoSpace+city2NoSpace + " " + mode + ' ' + buf + ' ' + str(run))
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
        processList.clear()
        print("\n-----Generating user terminal plot PDFs for " + experiment + "-----\n")
        os.makedirs(plotsExperimentDir, exist_ok=True)
        plotSingleRunScript = scriptDir / "plotSingleRun.py"

        for protocol in congControlList:
            protocolTitle = protocol.title()
            for buf in buffersizes:
                for city1, city2, modes in city_pairs:
                    sourceDestination = city1.replace(" ", "") + city2.replace(" ", "")
                    for mode in modes:
                        for run in runList:
                            csvRunDir = paperExperimentDir / "csvs" / protocolTitle / sourceDestination / mode / buf / ("run" + str(run))
                            if(not csvRunDir.is_dir()):
                                continue

                            plotRunDir = plotsExperimentDir / protocolTitle / sourceDestination / mode / buf / ("run" + str(run))
                            os.makedirs(plotRunDir, exist_ok=True)
                            processList.append(subprocess.Popen(["python3", str(plotSingleRunScript), str(csvRunDir)], cwd=str(plotRunDir)))
                            currentProc += 1
                            print("Generating merged PDF for [" + protocolTitle + " " + sourceDestination + " " + mode + " " + buf + " run" + str(run) + "]")

                            if(currentProc == cores):
                                for proc in processList:
                                    proc.wait()
                                currentProc = 0
                                processList.clear()

        for proc in processList:
            proc.wait()
        processList.clear()
    currStep += 1
    
    if(currStep <= endStep and currStep >= startStep): #STEP 5
        print("Plotting Heatmap!\n")
        subprocess.Popen("mkdir cumulative", shell=True, cwd='../../plots/experiment9/').communicate(timeout=10)
        time.sleep(3)
        p = subprocess.Popen("python3 ../../../pythonScripts/experiment9/plotHeatmapGoodputRatio.py", shell=True, cwd='../../plots/experiment9/cumulative')
        p.wait(timeout=3600)
        time.sleep(1)
    currStep += 1

    if(currStep <= endStep and currStep >= startStep): #STEP 6
        print("Plotting Heatmap!\n")
        subprocess.Popen("mkdir cumulative", shell=True, cwd='../../plots/experiment9/').communicate(timeout=10)
        time.sleep(3)
        p = subprocess.Popen("python3 ../../../pythonScripts/experiment9/plotHeatmapDelay.py", shell=True, cwd='../../plots/experiment9/cumulative')
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
    #                         dirPath = '../../plots/experiment9/' + protocol + '/' + buf + '/' + str(rtt) + 'ms/DI' + str(di) +'ms/run' + str(run) + '/'
                            
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
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment9/plotCwnd.py " + cwndFile[0], dirPath + cwndFile[1]))
                            
    #                         for rttFile in rttFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment9/plotRtt.py " + rttFile[0], dirPath + rttFile[1]))
                                    
    #                         for UFile in UFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment9/plotU.py " + UFile[0], dirPath + UFile[1]))
                                    
    #                         for goodputFile in goodputFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment9/plotGoodput.py " + goodputFile[0], dirPath + goodputFile[1]))
                                    
    #                         for queueLengthFile in queueLengthFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment9/plotQueueLength.py " + queueLengthFile[0], dirPath + queueLengthFile[1]))
                                    
    #                         for aggrePlotFile in aggrPlotsFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment9/plotCwnd.py " + aggrePlotFile[0], dirPath + aggrePlotFile[1]))
                                
    #                         for aggreGpPlotFile in aggrPlotsGoodputFileList:
    #                             processListStr.append(("python3 ../../../../../../../pythonScripts/experiment9/plotGoodput.py " + aggreGpPlotFile[0], dirPath + aggreGpPlotFile[1]))
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
    #     merge_pdfs_in_folders("../../plots/experiment9")

    # currStep += 1
        
