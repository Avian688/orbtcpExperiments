#!/usr/bin/env python3

RAYNET_PROTOCOLS = ["orca", "cleanslate", "astrea"]

CORE_PROTOCOLS = ["cubic", "bbr", "bbr3", "orbtcp", *RAYNET_PROTOCOLS]
LEO_PROTOCOLS = ["cubic", "bbr", "bbr3", "satcp", "orbtcp", "leocc", *RAYNET_PROTOCOLS]
EXPERIMENT_1_PROTOCOLS = ["orbtcp", "bbr", "cubic", "bbr3", "satcp", "leocc", *RAYNET_PROTOCOLS]

PROTOCOL_LABELS = {
    "cubic": "Cubic",
    "bbr": "BBRv1",
    "bbr3": "BBRv3",
    "satcp": "SaTCP",
    "orbtcp": "OrbCC",
    "leocc": "LeoCC",
    "orca": "Orca",
    "cleanslate": "CleanSlate",
    "astrea": "Astrea",
}

PROTOCOL_COLORS = {
    "cubic": "#0C5DA5",
    "bbr": "#00B945",
    "bbr3": "#EB0909",
    "satcp": "#7E2F8E",
    "orbtcp": "#FF9500",
    "leocc": "#17BECF",
    "orca": "#8C564B",
    "cleanslate": "#E377C2",
    "astrea": "#BCBD22",
}

PROTOCOL_REJOIN_COLORS = {
    "cubic": "#6AA4D9",
    "bbr": "#76D98A",
    "bbr3": "#F27A7A",
    "satcp": "#B77CC4",
    "orbtcp": "#FFC46B",
    "leocc": "#77DCE6",
    "orca": "#C49A8F",
    "cleanslate": "#F0A8D7",
    "astrea": "#D9DA74",
}

PROTOCOL_MARKERS = {
    "cubic": "x",
    "bbr": ".",
    "bbr3": "_",
    "satcp": "s",
    "orbtcp": "^",
    "leocc": "D",
    "orca": "o",
    "cleanslate": "v",
    "astrea": "P",
}


def labels_for(protocols):
    return [PROTOCOL_LABELS[p] for p in protocols]


def title_case_folder(protocol):
    return protocol.title()
