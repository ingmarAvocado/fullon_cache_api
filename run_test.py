#!/usr/bin/env python3
"""Enhanced test runner with better visibility and control."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _supports_xdist() -> bool:
    """Return True if pytest-xdist is available in the environment."""
    # Fast path: check if `pytest -n` is supported by presence of xdist
    try:
        import importlib.util

        return importlib.util.find_spec("xdist") is not None
    except Exception:
        return False


def _existing_paths(paths: list[str]) -> list[str]:
    """Filter only existing paths to avoid pytest errors."""
    out: list[str] = []
    for p in paths:
        if Path(p).exists():
            out.append(p)
    return out or ["tests/"]


def run_tests(args: argparse.Namespace) -> int:
    """Run tests with enhanced output."""
    # Ensure we run from project root
    os.chdir(Path(__file__).parent)

    # Base command
    cmd: list[str] = ["poetry", "run", "pytest"]

    # Select paths
    if args.paths:
        cmd.extend(_existing_paths(args.paths))
    else:
        # Default: run unit tests only for speed and determinism
        paths = ["tests/unit/"]
        cmd.extend(_existing_paths(paths))

    # Parallelism (opt-in if xdist is available)
    if args.parallel and _supports_xdist():
        # Enable xdist only when explicitly requested
        if args.workers and args.workers > 0:
            cmd.extend(["-n", str(args.workers)])
        else:
            cmd.extend(["-n", "auto"])

    # Verbosity
    if args.verbose == 1:
        cmd.append("-v")
    elif args.verbose >= 2:
        cmd.append("-vv")
    elif args.quiet:
        cmd.append("-q")

    # Output controls
    if args.tb:
        cmd.extend(["--tb", args.tb])
    if args.capture:
        cmd.extend(["--capture", args.capture])
    if args.no_header:
        cmd.append("--no-header")
    if args.no_summary:
        cmd.append("--no-summary")

    # Stop/limit
    if args.exitfirst:
        cmd.append("-x")
    if args.maxfail:
        cmd.extend(["--maxfail", str(args.maxfail)])

    # Markers/keyword
    if args.markers:
        cmd.extend(["-m", args.markers])
    if args.keyword:
        cmd.extend(["-k", args.keyword])

    # Last-failed
    if args.lf:
        cmd.append("--lf")
    if args.ff:
        cmd.append("--ff")

    # Timeouts and durations (only if plugin available)
    if args.timeout and args.timeout != 30:
        cmd.extend(["--timeout", str(args.timeout)])
    if args.timeout_method:
        cmd.extend(["--timeout-method", args.timeout_method])
    if args.durations and args.durations != 10:
        cmd.extend(["--durations", str(args.durations)])

    # Warnings/capture
    if args.no_warnings:
        cmd.extend(["-p", "no:warnings"])
    if args.capture_no:
        cmd.append("-s")

    # Coverage
    if args.cov:
        if args.cov is True:
            cmd.append("--cov")
        else:
            cmd.extend(["--cov", args.cov])
        if args.cov_report:
            cmd.extend(["--cov-report", args.cov_report])
        if args.cov_fail_under:
            cmd.extend(["--cov-fail-under", str(args.cov_fail_under)])

    # JUnit
    if args.junitxml:
        cmd.extend(["--junitxml", args.junitxml])

    # Color
    if args.color:
        cmd.append("--color=yes")
    elif args.no_color:
        cmd.append("--color=no")

    # Results summary flags
    if args.results:
        cmd.extend(["-r", args.results])

    # Collection-only
    if args.collect_only or args.dry_run:
        cmd.append("--collect-only")

    # Render final command
    print("Running:", " ".join(cmd))
    print("=" * 80)

    # Execute with graceful fallback if xdist is unavailable
    try:
        proc = subprocess.run(cmd, text=True)
        rc = proc.returncode
    except FileNotFoundError:
        print("poetry not found; falling back to system pytest")
        cmd = ["pytest"] + cmd[3:]
        proc = subprocess.run(cmd, text=True)
        rc = proc.returncode

    # Retry without -n if plugin not installed
    if rc != 0 and "-n" in cmd:
        # Minimal detection: rerun help to see if -n is unrecognized
        print("Note: pytest-xdist not detected. Retrying without parallelism…")
        try:
            # strip "-n <value>" pair
            if "-n" in cmd:
                i = cmd.index("-n")
                # remove flag and value if present
                del cmd[i : min(i + 2, len(cmd))]
            print("Running:", " ".join(cmd))
            print("=" * 80)
            proc = subprocess.run(cmd, text=True)
            rc = proc.returncode
        except Exception:
            pass

    return rc


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Enhanced test runner with better visibility and control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ./run_test.py                           # Default suite (auto-parallel if xdist)
  ./run_test.py tests/unit/ -v            # Run unit tests with verbosity
  ./run_test.py tests/integration/ -x     # Stop on first failure
  ./run_test.py -k websocket -vv          # Keyword filter with high verbosity
  ./run_test.py --quick --tb=line         # Quick run with line tracebacks
  ./run_test.py --cov src/fullon_cache_api --cov-report=term-missing
  ./run_test.py -n --workers 8            # Force 8 workers (requires xdist)
        """,
    )

    # Paths
    parser.add_argument("paths", nargs="*", help="Test paths to run")

    # Shortcuts
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--unit", action="store_true", help="Run unit tests only")
    group.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    group.add_argument("--chaos", action="store_true", help="Run chaos tests only")
    group.add_argument(
        "--monitoring", action="store_true", help="Run monitoring tests only"
    )
    group.add_argument(
        "--quick", action="store_true", help="Run quick tests (unit + fast integ)"
    )
    group.add_argument("--all", action="store_true", help="Run all tests")

    # Execution
    parser.add_argument("-n", "--parallel", action="store_true", help="Use xdist")
    parser.add_argument("--no-parallel", action="store_true", help="Disable xdist")
    parser.add_argument("-w", "--workers", type=int, default=4, help="xdist workers")
    parser.add_argument("-x", "--exitfirst", action="store_true", help="Exit early")
    parser.add_argument("--maxfail", type=int, help="Exit after N failures")
    parser.add_argument("--lf", action="store_true", help="Last failed only")
    parser.add_argument("--ff", action="store_true", help="Failed first")

    # Output
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument(
        "--tb", choices=["auto", "long", "short", "line", "native", "no"], help="TB"
    )
    parser.add_argument(
        "--capture", choices=["sys", "fd", "no"], help="Capture method"
    )
    parser.add_argument("-s", "--capture-no", action="store_true")
    parser.add_argument("--no-header", action="store_true")
    parser.add_argument("--no-summary", action="store_true")
    parser.add_argument("--color", action="store_true")
    parser.add_argument("--no-color", action="store_true")

    # Filters
    parser.add_argument("-m", "--markers", help="Marker expression")
    parser.add_argument("-k", "--keyword", help="Keyword expression")

    # Time/size
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--timeout-method", choices=["signal", "thread"])
    parser.add_argument("--durations", type=int, default=10)

    # Collection/reporting
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-warnings", action="store_true")
    parser.add_argument("-r", "--results", default="fEsxX")

    # Coverage
    parser.add_argument("--cov", nargs="?", const=True)
    parser.add_argument(
        "--cov-report", choices=["term", "html", "xml", "term-missing"]
    )
    parser.add_argument("--cov-fail-under", type=int)
    parser.add_argument("--junitxml")

    args = parser.parse_args()

    # Shortcut resolution
    if args.unit:
        args.paths = ["tests/unit/"]
    elif args.integration:
        args.paths = ["tests/integration/"]
    elif args.chaos:
        args.paths = ["tests/chaos/"]
    elif args.monitoring:
        args.paths = ["tests/monitoring/"]
    elif args.quick:
        args.paths = ["tests/unit/"]
        args.markers = (args.markers + " and not slow") if args.markers else "not slow"
    elif args.all:
        args.paths = ["tests/"]

    # Validate conflicting options
    if args.quiet and args.verbose:
        parser.error("Cannot use both --quiet and --verbose")
    if args.color and args.no_color:
        parser.error("Cannot use both --color and --no-color")
    if args.parallel and args.no_parallel:
        parser.error("Cannot use both --parallel and --no-parallel")

    sys.exit(run_tests(args))


if __name__ == "__main__":
    main()
