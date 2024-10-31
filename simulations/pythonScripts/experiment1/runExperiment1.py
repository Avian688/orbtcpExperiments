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
           
if __name__ == "__main__":
    cores = 4
    currentProc = 0
    processList = []
    congControlList = ["bbr", "cubic", "orbtcp"]
    for cc in congControlList:
        fileName =  '../../paperExperiments/experiment1/experiment1' + cc +'.ini'
        iniFile = open(fileName, 'r').readlines()
        print("----------experiment 1 " + cc + " simulations------------")
        for line in iniFile:
            if line.find('[Config') != -1:
                configName = (line[8:])[:-2]
                processList.append(subprocess.Popen("opp_run -r 0 -m -u Cmdenv -c " + configName +" -n ../..:../../../src:../../../../bbr/simulations:../../../../bbr/src:../../../../inet4.5/examples:../../../../inet4.5/showcases:../../../../inet4.5/src:../../../../inet4.5/tests/validation:../../../../inet4.5/tests/networks:../../../../inet4.5/tutorials:../../../../tcpPaced/src:../../../../tcpPaced/simulations:../../../../cubic/simulations:../../../../cubic/src:../../../../orbtcp/simulations:../../../../orbtcp/src:../../../../tcpGoodputApplications/simulations:../../../../tcpGoodputApplications/src --image-path=../../../../inet4.5/images -l ../../../src/orbtcpExperiments -l ../../../../bbr/src/bbr -l ../../../../inet4.5/src/INET -l ../../../../tcpPaced/src/tcpPaced -l ../../../../cubic/src/cubic -l ../../../../orbtcp/src/orbtcp -l ../../../../tcpGoodputApplications/src/tcpGoodputApplications experiment1" + cc + ".ini", shell=True, cwd='../../paperExperiments/experiment1', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                currentProc = currentProc + 1
                print("Running simulation [" + configName + "]... (Run #" + str(currentProc) + ")")
                if(currentProc == cores):
                    procCompleteNum = 0
                    for proc in processList:
                        proc.wait()
                        procCompleteNum = procCompleteNum + 1
                        print("\tRun #" + str(procCompleteNum) + " is complete!")
                    currentProc = 0
                    processList.clear()
                    print(" ... Running next batch of simulations! ...\n")
        
        