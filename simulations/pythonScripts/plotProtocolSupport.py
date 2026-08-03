#!/usr/bin/env python3

import os


RAYNET_PROTOCOLS = []

PLOT_VARIANT_ENV = "ORBTCP_PLOT_VARIANT"
PLOT_VARIANT_MAIN = "pint"
PLOT_VARIANT_COMPARISON = "with_orbtcp"

CORE_PROTOCOLS_FINAL = ["cubic", "bbr", "bbr3", "orbtcp_pint", *RAYNET_PROTOCOLS]
CORE_PROTOCOLS_WITH_ORBTCP = ["cubic", "bbr", "bbr3", "orbtcp_pint", "orbtcp", *RAYNET_PROTOCOLS]
LEO_PROTOCOLS_FINAL = ["cubic", "bbr", "bbr3", "satcp", "orbtcp_pint", "leocc", *RAYNET_PROTOCOLS]
LEO_PROTOCOLS_WITH_ORBTCP = ["cubic", "bbr", "bbr3", "satcp", "orbtcp_pint", "orbtcp", "leocc", *RAYNET_PROTOCOLS]
EXPERIMENT_1_PROTOCOLS_FINAL = ["orbtcp_pint", "bbr", "cubic", "bbr3", "satcp", "leocc", *RAYNET_PROTOCOLS]
EXPERIMENT_1_PROTOCOLS_WITH_ORBTCP = ["orbtcp_pint", "orbtcp", "bbr", "cubic", "bbr3", "satcp", "leocc", *RAYNET_PROTOCOLS]


def current_plot_variant():
    variant = os.environ.get(PLOT_VARIANT_ENV, PLOT_VARIANT_MAIN).strip().lower()
    if variant not in {PLOT_VARIANT_MAIN, PLOT_VARIANT_COMPARISON}:
        raise ValueError(
            f"Unsupported {PLOT_VARIANT_ENV}={variant!r}; expected "
            f"{PLOT_VARIANT_MAIN!r} or {PLOT_VARIANT_COMPARISON!r}"
        )
    return variant


def _select_protocols(final_protocols, comparison_protocols):
    return comparison_protocols if current_plot_variant() == PLOT_VARIANT_COMPARISON else final_protocols


# Main figures represent the final PINT design. The comparison variant adds
# full-INT OrbCC alongside it for direct protocol comparison.
CORE_PROTOCOLS = _select_protocols(CORE_PROTOCOLS_FINAL, CORE_PROTOCOLS_WITH_ORBTCP)
LEO_PROTOCOLS = _select_protocols(LEO_PROTOCOLS_FINAL, LEO_PROTOCOLS_WITH_ORBTCP)
EXPERIMENT_1_PROTOCOLS = _select_protocols(
    EXPERIMENT_1_PROTOCOLS_FINAL,
    EXPERIMENT_1_PROTOCOLS_WITH_ORBTCP,
)

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
    "orbtcp_pint": "#FF9500",
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
    "orbtcp_pint": "#FFC46B",
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
