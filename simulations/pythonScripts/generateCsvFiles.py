#!/usr/bin/env python

# Generates csv files for given experiment name
# generateCsvFiles experiment1 ... experimentN
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
        folderLoc =  '../paperExperiments/'+ arg +'/results/'
        print("------------ Generating CSV Files for " + arg + "------------")
        for file in os.listdir(folderLoc):
            if(file.endswith(".vec")):
                f = os.path.join(folderLoc, file)
                processList.append(subprocess.Popen("opp_scavetool export -o "+ "results/"+ file[:-7] + ".csv -F CSV-R " + "results/" + file , shell=True, cwd='../paperExperiments/' + arg))
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
    #subprocess.Popen("find . -depth 1 -type f -not -name '*.csv' -delete", shell=True, cwd='../' + arg + '/results')
        
        