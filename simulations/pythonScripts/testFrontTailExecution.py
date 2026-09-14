"""Static/mocked regression checks; never starts OMNeT++."""

import argparse
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import raynetExperimentSupportFrontTail as support


def load_script(relative):
    path = Path(__file__).resolve().parent / relative
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FrontTailExecutionTests(unittest.TestCase):
    def test_snapshot_generator_translates_leocc_types(self):
        generator = load_script("duplicateFrontTailExperiments.py")
        self.assertEqual(generator.transform("LeoccQueue LeoccInterface"),
                         "LeoccFrontTailQueue LeoccFrontTailInterface")

    def test_stale_satcp_cubic_dependency_is_rejected(self):
        config = support.SimulationConfig("satcp", "test.ini", "Satcp_Run1", include_leo=True)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suffix = ".dylib" if sys.platform == "darwin" else ".so"
            library = root / "satcp/src" / ("libsatcp" + suffix)
            header = root / "cubic/src/transportlayer/tcp/flavours/TcpCubic.h"
            for path in (library, header):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            os.utime(library, (100, 100))
            os.utime(header, (200, 200))
            with self.assertRaisesRegex(RuntimeError, "stale SaTCP"):
                support.check_satcp_build_freshness([config], root)
            os.utime(library, (300, 300))
            support.check_satcp_build_freshness([config], root)

    def test_leo_runners_use_shared_runner_and_leo_paths(self):
        for number in (8, 9, 10):
            with self.subTest(experiment=number), patch.dict(sys.modules, {"PyPDF2": Mock()}):
                runner = load_script(f"experiment{number}FrontTail/runExperiment{number}FrontTail.py")
                self.assertEqual(runner.DEFAULT_LEO_SIMULATION_CORES, 15)
                with patch.object(runner, "run_simulation_configs") as run:
                    runner.run_config_batch([("satcp", "Satcp_Run1")], 15, Path("test"))
                self.assertTrue(run.call_args.args[0][0].include_leo)
                self.assertEqual(run.call_args.args[2], 15)

    def test_leo_generators_override_real_queue_dropper(self):
        root = Path(__file__).resolve().parent
        for number in (8, 9, 10):
            with self.subTest(experiment=number):
                text = (root / f"experiment{number}FrontTail/generateExperiment{number}FrontTailIniFile.py").read_text()
                self.assertIn('**.ppp[*].queue.dropperClass = "inet::queueing::PacketAtCollectionBeginDropper"', text)
                self.assertNotIn('ppp[*].ppp.queue', text)
                self.assertIn('useLeosatellitesHandoverOracle = true', text)
                self.assertIn('LeoccFrontTailInterface', text)

    def test_stale_leocc_is_rejected(self):
        config = support.SimulationConfig("leocc", "test.ini", "Leocc_Run1")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            suffix = ".dylib" if sys.platform == "darwin" else ".so"
            library = root / "leocc/src" / ("libleocc" + suffix)
            header = root / "tcpPaced/src/transportlayer/tcp/TcpPacedConnection.h"
            for path in (library, header):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
            os.utime(library, (100, 100))
            os.utime(header, (200, 200))
            with self.assertRaisesRegex(RuntimeError, "stale LeoCC"):
                support.check_leocc_build_freshness([config], root)
            os.utime(library, (300, 300))
            support.check_leocc_build_freshness([config], root)

    def test_cleanup_does_not_remove_neighboring_runs(self):
        config = support.SimulationConfig("leocc", "test.ini", "Leocc_Run1")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "results").mkdir()
            own = root / "results/Leocc_Run1-#0.vec"
            other = root / "results/Leocc_Run10-#0.vec"
            own.touch()
            other.touch()
            support._clean_result_files(config, root)
            self.assertFalse(own.exists())
            self.assertTrue(other.exists())

    def test_timeout_terminates_and_never_marks_complete(self):
        config = support.SimulationConfig("leocc", "test.ini", "Leocc_Run1")
        process = Mock()
        process.wait.side_effect = subprocess.TimeoutExpired("fake", 1)
        process.returncode = -15
        running = support._RunningSimulation(config, process, time.monotonic() - 2, None, None)
        with patch.object(support, "_terminate_process_group") as terminate, \
                patch.object(support, "_result_signature", return_value=[{}]), \
                patch.object(support, "_write_completion_marker") as mark:
            self.assertFalse(support._finish_simulation(running, Path("."), 1, None))
            terminate.assert_called_once_with(process)
            mark.assert_not_called()

    def test_failed_jobs_retry_but_successes_do_not(self):
        configs = [support.SimulationConfig("cubic", "test.ini", name)
                   for name in ("Cubic_Run1", "Cubic_Run2")]
        started = []

        def start(config, cwd, attempt):
            started.append((config.config_name, attempt))
            process = Mock()
            process.poll.return_value = 0
            return support._RunningSimulation(config, process, time.monotonic(), None, None)

        def finish(running, *args):
            return running.config.config_name != "Cubic_Run1" or len(started) > 2

        with patch.object(support, "_start_simulation", side_effect=start), \
                patch.object(support, "_finish_simulation", side_effect=finish), \
                patch.object(support.time, "sleep"):
            support._run_simulation_configs(configs, ".", 2, retries=1, resume=False)
        self.assertEqual(started, [("Cubic_Run1", 1), ("Cubic_Run2", 1), ("Cubic_Run1", 2)])

    def test_experiment1_delegates_to_bounded_runner(self):
        runner = load_script("experiment1FrontTail/runExperiment1and2FrontTail.py")
        entry = runner.ConfigEntry("experiment1FrontTail", "leocc", "test.ini", "Leocc_Run1", 1)
        args = argparse.Namespace(cores=30, retries=2, resume=True)
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(runner, "SCRIPT_DIR", Path(directory)), \
                patch.object(runner, "run_simulation_configs") as run:
            runner.run_simulations([entry], args)
        self.assertEqual(run.call_args.args[2], 30)
        self.assertEqual(run.call_args.kwargs, {"retries": 2, "resume": True})

    def test_experiment1_generator_selects_front_drop_leocc(self):
        generator = load_script("experiment1FrontTail/generateExperiment1FrontTailIniFile.py")
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "pythonScripts/experiment1FrontTail"
            script.mkdir(parents=True)
            scenarios = root / "paperExperiments/scenarios/experiment1FrontTail"
            scenarios.mkdir(parents=True)
            (scenarios / "run1.xml").write_text("<scenario/>")
            try:
                os.chdir(script)
                with patch.object(generator, "clone_raynet_ini_variants"), \
                        patch.object(generator, "clone_orbtcp_pint_ini_variants"):
                    generator.main()
            finally:
                os.chdir(previous)
            text = (root / "paperExperiments/experiment1FrontTail/experiment1FrontTail_leocc.ini").read_text()
            self.assertIn('queue.typename = "LeoccFrontTailQueue"', text)
            self.assertIn('app[1].typename = "LeoccPingApp"', text)
            self.assertNotIn('queue.typename = "LeoccQueue"', text)


if __name__ == "__main__":
    unittest.main()
