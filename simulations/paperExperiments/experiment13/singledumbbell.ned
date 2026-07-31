package orbtcpexperiments.simulations.paperExperiments.experiment13;
@namespace(inet);

import inet.common.scenario.ScenarioManager;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import ned.DatarateChannel;
import tcppaced.networklayer.configurator.ipv4.AutoNetworkConfigurator;

network singledumbbell
{
    parameters:
        @display("bgb=512,395");
    types:
        channel accessLine extends DatarateChannel
        {
            delay = 10ms;
            datarate = 10Gbps;
        }
        channel bottleneckLine extends DatarateChannel
        {
            delay = 10ms;
            datarate = 100Mbps;
        }
    submodules:
        client: StandardHost {
            @display("p=68,71");
        }
        server: StandardHost {
            @display("p=431,50");
        }
        router1: Router {
            @display("p=215,140");
        }
        router2: Router {
            @display("p=327,140");
        }
        configurator: AutoNetworkConfigurator {
            @display("p=450,350");
        }
        scenarioManager: ScenarioManager {
            @display("p=100,300;is=s");
        }
    connections:
        client.pppg++ <--> accessLine <--> router1.pppg++;
        server.pppg++ <--> accessLine <--> router2.pppg++;
        router1.pppg++ <--> bottleneckLine <--> router2.pppg++;
}
