package orbtcpexperiments.simulations.paperExperiments.experimentTuning;

@namespace(inet);

import inet.common.scenario.ScenarioManager;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import ned.DatarateChannel;
import RLComponents.Broker;
import tcppaced.networklayer.configurator.ipv4.AutoNetworkConfigurator;

network singledumbbell
{
    parameters:
        @display("bgb=512,395");
        int numberOfFlows = default(1);
    types:
        channel accessLine extends DatarateChannel
        {
            delay = 12.25ms;
            datarate = 10Gbps;
        }

        channel bottleneckLine extends DatarateChannel
        {
            delay = 0.5ms;
            datarate = 100Mbps;
        }
    submodules:
        client[numberOfFlows]: StandardHost {
            @display("p=68,71,m,n,numberOfFlows,150");
        }
        configurator: AutoNetworkConfigurator {
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
        //broker: Broker;
    connections:
        for i=0..sizeof(client)-1 {
            client[i].pppg++ <--> accessLine <--> router1.pppg++;
        }

        for i=0..sizeof(server)-1 {
            server[i].pppg++ <--> accessLine <--> router2.pppg++;
        }

        router1.pppg++ <--> bottleneckLine <--> router2.pppg++;
}
