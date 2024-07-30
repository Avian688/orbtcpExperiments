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
        fileName =  '../../paperExperiments/experiment2/experiment2' + cc +'.ini'
        iniFile = open(fileName, 'r').readlines()
        print("----------experiment 2 " + cc + " simulations------------")
        for line in iniFile:
            if line.find('[Config') != -1:
                configName = (line[8:])[:-2]
                processList.append(subprocess.Popen("opp_run -r 0 -m -u Cmdenv -c " + configName +" -n ../..:../../../src:../../../../bbr/simulations:../../../../bbr/src:../../../../inet4.4/examples:../../../../inet4.4/showcases:../../../../inet4.4/src:../../../../inet4.4/tests/validation:../../../../inet4.4/tests/networks:../../../../inet4.4/tutorials:../../../../cubic/simulations:../../../../cubic/src:../../../../orbtcp/simulations:../../../../orbtcp/src --image-path=../../../../inet4.4/images -l ../../../src/orbtcpExperiments -l ../../../../bbr/src/bbr -l ../../../../inet4.4/src/INET -l ../../../../cubic/src/cubic -l ../../../../orbtcp/src/orbtcp experiment2" + cc + ".ini", shell=True, cwd='../../paperExperiments/experiment2', stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
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
        
        