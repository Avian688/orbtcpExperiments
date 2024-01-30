#!/bin/bash

echo "Plotting CC results for $flavour..."
for i in *.csv;
do
	folderName="${i%????}"
	folderNameClean=${folderName//[^[:alnum:]]/}
	cd ../../pythonResults/$flavour
	if [ -d "$folderNameClean" ]; then
  		 rm -rf $folderNameClean
	fi
	mkdir $folderNameClean
	cd $folderNameClean

	csvFile="../../../$flavour/results/$i"
	python3 ../../../pythonScripts/plotCwnd.py $csvFile
	python3 ../../../pythonScripts/plotU.py $csvFile

	python3 ../../../pythonScripts/plotUsmoothed.py $csvFile
	python3 ../../../pythonScripts/plotAdditiveIncrease.py $csvFile

	python3 ../../../pythonScripts/plotRtt.py $csvFile
	python3 ../../../pythonScripts/plotAvgRtt.py $csvFile
	python3 ../../../pythonScripts/plotEstimatedRtt.py $csvFile

	python3 ../../../pythonScripts/plotThroughput.py $csvFile

	python3 ../../../pythonScripts/plotQueueLength.py $csvFile

	cd ..

done