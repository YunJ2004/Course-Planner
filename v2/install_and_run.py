"""
Installation and Launch Script for Course Planner
------------------------------------------------

This script ensures that all required Python packages are available
before launching the Course Planner web application.  When run, it
will attempt to import the necessary modules for the application
(Streamlit, ddgs, duckduckgo_search, and OpenAI).  If any of these
imports fail, the script will install the missing package using
``pip``.  Once all dependencies are available, the script invokes
Streamlit to run the ``streamlit_app.py`` module in this directory.

Usage
-----

Run this script with your Python interpreter (for example ``python3
install_and_run.py`` on Linux or macOS, or ``python install_and_run.py``
on Windows).  The script automatically installs missing packages and
starts the web app.  If you prefer to avoid modifying your system
Python installation, run the script inside a virtual environment.
"""

from __future__ import annotations

import subprocess
import sys
import importlib
from pathlib import Path


def ensure_package(pkg_name: str, import_name: str | None = None) -> None:
    """Ensure that a package is installed.

    Attempts to import the package specified by ``import_name`` (or
    ``pkg_name`` if ``import_name`` is ``None``).  If the import fails,
    ``pip`` is invoked to install the package.  Any installation
    failures will raise a ``subprocess.CalledProcessError``.

    :param pkg_name: The name of the package to install via pip.
    :param import_name: Optional alternative module name to import.
    """
    module_name = import_name or pkg_name
    try:
        importlib.import_module(module_name)
    except ImportError:
        print(f"Package '{module_name}' not found; installing {pkg_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg_name])


def main() -> None:
    """Install dependencies and launch the Streamlit app."""
    # Ensure essential packages are present.  We try to import
    # ``ddgs`` first, but if it isn't available we'll install
    # ``ddgs``.  Some environments may still use the legacy
    # ``duckduckgo_search`` package; Streamlit app handles that.
    ensure_package("streamlit", "streamlit")
    # Attempt to install the newer ddgs package.  If it's not
    # available, fallback to duckduckgo_search.
    try:
        importlib.import_module("ddgs")
    except ImportError:
        ensure_package("ddgs")
    # ``duckduckgo_search`` may still be required as a fallback; install
    # both to maximise compatibility.
    ensure_package("duckduckgo_search")
    # Install OpenAI client library for plan generation.
    ensure_package("openai")
    # Install Anthropic client library for additional AI provider support.
    # The 'anthropic' package provides a synchronous client compatible with the
    # messages API.  Installing both openai and anthropic allows users to
    # choose between providers at runtime.
    ensure_package("anthropic")

    # Launch the Streamlit app.  We use subprocess.run to ensure
    # appropriate propagation of exit codes.
    app_path = Path(__file__).parent / "streamlit_app.py"
    print("Launching the Course Planner Streamlit app...\n")
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
    ], check=True)


if __name__ == "__main__":
    main()