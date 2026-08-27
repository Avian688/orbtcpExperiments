#!/usr/bin/env python3

import os


RAYNET_PROTOCOLS = []

PLOT_VARIANT_ENV = "ORBTCP_PLOT_VARIANT"
PLOT_VARIANT_MAIN = "pint"
PLOT_VARIANT_COMPARISON = "with_orbtcp"
PLOT_BBRV1_ENV = "ORBTCP_PLOT_BBRV1"
PLOT_BBRV1_WITH = "with_bbrv1"
PLOT_BBRV1_WITHOUT = "without_bbrv1"
FINAL_ORBCC_PROTOCOL = "orbtcp_pint"
FULL_INT_ORBCC_PROTOCOL = "orbtcp"
FINAL_ORBCC_LABEL = "OrbCC"
FULL_INT_REFERENCE_LABEL = "Full INT reference"

CORE_PROTOCOLS_FINAL = ["cubic", "bbr", "bbr3", *RAYNET_PROTOCOLS, "orbtcp_pint"]
CORE_PROTOCOLS_WITH_ORBTCP = ["cubic", "bbr", "bbr3", *RAYNET_PROTOCOLS, "orbtcp", "orbtcp_pint"]
LEO_PROTOCOLS_FINAL = ["cubic", "bbr", "bbr3", "satcp", "leocc", *RAYNET_PROTOCOLS, "orbtcp_pint"]
LEO_PROTOCOLS_WITH_ORBTCP = ["cubic", "bbr", "bbr3", "satcp", "leocc", *RAYNET_PROTOCOLS, "orbtcp", "orbtcp_pint"]
EXPERIMENT_1_PROTOCOLS_FINAL = ["bbr", "cubic", "bbr3", "satcp", "leocc", *RAYNET_PROTOCOLS, "orbtcp_pint"]
EXPERIMENT_1_PROTOCOLS_WITH_ORBTCP = ["bbr", "cubic", "bbr3", "satcp", "leocc", *RAYNET_PROTOCOLS, "orbtcp", "orbtcp_pint"]


def current_plot_variant():
    variant = os.environ.get(PLOT_VARIANT_ENV, PLOT_VARIANT_MAIN).strip().lower()
    if variant not in {PLOT_VARIANT_MAIN, PLOT_VARIANT_COMPARISON}:
        raise ValueError(
            f"Unsupported {PLOT_VARIANT_ENV}={variant!r}; expected "
            f"{PLOT_VARIANT_MAIN!r} or {PLOT_VARIANT_COMPARISON!r}"
        )
    return variant


def current_bbrv1_plot_variant():
    variant = os.environ.get(PLOT_BBRV1_ENV, PLOT_BBRV1_WITH).strip().lower()
    if variant not in {PLOT_BBRV1_WITH, PLOT_BBRV1_WITHOUT}:
        raise ValueError(
            f"Unsupported {PLOT_BBRV1_ENV}={variant!r}; expected "
            f"{PLOT_BBRV1_WITH!r} or {PLOT_BBRV1_WITHOUT!r}"
        )
    return variant


def filter_bbrv1_plot_protocols(protocols):
    protocols = list(protocols)
    if current_bbrv1_plot_variant() == PLOT_BBRV1_WITHOUT:
        return [protocol for protocol in protocols if protocol != "bbr"]
    return protocols


def _select_protocols(final_protocols, comparison_protocols):
    protocols = (
        comparison_protocols
        if current_plot_variant() == PLOT_VARIANT_COMPARISON
        else final_protocols
    )
    return filter_bbrv1_plot_protocols(protocols)


def _validate_protocol_sets(name, final_protocols, comparison_protocols):
    if FULL_INT_ORBCC_PROTOCOL in final_protocols:
        raise RuntimeError(f"{name} main plots must not include full-INT OrbCC")
    if FINAL_ORBCC_PROTOCOL not in final_protocols:
        raise RuntimeError(f"{name} main plots must include the final OrbCC implementation")
    if final_protocols[-1] != FINAL_ORBCC_PROTOCOL:
        raise RuntimeError(f"{name} main plots must place OrbCC last")
    if comparison_protocols[-1] != FINAL_ORBCC_PROTOCOL:
        raise RuntimeError(f"{name} comparison plots must place OrbCC last")
    for protocol in (FINAL_ORBCC_PROTOCOL, FULL_INT_ORBCC_PROTOCOL):
        if protocol not in comparison_protocols:
            raise RuntimeError(
                f"{name} comparison plots must include {protocol}"
            )


for _name, _final_protocols, _comparison_protocols in (
    ("core", CORE_PROTOCOLS_FINAL, CORE_PROTOCOLS_WITH_ORBTCP),
    ("LEO", LEO_PROTOCOLS_FINAL, LEO_PROTOCOLS_WITH_ORBTCP),
    (
        "experiment 1/2",
        EXPERIMENT_1_PROTOCOLS_FINAL,
        EXPERIMENT_1_PROTOCOLS_WITH_ORBTCP,
    ),
):
    _validate_protocol_sets(_name, _final_protocols, _comparison_protocols)


# Main figures use the final OrbCC implementation (the internal orbtcp_pint
# result key). The comparison variant adds the legacy full-INT reference.
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
    "orbtcp": FULL_INT_REFERENCE_LABEL,
    "orbtcp_pint": FINAL_ORBCC_LABEL,
    "leocc": "LeoCC",
    "orca": "Orca",
    "cleanslate": "CleanSlate",
    "astrea": "Astrea",
}

# Canonical Experiment 1/2 palette. All protocol-comparison plots should use
# these values rather than Matplotlib's positional colour cycle.
PROTOCOL_COLORS = {
    "cubic": "#0C5DA5",
    "bbr": "#17BECF",
    "bbr3": "#EB0909",
    "satcp": "#00B945",
    "orbtcp": "#777777",
    "orbtcp_pint": "#FF9500",
    "leocc": "#7E2F8E",
    "orca": "#8C564B",
    "cleanslate": "#E377C2",
    "astrea": "#BCBD22",
}

COMPACT_PROTOCOL_LEGEND_FONTSIZE = 8
HEATMAP_FONT_SIZE = 40
HEATMAP_CELL_FONT_SIZE = 25
HEATMAP_COLORBAR_TICK_FONT_SIZE = 27
HEATMAP_PATH_LABEL_FONT_SIZE = 28

# Keep protocol labels consistent across the LEO heatmaps. In particular, the
# fairness plots should not rotate labels to compensate for a smaller font.
HEATMAP_PROTOCOL_TICK_STYLE = {
    "rotation": 0,
    "ha": "center",
    "fontsize": 22,
    "fontstyle": "normal",
}


def compact_protocol_legend_kwargs(protocols):
    return {
        "ncol": max(1, len(protocols)),
        "frameon": False,
        "fontsize": COMPACT_PROTOCOL_LEGEND_FONTSIZE,
        "columnspacing": 0.65,
        "handlelength": 1.0,
        "handletextpad": 0.3,
        "labelspacing": 0.1,
        "borderaxespad": 0.0,
    }

PROTOCOL_REJOIN_COLORS = {
    "cubic": "#6AA4D9",
    "bbr": "#77DCE6",
    "bbr3": "#F27A7A",
    "satcp": "#76D98A",
    "orbtcp": "#B5B5B5",
    "orbtcp_pint": "#FFC46B",
    "leocc": "#B77CC4",
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
