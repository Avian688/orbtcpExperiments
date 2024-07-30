//
// Copyright (C) 2020 OpenSim Ltd.
//
// SPDX-License-Identifier: LGPL-3.0-or-later
//


#ifndef __ORBTCPEXPERIMENTS_BANDWIDTHRECORDERDROPTAILQUEUE_H
#define __ORBTCPEXPERIMENTS_BANDWIDTHRECORDERDROPTAILQUEUE_H

#include "inet/queueing/queue/PacketQueue.h"

namespace inet {
namespace queueing {

class BandwidthRecorderDropTailQueue : public PacketQueue {
protected:
    static simsignal_t bandwidthSignal;

    simtime_t bandwidthRecorderTimer;
    cMessage *bandwidthRecorderTimerMsg = nullptr;

    bool isActive;

protected:
    virtual void initialize(int stage) override;
    virtual void handleMessage(cMessage *message) override;
    virtual void processTimer();
    virtual void scheduleTimer();

};

} // namespace queueing
} // namespace inet

#endif

