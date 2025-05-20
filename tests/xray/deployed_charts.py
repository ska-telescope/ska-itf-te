import json
from pathlib import Path
from typing import Dict, List, Set

import pytest
from assertpy.assertpy import assert_that
from mock import patch

from ska_ser_skallop.xray import execution_desc, execution_report, results

import sys
import ast

import argparse
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("chart_name", help="Helm chart name")
    parser.add_argument("dependencies_json", help="JSON string of chart dependencies")
    args = parser.parse_args()

    try:
        deps = json.loads(args.dependencies_json)
    except json.JSONDecodeError as e:
        print("❌ JSON decode error:", e)
        return

    print(f"✅ Chart: {args.chart_name}")
    print("✅ Dependencies:")
    for dep in deps:
        print(f" - {dep.strip()}")

if __name__ == "__main__":
    main()


