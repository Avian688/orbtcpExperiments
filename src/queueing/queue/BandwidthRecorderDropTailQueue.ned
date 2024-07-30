//
// Copyright (C) 2020 OpenSim Ltd.
//
// SPDX-License-Identifier: LGPL-3.0-or-later
//


package orbtcpexperiments.queueing.queue;

import inet.queueing.queue.DropTailQueue;
//
// This module is a limited packet queue which drops packets at the tail of the queue.
//
simple BandwidthRecorderDropTailQueue extends DropTailQueue
{
 	@class("inet::queueing::BandwidthRecorderDropTailQueue");
	@signal[bandwidth];
    @statistic[bandwidth](record=vector; interpolationmode=sample-hold);
        
}
