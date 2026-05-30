package orbtcpexperiments.simulations.paperExperiments.experiment0;
@namespace(inet);

import inet.node.inet.StandardHost;
import inet.node.inet.Router;
import inet.networklayer.configurator.ipv4.Ipv4NetworkConfigurator;
import ned.DatarateChannel;
import inet.common.scenario.ScenarioManager;

network singledumbbell
{
    parameters:
        @display("bgb=512,395");
        int numberOfFlows = default(1);
    types:
        channel standardLine extends DatarateChannel
        {
            delay = 8.333333ms;
            datarate = 10Gbps;
            per = 0;
        }

        channel bottleneckLine extends DatarateChannel
        {
            delay = 8.333333ms;
            datarate = 100Mbps;
            per = 0;
        }
    submodules:
        client[numberOfFlows]: StandardHost {
            @display("p=68,71,m,n,numberOfFlows,150");
        }
        configurator: Ipv4NetworkConfigurator {
            @display("p=450,350");
        }
        server[numberOfFlows]: StandardHost {
            @display("p=431,50,m,n,numberOfFlows,150");
        }
        router1: Router {
            @display("p=215,140");
        }
        router2: Router {
            @display("p=327,140");
        }
        scenarioManager: ScenarioManager {
            @display("p=100,300;is=s");
        }
    connections:
        for i=0..sizeof(client)-1 {
            client[i].pppg++ <--> standardLine <--> router1.pppg++;
        }

        for n=0..sizeof(server)-1 {
            server[n].pppg++ <--> standardLine <--> router2.pppg++;
        }

        router1.pppg++ <--> bottleneckLine <--> router2.pppg++;
}
