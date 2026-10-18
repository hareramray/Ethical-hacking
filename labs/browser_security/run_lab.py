"""Prepare, run, and verify the local Vue + Django browser-security labs."""

import argparse
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
import venv

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
ENVIRONMENT = ROOT / ".venv"
PYTHON = ENVIRONMENT / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def run(arguments, cwd=ROOT):
    print("\n> " + " ".join(map(str, arguments)), flush=True)
    subprocess.run([str(value) for value in arguments], cwd=cwd, check=True)


def npm():
    executable = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not executable:
        raise RuntimeError("Node.js and npm are required. Install Node.js 24 LTS, then rerun --setup.")
    return executable


def require_setup():
    if not PYTHON.is_file():
        raise RuntimeError("Run python labs/browser_security/run_lab.py --setup first.")


def migrate():
    run([PYTHON, "manage.py", "migrate", "--noinput"], BACKEND)


def build():
    if not (FRONTEND / "node_modules").is_dir():
        raise RuntimeError("Frontend dependencies are missing. Run this launcher with --setup.")
    run([npm(), "run", "build"], FRONTEND)


def setup():
    if sys.version_info < (3, 12):
        raise RuntimeError("This lab requires Python 3.12 or newer.")
    npm_executable = npm()
    if not PYTHON.is_file():
        print("Creating an isolated Python environment...", flush=True)
        venv.EnvBuilder(with_pip=True).create(ENVIRONMENT)
    run([PYTHON, "-m", "pip", "install", "-r", ROOT / "requirements.txt"])
    run([npm_executable, "ci" if (FRONTEND / "package-lock.json").is_file() else "install"], FRONTEND)
    build()
    migrate()
    print("\nSetup complete. Start with: python labs/browser_security/run_lab.py", flush=True)


def stop_child(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        # The Windows virtual-environment launcher may spawn another Python
        # process. Stop this known child tree, including that interpreter.
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def serve(port, peer_port):
    for selected_port in (port, peer_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as check:
            try:
                check.bind(("127.0.0.1", selected_port))
            except OSError as error:
                raise RuntimeError(f"Loopback port {selected_port} is unavailable. Stop the existing lab or choose --port/--peer-port.") from error
    migrate()
    common = dict(os.environ, LAB_MAIN_ORIGIN=f"http://127.0.0.1:{port}",
                  LAB_PEER_ORIGIN=f"http://127.0.0.1:{peer_port}")
    print(f"\nOpen {common['LAB_MAIN_ORIGIN']}/\nCompanion origin: {common['LAB_PEER_ORIGIN']}\nStop both with Ctrl+C.\n", flush=True)
    processes = []

    def stop_signal(_number, _frame):
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, stop_signal)
    try:
        for role, selected_port in (("main", port), ("peer", peer_port)):
            processes.append(subprocess.Popen(
                [str(PYTHON), "manage.py", "runserver", f"127.0.0.1:{selected_port}", "--noreload"],
                cwd=BACKEND, env=dict(common, LAB_ROLE=role),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            ))
        while all(process.poll() is None for process in processes):
            time.sleep(0.25)
        raise RuntimeError("A lab server stopped unexpectedly; both servers have been shut down.")
    finally:
        for process in processes:
            stop_child(process)
        signal.signal(signal.SIGTERM, previous)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--setup", action="store_true", help="Install isolated dependencies, build Vue, and migrate; then exit")
    actions.add_argument("--serve", action="store_true", help="Serve on loopback (the default action)")
    actions.add_argument("--build", action="store_true", help="Rebuild Vue after frontend edits")
    actions.add_argument("--test", action="store_true", help="Run Django checks/tests, rebuild Vue, then run browser tests")
    parser.add_argument("--port", type=int, default=8766, help="Loopback port, default 8766")
    parser.add_argument("--peer-port", type=int, help="Companion origin port, default main port + 1")
    args = parser.parse_args()
    peer_port = args.peer_port if args.peer_port is not None else args.port + 1
    if not 1024 <= args.port <= 65535:
        parser.error("--port must be between 1024 and 65535")
    if not 1024 <= peer_port <= 65535 or peer_port == args.port:
        parser.error("--peer-port must be between 1024 and 65535 and different from --port")
    try:
        if args.setup:
            setup()
            return 0
        require_setup()
        if args.build:
            build()
        elif args.test:
            run([PYTHON, "manage.py", "check"], BACKEND)
            run([PYTHON, "manage.py", "test", "securitylab", "--verbosity", "2"], BACKEND)
            build()
            run([npm(), "run", "test:e2e"], FRONTEND)
        else:
            if not (FRONTEND / "dist" / "index.html").is_file():
                raise RuntimeError("Vue build is missing. Run this launcher with --setup or --build.")
            serve(args.port, peer_port)
        return 0
    except KeyboardInterrupt:
        print("\nLab stopped.")
        return 0
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"\nLab command failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
