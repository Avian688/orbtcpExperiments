#!/bin/bash

python3 ../../../pythonScripts/plotCwnd.py $1
python3 ../../../pythonScripts/plotU.py $1

python3 ../../../pythonScripts/plotUsmoothed.py $1
python3 ../../../pythonScripts/plotAdditiveIncrease.py $1

python3 ../../../pythonScripts/plotRtt.py $1
python3 ../../../pythonScripts/plotAvgRtt.py $1
python3 ../../../pythonScripts/plotEstimatedRtt.py $1

python3 ../../../pythonScripts/plotThroughput.py $1

python3 ../../../pythonScripts/plotQueueLength.py $1