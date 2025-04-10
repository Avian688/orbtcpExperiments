package orbtcpexperiments.simulations.paperExperiments.experiment6;
@namespace(inet);

import inet.node.inet.StandardHost;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import inet.node.inet.Router;
import ned.DatarateChannel;
import ned.IBidirectionalChannel;
import inet.common.scenario.ScenarioManager;

network parkinglot
{
    parameters:
        @display("bgb=500,400");
        int numberOfRibFlows = default(3);
    types:
        channel standardLine extends DatarateChannel //look at 
        {
            delay = 0ms;
            datarate = 10Gbps;
        }

        channel bottleneckLine extends DatarateChannel //look at 
        {
            delay = 0ms;
            datarate = 100Mbps;
        }
    submodules:
        spineClient: StandardHost {
            @display("p=50,140");
        }
        spineServer: StandardHost {
            @display("p=400,140");
        }

        ribClient[numberOfRibFlows]: StandardHost {
            @display("p=200,43,m,n,numberOfRibFlows,150");
        }
        ribServer[numberOfRibFlows]: StandardHost {
            @display("p=300,258,m,n,numberOfRibFlows,150");
        }

        router[numberOfRibFlows+1]: Router {
            @display("p=200,140,m,n,numberOfRibFlows,150");
        }

        scenarioManager: ScenarioManager {
            @display("p=100,300;is=s");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=450,350");
        }
    connections:
        spineClient.pppg++ <--> standardLine <--> router[0].pppg++;
        spineServer.pppg++ <--> standardLine <--> router[numberOfRibFlows].pppg++;

        for i=0..sizeof(ribClient)-1 {
            ribClient[i].pppg++ <--> standardLine <--> router[i].pppg++;
            ribServer[i].pppg++ <--> standardLine <--> router[i+1].pppg++;
        }

        for i=0..sizeof(router)-2 {
            router[i].pppg++ <--> bottleneckLine <--> router[i+1].pppg++;
        }

}
