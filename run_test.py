#!/usr/bin/env python3
"""
Comprehensive test runner for fullon_cache_api.

This script runs the full test suite including unit tests, integration tests,
linting, type checking, and code coverage reporting.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return whether it succeeded."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Command: {' '.join(command)}")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False


def main():
    """Run comprehensive test suite."""
    print("🚀 Starting comprehensive test suite for fullon_cache_api")

    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # List of test commands to run
    test_commands = [
        {
            "command": ["poetry", "run", "pytest", "tests/", "-v", "--tb=short"],
            "description": "Running pytest unit tests",
        },
        {
            "command": [
                "poetry",
                "run",
                "pytest",
                "tests/",
                "--cov=src/fullon_cache_api",
                "--cov-report=term-missing",
            ],
            "description": "Running test coverage analysis",
        },
        {
            "command": ["poetry", "run", "black", "--check", "src/", "tests/"],
            "description": "Checking code formatting with Black",
        },
        {
            "command": ["poetry", "run", "ruff", "check", "src/", "tests/"],
            "description": "Running Ruff linting",
        },
        {
            "command": ["poetry", "run", "mypy", "src/fullon_cache_api/"],
            "description": "Running mypy type checking",
        },
    ]

    # Run all commands
    all_passed = True
    results = []

    for test in test_commands:
        passed = run_command(test["command"], test["description"])
        results.append((test["description"], passed))
        if not passed:
            all_passed = False

    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    for description, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {description}")

    print("=" * 60)

    if all_passed:
        print("🎉 All tests passed! Infrastructure is ready.")
        return 0
    else:
        print("💥 Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
