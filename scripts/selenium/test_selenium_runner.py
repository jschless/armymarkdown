#!/usr/bin/env python3
"""
Simple script to run Selenium tests for PDF generation validation.

Usage:
    python test_selenium_runner.py                    # Run all selenium tests
    python test_selenium_runner.py --test-home       # Test home page only
    python test_selenium_runner.py --test-form       # Test form view only
    python test_selenium_runner.py --test-nan-bug    # Test NaN% bug specifically
"""

import argparse
import subprocess
import sys

import requests


def check_server_running(url="http://localhost:8000", timeout=5):
    """Check if the development server is running."""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


def run_selenium_tests(test_filter=None):
    """Run selenium tests with optional filter."""
    # Check if server is running
    if not check_server_running():
        print("❌ Development server not running at http://localhost:8000")
        print("Please start the server first:")
        print("  docker-compose -f docker-compose-dev.yaml up --build")
        return False

    print("✅ Development server is running")

    # Build pytest command
    cmd = [
        "uv",
        "run",
        "pytest",
        "tests/test_pdf_generation_e2e.py",
        "-v",
        "-m",
        "selenium",
    ]

    if test_filter:
        cmd.extend(["-k", test_filter])

    print(f"Running: {' '.join(cmd)}")

    # Run tests
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Run Selenium tests for PDF generation"
    )
    parser.add_argument("--test-home", action="store_true", help="Test home page only")
    parser.add_argument("--test-form", action="store_true", help="Test form view only")
    parser.add_argument(
        "--test-nan-bug", action="store_true", help="Test NaN% bug specifically"
    )
    parser.add_argument(
        "--url", default="http://localhost:8000", help="Server URL to test against"
    )

    args = parser.parse_args()

    # Set environment variable for test URL
    import os

    os.environ["TEST_APP_URL"] = args.url

    # Determine test filter
    test_filter = None
    if args.test_home:
        test_filter = "test_pdf_from_home_page"
    elif args.test_form:
        test_filter = "test_pdf_from_form_view"
    elif args.test_nan_bug:
        test_filter = "test_progress_bar_nan_bug"

    # Run tests
    success = run_selenium_tests(test_filter)

    if success:
        print("\n✅ All Selenium tests passed!")
        print("PDF generation appears to be working correctly from both views.")
    else:
        print("\n❌ Some Selenium tests failed!")
        print("Check the output above for details.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
