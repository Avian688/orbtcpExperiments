package orbtcpexperiments.simulations.paperExperiments.experiment3;

@namespace(inet);

import inet.node.inet.StandardHost;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import orbtcp.networklayer.configurator.ipv4.Ipv4NetworkConfiguratorUpdate;
import inet.node.inet.Router;
import ned.DatarateChannel;
import ned.IBidirectionalChannel;
import inet.common.scenario.ScenarioManager;

network doubledumbbellpathchange
{
    parameters:
        @display("bgb=512,395");
        int numberOfConstantFlows = default(1);
        int numberOfPathChangeFlows = default(1);
    types:
        channel standardLine extends DatarateChannel
        {
            delay = 1ms;
            datarate = 1Gbps;
            int weight @mutable = 1;
        }

        channel bottleneckLine extends DatarateChannel
        {
            delay = 0.5ms;
            datarate = 100 Mbps;
            int weight @mutable = 1;
        }

        channel unusedLine extends DatarateChannel //Not used by flows (used to establish link gates for path change)
        {
            delay = 200ms;
            datarate = 1Gbps;
            int weight @mutable = 2;
        }
    submodules:
        constantClient[numberOfConstantFlows]: StandardHost {
            @display("p=68,71,m,n,numberOfConstantFlows,40");
        }
        constantServer[numberOfConstantFlows]: StandardHost {
            @display("p=431,50,m,n,numberOfConstantFlows,40");
        }
        pathChangeClient[numberOfPathChangeFlows]: StandardHost {
            @display("p=61,350,m,n,numberOfPathChangeFlows,70");
        }
        pathChangeServer[numberOfPathChangeFlows]: StandardHost {
            @display("p=463,350,m,n,numberOfPathChangeFlows,70");
        }
        constantRouter1: Router {
            @display("p=215,140");
        }
        constantRouter2: Router {
            @display("p=327,140");
        }
        pathChangeRouter1: Router {
            @display("p=215,350");
        }
        pathChangeRouter2: Router {
            @display("p=327,350");
        }
        scenarioManager: ScenarioManager {
            @display("p=100,300;is=s");
        }
        configurator: Ipv4NetworkConfiguratorUpdate{
            @display("p=494,17");
        }
    connections:
        for i=0..sizeof(constantClient)-1 {
            constantClient[i].pppg++ <--> standardLine <--> constantRouter1.pppg++;
        }

        for n=0..sizeof(constantServer)-1 {
            constantServer[n].pppg++ <--> standardLine <--> constantRouter2.pppg++;
        }

        constantRouter1.pppg++ <--> bottleneckLine <--> constantRouter2.pppg++;

        for j=0..sizeof(pathChangeClient)-1 {
            pathChangeClient[j].pppg++ <--> standardLine <--> pathChangeRouter1.pppg++;
        }

        for k=0..sizeof(pathChangeServer)-1 {
            pathChangeServer[k].pppg++ <--> standardLine <--> pathChangeRouter2.pppg++;
        }

        pathChangeRouter1.pppg++ <--> bottleneckLine <--> pathChangeRouter2.pppg++;

        for l=0..sizeof(pathChangeClient)-1 {
            pathChangeClient[l].pppg++ <--> unusedLine <--> constantRouter1.pppg++;
        }

        for m=0..sizeof(pathChangeServer)-1 {
            pathChangeServer[m].pppg++ <--> unusedLine <--> constantRouter2.pppg++;
        }

}
