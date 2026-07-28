#!/usr/bin/env python3

RAYNET_PROTOCOLS = ["orca", "cleanslate", "astrea"]

CORE_PROTOCOLS = ["cubic", "bbr", "bbr3", "orbtcp", "orbtcp_pint", *RAYNET_PROTOCOLS]
LEO_PROTOCOLS = ["cubic", "bbr", "bbr3", "satcp", "orbtcp", "orbtcp_pint", "leocc", *RAYNET_PROTOCOLS]
EXPERIMENT_1_PROTOCOLS = ["orbtcp", "orbtcp_pint", "bbr", "cubic", "bbr3", "satcp", "leocc", *RAYNET_PROTOCOLS]

PROTOCOL_LABELS = {
    "cubic": "Cubic",
    "bbr": "BBRv1",
    "bbr3": "BBRv3",
    "satcp": "SaTCP",
    "orbtcp": "OrbCC",
    "orbtcp_pint": "OrbCC-PINT",
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
    "orbtcp_pint": "#C44E00",
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
    "orbtcp_pint": "#E89A67",
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
    "orbtcp_pint": "h",
    "leocc": "D",
    "orca": "o",
    "cleanslate": "v",
    "astrea": "P",
}


def labels_for(protocols):
    return [PROTOCOL_LABELS[p] for p in protocols]


def title_case_folder(protocol):
    if protocol.lower() == "orbtcp_pint":
        return "OrbtcpPint"
    return protocol.title()
