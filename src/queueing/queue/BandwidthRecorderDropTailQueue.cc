//
// Copyright (C) 2020 OpenSim Ltd.
//
// SPDX-License-Identifier: LGPL-3.0-or-later
//

#include <inet/networklayer/common/NetworkInterface.h>
#include "BandwidthRecorderDropTailQueue.h"

namespace inet {
namespace queueing {

Define_Module(BandwidthRecorderDropTailQueue);

simsignal_t BandwidthRecorderDropTailQueue::bandwidthSignal = cComponent::registerSignal("bandwidth");

void BandwidthRecorderDropTailQueue::initialize(int stage)
{
    PacketQueue::initialize(stage);
    isActive = true;
    bandwidthRecorderTimer = SimTime(500, SIMTIME_MS);
    if (stage == INITSTAGE_TRANSPORT_LAYER) {
        bandwidthRecorderTimerMsg = new cMessage("bandwidthRecorderTimerMsg");
        bandwidthRecorderTimerMsg->setContextPointer(this);
        scheduleTimer();
    }
}

void BandwidthRecorderDropTailQueue::handleMessage(cMessage *message)
{
    if (message == bandwidthRecorderTimerMsg) {
        processTimer();
    }
    else{
        auto packet = check_and_cast<Packet *>(message);
        pushPacket(packet, packet->getArrivalGate());
    }
}

void BandwidthRecorderDropTailQueue::processTimer()
{
    if(isActive){
        if(!dynamic_cast<NetworkInterface*>(getParentModule())->getRxTransmissionChannel()){
            EV_DEBUG << "\n Channel has been deactivated!" << endl;
            isActive = false;
            return;
        }
        else{
            cSimpleModule::emit(bandwidthSignal, dynamic_cast<NetworkInterface*>(getParentModule())->getRxTransmissionChannel()->getNominalDatarate());
        }
        scheduleTimer();
    }
}

void BandwidthRecorderDropTailQueue::scheduleTimer()
{
    if(!bandwidthRecorderTimerMsg->isScheduled()){
        scheduleAt(simTime()+bandwidthRecorderTimer, bandwidthRecorderTimerMsg);
    }
}




} // namespace queueing
} // namespace inet

