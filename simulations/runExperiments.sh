#!/bin/bash

for flavour in "orbtcp" "orbtcpNoSS";
do
	cd $flavour
	for runName in "OneFlow1ms" "OneFlow25ms" "OneFlow50ms" "OneFlow75ms" "OneFlow100ms" "TwoFlows1ms1ms" "TwoFlows1ms100ms" "TwoFlows25ms25ms" "TwoFlows25ms100ms" "TwoFlows50ms50ms" "TwoFlows50ms100ms" "TwoFlows75ms75ms" "TwoFlows75ms100ms" "TwoFlows100ms100ms" "FiveFlows1ms1ms1ms1ms1ms" "FiveFlows1ms1ms1ms1ms100ms" "FiveFlows1ms1ms1ms100ms100ms" "FiveFlows1ms1ms100ms100ms100ms" "FiveFlows1ms100ms100ms100ms100ms" "FiveFlows1ms25ms50ms75ms100ms" "FiveFlows50ms50ms50ms50ms50ms" "FiveFlows25ms50ms50ms50ms100ms" "FiveFlows25ms50ms50ms50ms100msLateFlow"
	do
		opp_run -r 23 -m -u Cmdenv -c $runName -n ../..:../../../src:../../../../inet4.4/src:../../../../orbtcp/simulations:../../../../orbtcp/src -l ../../../../inet4.4/src/INET -l ../../../../orbtcp/src/orbtcp omnetpp.ini
	done
	cd ..
done