#!/usr/bin/env python3

import argparse
import csv
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SIMULATIONS_DIR = SCRIPT_DIR.parent.parent
PAPER_EXPERIMENT_DIR = SIMULATIONS_DIR / "paperExperiments" / "experiment8"
RESULTS_DIR = PAPER_EXPERIMENT_DIR / "results"
PING_CSV_ROOT = PAPER_EXPERIMENT_DIR / "csvs" / "ping"
INI_FILE = PAPER_EXPERIMENT_DIR / "experiment8_ping.ini"
GROUND_STATIONS_CSV = SCRIPT_DIR / "ground_stations.csv"

SIM_TIME_LIMIT = "30s"
PING_START_TIME = "0s"
PING_INTERVAL = "50ms"
PING_PACKET_SIZE = "1B"

BASE_CITY_GROUND_STATIONS = [
    ("SanDiego", "San Diego", 32.7157, -117.1611),
    ("Seattle", "Seattle", 47.6062, -122.3321),
    ("NewYork", "New York", 40.7128, -74.0060),
    ("London", "London", 51.5074, -0.1278),
    ("Shanghai", "Shanghai", 31.2304, 121.4737),
]

PING_TERMINALS = BASE_CITY_GROUND_STATIONS + [
    ("Lawrence", "Lawrence, KS", 39.014, -95.149),
    ("StJohns", "St John's, Canada", 47.561, -52.775),
]

CITY_TO_TERMINAL = {city_key: idx for idx, (city_key, _, _, _) in enumerate(PING_TERMINALS)}

# Keep these app indexes stable: the delay heatmap scripts use them to find
# the baseline RTT for each source/destination pair.
PING_APPS = {
    "SanDiego": [
        ("Seattle", 0),
        ("NewYork", 1),
        ("Shanghai", 2),
    ],
    "Seattle": [
        ("NewYork", 0),
    ],
    "NewYork": [
        ("London", 0),
        ("StJohns", 1),
    ],
    "Lawrence": [
        ("NewYork", 0),
    ],
}

MODE_CONFIGS = {
    "isl": {
        "config": "PingIsl",
        "output_base": "pingIsl",
        "enable_isl": "true",
    },
    "bentpipe": {
        "config": "PingBentPipe",
        "output_base": "pingBentPipe",
        "enable_isl": "false",
    },
}

NED_PATH = (
    "../..:"
    "../../../src:"
    "../../../../bbr/simulations:"
    "../../../../bbr/src:"
    "../../../../inet4.5/examples:"
    "../../../../inet4.5/showcases:"
    "../../../../inet4.5/src:"
    "../../../../inet4.5/tests/validation:"
    "../../../../inet4.5/tests/networks:"
    "../../../../inet4.5/tutorials:"
    "../../../../tcpGoodputApplications/simulations:"
    "../../../../tcpGoodputApplications/src:"
    "../../../../tcpPaced/src:"
    "../../../../tcpPaced/simulations:"
    "../../../../cubic/simulations:"
    "../../../../cubic/src:"
    "../../../../leosatellites/src:"
    "../../../../leosatellites/simulations:"
    "../../../../os3/simulations:"
    "../../../../os3/src:"
    "../../../../orbtcp/simulations:"
    "../../../../orbtcp/src:"
    "../../../../leocc/simulations:"
    "../../../../leocc/src"
)

IMAGE_PATH = "../../../../inet4.5/images:../../../../os3/images"

LIBRARIES = [
    "../../../src/orbtcpExperiments",
    "../../../../bbr/src/bbr",
    "../../../../inet4.5/src/INET",
    "../../../../tcpGoodputApplications/src/tcpGoodputApplications",
    "../../../../tcpPaced/src/tcpPaced",
    "../../../../cubic/src/cubic",
    "../../../../leosatellites/src/leosatellites",
    "../../../../os3/src/os3",
    "../../../../orbtcp/src/orbtcp",
    "../../../../leocc/src/leocc",
]


def write_line(handle, line=""):
    handle.write(line + "\n")


def load_extra_ground_stations():
    if not GROUND_STATIONS_CSV.exists():
        raise FileNotFoundError(f"Missing ground stations CSV: {GROUND_STATIONS_CSV}")

    with GROUND_STATIONS_CSV.open(newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def generate_ping_ini():
    extra_ground_stations = load_extra_ground_stations()
    num_ground_stations = len(BASE_CITY_GROUND_STATIONS) + len(extra_ground_stations)

    PAPER_EXPERIMENT_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    with INI_FILE.open("w", encoding="utf-8") as f:
        write_line(f, "[General]")
        write_line(f, "network = leoconstellation")
        write_line(f, f"sim-time-limit = {SIM_TIME_LIMIT}")
        write_line(f, "record-eventlog=false")
        write_line(f, "cmdenv-express-mode = true")
        write_line(f, "cmdenv-redirect-output = false")
        write_line(f, "cmdenv-output-file = dctcpLog.txt")
        write_line(f, "cmdenv-log-prefix = %t | %m |")
        write_line(f, "cmdenv-event-banners = false")
        write_line(f, "**.cmdenv-log-level = off")
        write_line(f)
        write_line(f, "**.rtt:vector.vector-recording = true")
        write_line(f, "**.pingTxSeq:vector.vector-recording = true")

        write_line(f, "result-dir = results")
        write_line(f, "**.scalar-recording=false")
        write_line(f, "**.vector-recording=false")
        write_line(f, "**.bin-recording=false")
        write_line(f)

        write_line(f, "**.constraintAreaMinX = 0m")
        write_line(f, "**.constraintAreaMaxX = 2160m")
        write_line(f, "**.constraintAreaMinY = 0m")
        write_line(f, "**.constraintAreaMaxY = 1080m")
        write_line(f, "**.constraintAreaMinZ = 0m")
        write_line(f, "**.constraintAreaMaxZ = 0m")
        write_line(f)

        write_line(f, '*.*.ipv4.typename = "LeoIpv4NetworkLayer"')
        write_line(f, '**.ipv4.configurator.typename = "LeoIpv4NodeConfigurator"')
        write_line(f, '*.*.ipv4.arp.typename = "GlobalArp"')
        write_line(f, '*.*.ipv4.routingTable.netmaskRoutes = ""')
        write_line(f, '**.groundStation[*].mobility.typename = "GroundStationMobility"')
        write_line(f, "*.groundStation[*].mobility.initFromDisplayString = false")
        write_line(f, "*.groundStation[*].mobility.updateFromDisplayString  = false")
        write_line(f, '**.userTerminal[*].mobility.typename = "GroundStationMobility"')
        write_line(f, "*.userTerminal[*].mobility.initFromDisplayString = false")
        write_line(f, "*.userTerminal[*].mobility.updateFromDisplayString  = false")
        write_line(f)

        write_line(
            f,
            "*.configurator.config = xml(\"<config><interface hosts='**' address='10.x.x.x' "
            "netmask='255.x.x.x'/><autoroute metric='delay'/></config>\")",
        )
        write_line(f, "*.configurator.addStaticRoutes = true")
        write_line(f, "*.configurator.optimizeRoutes = false")
        write_line(f, "*.*.forwarding = true")
        write_line(f)

        write_line(f, '*.visualizer.dataLinkVisualizer.packetFilter = "*"')
        write_line(f, "*.visualizer.networkRouteVisualizer.displayRoutes = true")
        write_line(f, '*.visualizer.networkRouteVisualizer.packetFilter = "*"')
        write_line(f, '*.visualizer.routingTableVisualizer.destinationFilter = "*"')
        write_line(f, '*.visualizer.statisticVisualizer.sourceFilter = "**.app[*]"')
        write_line(f, '*.visualizer.statisticVisualizer.signalName = "rtt"')
        write_line(f, '*.visualizer.statisticVisualizer.unit = "s"')
        write_line(f)

        write_line(f, '**.ppp[*].ppp.queue.typename = "DropTailQueue"')
        write_line(f, "**.ppp[*].ppp.queue.packetCapacity = 300")
        write_line(f)

        write_line(f, "**.satellite[*].NoradModule.satIndex = parentIndex()")
        write_line(f, '**.satellite[*].NoradModule.satName = "Starlink Satellite"')
        write_line(f, "**.satellite[*].**.bitrate = 100Mbps")
        write_line(f, '**.satellite[*].mobility.typename = "SatelliteMobility"')
        write_line(f, "**.satellite[*].mobility.updateInterval = 100ms")
        write_line(f)

        write_line(f, "**.numOfSats = 1584")
        write_line(f, "**.satsPerPlane = 22")
        write_line(f, "**.numOfPlanes = 72")
        write_line(f, "**.incl = 53")
        write_line(f, "**.satellite[*].NoradModule.inclination = 53*0.0174533")
        write_line(f, "**.alt = 550")
        write_line(f, "**.satellite[*].NoradModule.altitude = 550")
        write_line(f, f"**.numOfGS = {num_ground_stations}")
        write_line(f, f"**.numOfUserTerminals = {len(PING_TERMINALS)}")
        write_line(f, "**.numOfClients = 0")
        write_line(f, "**.numberOfFlows = 1")
        write_line(f, "**.dataRate = 100Mbps")
        write_line(f, "**.queueSize = 300")
        write_line(f, "**.loadFiles = true")
        write_line(f, "**.userTerminalUpdateInterval = 5s")
        write_line(f)

        for idx, (_, label, latitude, longitude) in enumerate(BASE_CITY_GROUND_STATIONS):
            write_line(f, f"# {label} Ground Station")
            write_line(f, f'**.groundStation[{idx}].cityName = "{label}"')
            write_line(f, f"**.groundStation[{idx}].mobility.latitude = {latitude}")
            write_line(f, f"**.groundStation[{idx}].mobility.longitude = {longitude}")
            write_line(f)

        start_idx = len(BASE_CITY_GROUND_STATIONS)
        for offset, entry in enumerate(extra_ground_stations):
            idx = start_idx + offset
            latitude = entry["Latitude"]
            longitude = entry["Longitude"]
            name = entry["Location Comment"]
            write_line(f, f"# {name} Ground Station")
            write_line(f, f'**.groundStation[{idx}].cityName = "{name}"')
            write_line(f, f"**.groundStation[{idx}].mobility.latitude = {latitude}")
            write_line(f, f"**.groundStation[{idx}].mobility.longitude = {longitude}")
            write_line(f)

        for idx, (city_key, label, latitude, longitude) in enumerate(PING_TERMINALS):
            apps = PING_APPS.get(city_key, [])
            write_line(f, f"# {label} User Terminal")
            write_line(f, f'**.userTerminal[{idx}].terminalName = "{label} UT"')
            write_line(f, f"**.userTerminal[{idx}].mobility.latitude = {latitude}")
            write_line(f, f"**.userTerminal[{idx}].mobility.longitude = {longitude}")
            write_line(f, f"**.userTerminal[{idx}].numApps = {len(apps)}")
            for dest_city, app_index in apps:
                dest_index = CITY_TO_TERMINAL[dest_city]
                write_line(f, f'**.userTerminal[{idx}].app[{app_index}].typename = "PingApp"')
                write_line(f, f'**.userTerminal[{idx}].app[{app_index}].destAddr = "userTerminal[{dest_index}]"')
                write_line(f, f"**.userTerminal[{idx}].app[{app_index}].startTime = {PING_START_TIME}")
                write_line(f, f"**.userTerminal[{idx}].app[{app_index}].stopTime = {SIM_TIME_LIMIT}")
                write_line(f, f"**.userTerminal[{idx}].app[{app_index}].sendInterval = {PING_INTERVAL}")
                write_line(f, f"**.userTerminal[{idx}].app[{app_index}].packetSize = {PING_PACKET_SIZE}")
                write_line(f, f"**.userTerminal[{idx}].app[{app_index}].printPing = false")
            write_line(f)

        for mode, mode_config in MODE_CONFIGS.items():
            write_line(f, f"[Config {mode_config['config']}]")
            write_line(f, "extends = General")
            write_line(f, f"**.enableInterSatelliteLinks = {mode_config['enable_isl']}")
            write_line(f, f"output-vector-file = results/{mode_config['output_base']}.vec")
            write_line(f, f"output-scalar-file = results/{mode_config['output_base']}.sca")
            write_line(f, f"description = \"Experiment 8 {mode} user-terminal ping baseline\"")
            write_line(f)

    print(f"Generated {INI_FILE}")


def require_tool(tool_name):
    if shutil.which(tool_name) is None:
        raise RuntimeError(f"Required command not found on PATH: {tool_name}")


def opp_run_command(config_name):
    command = [
        "opp_run",
        "-r",
        "0",
        "-m",
        "-u",
        "Cmdenv",
        "-c",
        config_name,
        "-n",
        NED_PATH,
        f"--image-path={IMAGE_PATH}",
    ]

    for library in LIBRARIES:
        command.extend(["-l", library])

    command.append(INI_FILE.name)
    return command


def run_ping_configs(modes):
    require_tool("opp_run")

    processes = []
    for mode in modes:
        mode_config = MODE_CONFIGS[mode]
        print(f"Starting {mode_config['config']}...")
        process = subprocess.Popen(
            opp_run_command(mode_config["config"]),
            cwd=PAPER_EXPERIMENT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        processes.append((mode, mode_config["config"], process))

    failures = []
    for mode, config_name, process in processes:
        return_code = process.wait()
        if return_code == 0:
            print(f"{config_name} complete.")
        else:
            failures.append((config_name, return_code))

    if failures:
        failed = ", ".join(f"{name} returned {code}" for name, code in failures)
        raise RuntimeError(f"Ping simulation failed: {failed}")


def find_vector_file(mode):
    mode_config = MODE_CONFIGS[mode]
    output_base = mode_config["output_base"]
    config_name = mode_config["config"]
    patterns = [
        RESULTS_DIR / f"{output_base}.vec",
        RESULTS_DIR / f"{output_base}-*.vec",
        RESULTS_DIR / f"{config_name}-*.vec",
    ]

    matches = []
    for pattern in patterns:
        matches.extend(Path(p) for p in glob.glob(str(pattern)))

    if not matches:
        raise FileNotFoundError(f"No vector file found for {mode} in {RESULTS_DIR}")

    matches.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0]


def export_vector_csv(mode):
    require_tool("opp_scavetool")
    mode_config = MODE_CONFIGS[mode]
    vector_file = find_vector_file(mode)
    csv_file = RESULTS_DIR / f"{mode_config['output_base']}.csv"

    print(f"Exporting {vector_file.name} to {csv_file.name}...")
    subprocess.run(
        [
            "opp_scavetool",
            "export",
            "-o",
            str(csv_file),
            "-F",
            "CSV-R",
            str(vector_file),
        ],
        cwd=PAPER_EXPERIMENT_DIR,
        check=True,
    )
    return csv_file


def parse_vector_values(value):
    if value is None:
        return []
    return [float(part) for part in value.split() if part]


def extract_ping_rtt_csvs(mode, exported_csv):
    if not exported_csv.exists():
        raise FileNotFoundError(f"Missing exported CSV: {exported_csv}")

    mode_output_dir = PING_CSV_ROOT / mode
    if mode_output_dir.exists():
        shutil.rmtree(mode_output_dir)

    output_count = 0
    rtt_vector_count = 0
    ping_tx_sample_count = 0
    with exported_csv.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if row.get("type") != "vector":
                continue

            if row.get("name") == "pingTxSeq:vector":
                ping_tx_sample_count += len(parse_vector_values(row.get("vecvalue")))
                continue

            if row.get("name") != "rtt:vector":
                continue

            rtt_vector_count += 1
            times = parse_vector_values(row.get("vectime"))
            rtts = parse_vector_values(row.get("vecvalue"))
            if not times or not rtts:
                continue
            if len(times) != len(rtts):
                raise ValueError(
                    f"Mismatched vector lengths for {row.get('module')}: "
                    f"{len(times)} times vs {len(rtts)} RTT values"
                )

            module_name = row["module"]
            output_dir = PING_CSV_ROOT / mode / module_name
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / "rtt.csv"
            with output_file.open("w", newline="", encoding="utf-8") as out_file:
                writer = csv.writer(out_file)
                writer.writerow(["time", "rtt"])
                writer.writerows(zip(times, rtts))
            output_count += 1

    if output_count == 0:
        if rtt_vector_count:
            raise RuntimeError(
                f"Found {rtt_vector_count} rtt vectors in {exported_csv}, but none had samples. "
                f"Ping tx samples seen: {ping_tx_sample_count}."
            )
        raise RuntimeError(f"No rtt:vector rows found in {exported_csv}")

    print(f"Extracted {output_count} RTT files under {mode_output_dir}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate and run experiment 8 user-terminal ping baselines."
    )
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=sorted(MODE_CONFIGS.keys()),
        default=sorted(MODE_CONFIGS.keys()),
        help="Ping modes to run. Defaults to both bentpipe and isl.",
    )
    parser.add_argument(
        "--generate-only",
        action="store_true",
        help="Only write experiment8_ping.ini.",
    )
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="Skip opp_run and export/extract from existing vector files.",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Skip opp_scavetool export and extract from existing exported CSVs.",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Do not generate or run; extract from existing exported CSVs.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if args.extract_only:
        for mode in args.modes:
            csv_file = RESULTS_DIR / f"{MODE_CONFIGS[mode]['output_base']}.csv"
            extract_ping_rtt_csvs(mode, csv_file)
        return 0

    generate_ping_ini()
    if args.generate_only:
        return 0

    if not args.skip_run:
        run_ping_configs(args.modes)

    for mode in args.modes:
        if args.skip_export:
            csv_file = RESULTS_DIR / f"{MODE_CONFIGS[mode]['output_base']}.csv"
        else:
            csv_file = export_vector_csv(mode)

        extract_ping_rtt_csvs(mode, csv_file)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
