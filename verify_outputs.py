#!/usr/bin/env python3
"""Convenience wrapper so `python3 verify_outputs.py` works from the repo root."""
import runpy
runpy.run_path(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "src", "verify_outputs.py"), run_name="__main__")
