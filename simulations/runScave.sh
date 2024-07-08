#!/bin/bash

for flavour in "orbtcp" "orbtcpNoSS" "cubic";
do
	echo "Creating csv files for $flavour..."
	cd $flavour/results
	find . -name "*.csv" -type f -delete
	fileName=""
	for i in *.vec;
	do
		fileName="${i%????}"
		opp_scavetool export -o "$fileName.csv" -F CSV-R "$fileName.vec"
	done
	cd ../..
done

#opp_scavetool export -o results/FiveFlows25ms50ms50ms50ms100msLateFlow-0.05,0.95-#0.csv  -F CSV-R results/FiveFlows25ms50ms50ms50ms100msLateFlow-0.05,0.95-#0.vec
