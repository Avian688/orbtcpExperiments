package orbtcpexperiments.simulations.paperExperiments.experimentSensitivityAnalysis;

@namespace(inet);

import inet.common.scenario.ScenarioManager;
import inet.node.inet.Router;
import inet.node.inet.StandardHost;
import ned.DatarateChannel;
import tcppaced.networklayer.configurator.ipv4.AutoNetworkConfigurator;

network dualdumbbell
{
    parameters:
        @display("bgb=760,430");
        int numberOfFlows = default(1);
    types:
        channel accessLine extends DatarateChannel
        {
            delay = 1ms;
            datarate = 10Gbps;
        }

        channel transitLine extends DatarateChannel
        {
            delay = 1ms;
            datarate = 10Gbps;
        }

        channel bottleneckLine extends DatarateChannel
        {
            delay = 1ms;
            datarate = 100Mbps;
        }
    submodules:
        client[numberOfFlows]: StandardHost {
            @display("p=70,90,m,n,numberOfFlows,150");
        }
        ingress: Router {
            @display("p=245,215");
        }
        transitA: Router {
            @display("p=390,130");
        }
        transitB: Router {
            @display("p=390,300");
        }
        egress: Router {
            @display("p=535,215");
        }
        server[numberOfFlows]: StandardHost {
            @display("p=700,90,m,n,numberOfFlows,150");
        }
        configurator: AutoNetworkConfigurator {
            @display("p=650,390");
        }
        scenarioManager: ScenarioManager {
            @display("p=110,390;is=s");
        }
    connections:
        for i=0..sizeof(client)-1 {
            client[i].pppg++ <--> accessLine <--> ingress.pppg++;
        }

        for i=0..sizeof(server)-1 {
            server[i].pppg++ <--> accessLine <--> egress.pppg++;
        }

        ingress.pppg++ <--> transitLine <--> transitA.pppg++;
        transitA.pppg++ <--> bottleneckLine <--> egress.pppg++;

        ingress.pppg++ <--> transitLine <--> transitB.pppg++;
        transitB.pppg++ <--> bottleneckLine <--> egress.pppg++;
}
