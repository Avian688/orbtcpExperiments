#!/usr/bin/env python

# Runs all experiments given the OrbTCP flavour folders
# runExperiments orbtcp ... orbTcpFlavourN
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
    for arg in sys.argv[1:]:
        fileName =  '../'+ arg +'/omnetpp.ini'
        iniFile = open(fileName, 'r').readlines()
        print("------------" + arg + " simulations------------")
        for line in iniFile:
            if line.find('[Config') != -1:
                configName = (line[8:])[:-2]
                processList.append(subprocess.Popen("opp_run -m -u Cmdenv -c " + configName + " -n ../..:../../../src:../../../../inet4.4/src:../../../../orbtcp/simulations:../../../../orbtcp/src -l ../../../../inet4.4/src/INET -l ../../../../orbtcp/src/orbtcp omnetpp.ini", shell=True, cwd='../' + arg, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
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
        
        