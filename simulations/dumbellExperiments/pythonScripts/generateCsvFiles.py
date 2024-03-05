#!/usr/bin/env python

# Generates csv files for given orbtcp flavours
# generateCsvFiles orbtcp ... orbTcpFlavourN
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
        folderLoc =  '../'+ arg +'/results/'
        print("------------ Generating CSV Files for " + arg + "------------")
        for file in os.listdir(folderLoc):
            if(file.endswith(".vec")):
                f = os.path.join(folderLoc, file)
                processList.append(subprocess.Popen("opp_scavetool export -o "+ folderLoc + file[:-7] + ".csv -F CSV-R " + folderLoc + file , shell=True, cwd='../' + arg))
                currentProc = currentProc + 1
                print("Generating CSV file for [" + file + "]... (Run #" + str(currentProc) + ")")
                if(currentProc == cores):
                     for proc in processList:
                         proc.wait()
                     currentProc = 0
                     processList.clear()
                     print("     ... Running next batch! ...\n")
        
        