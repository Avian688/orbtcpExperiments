#!/usr/bin/env python

# Clears result folders given the OrbTCP flavour folders
# clearResults orbtcp ... orbTcpFlavourN
# Aiden Valentine

import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import random
from pathlib import Path
import os
import shutil
import subprocess
           
if __name__ == "__main__":
    cores = 4
    for arg in sys.argv[1:]:
        folderLoc =  '../'+ arg +'/results/'
        print("------------ Clearing results for " + arg + "------------")
        #clear folders
        processNestedList = []
        processFolderNameList = []
        dir = '../pythonResults/' + arg 
        for filename in os.listdir(dir):
            file_path = os.path.join(dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))
