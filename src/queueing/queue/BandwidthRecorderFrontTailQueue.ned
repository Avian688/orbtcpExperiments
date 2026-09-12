// SPDX-License-Identifier: LGPL-3.0-or-later
package orbtcpexperiments.queueing.queue;

simple BandwidthRecorderFrontTailQueue extends BandwidthRecorderDropTailQueue
{
    parameters:
        @class("inet::queueing::BandwidthRecorderDropTailQueue");
        dropperClass = default("inet::queueing::PacketAtCollectionBeginDropper");
}
