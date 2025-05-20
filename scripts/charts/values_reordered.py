import yaml
from collections import OrderedDict
import re
import os
import sys
import glob

# === Parse Chart.yaml to extract product → chart mapping ===
def parse_chart_yaml(chart_path):
    # Load the YAML structure
    with open(chart_path, 'r') as f:
        chart_data = yaml.safe_load(f)

    # Read raw lines to find comments and align them to dependencies
    with open(chart_path, 'r') as f:
        raw_lines = f.readlines()

    dependencies = chart_data.get('dependencies', [])
    product_map = OrderedDict()

    # Match each chart to its nearest preceding comment
    heading_for_index = {}
    current_heading = None
    dep_index = -1

    for i, line in enumerate(raw_lines):
        stripped = line.strip()
        if stripped.startswith('#'):
            current_heading = stripped
        elif stripped.startswith('- name:'):
            dep_index += 1
            heading_for_index[dep_index] = current_heading or '# Uncategorized'

    for i, dep in enumerate(dependencies):
        chart_key = dep.get('alias', dep.get('name'))
        heading = heading_for_index.get(i, '# Uncategorized')
        if heading not in product_map:
            product_map[heading] = []
        product_map[heading].append(chart_key)

    return product_map


# === Load values file ===
def parse_values_yaml(values_path):
    with open(values_path, 'r') as f:
        return yaml.safe_load(f)

# === Write reordered and annotated values file (overwrite) ===
def write_ordered_values(output_path, product_map, values_data):
    with open(output_path, 'w') as f:
        written_charts = set()
        for heading, charts in product_map.items():
            f.write(f"\n{heading}\n")
            for chart in charts:
                if chart in values_data:
                    yaml.dump({chart: values_data[chart]}, f, default_flow_style=False, sort_keys=False)
                    written_charts.add(chart)

        # Add any charts not in Chart.yaml under Uncategorized
        remaining = [chart for chart in values_data if chart not in written_charts]
        if remaining:
            f.write("\n# Uncategorized\n")
            for chart in remaining:
                yaml.dump({chart: values_data[chart]}, f, default_flow_style=False, sort_keys=False)

# === Find enabler file in a directory ===
def find_enabler_file(dir_path):
    matches = glob.glob(os.path.join(dir_path, '*-enablers.yaml'))
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        raise Exception(f"Multiple -enablers.yaml files found in {dir_path}")
    else:
        raise FileNotFoundError(f"No -enablers.yaml file found in {dir_path}")

# === Process multiple directories ===
def process_values_dirs(chart_yaml_path, values_dirs):
    product_map = parse_chart_yaml(chart_yaml_path)

    for dir_path in values_dirs:
        try:
            enabler_path = find_enabler_file(dir_path)
            values_data = parse_values_yaml(enabler_path)
            write_ordered_values(enabler_path, product_map, values_data)
            print(f"✅ Rewritten: {enabler_path}")
        except Exception as e:
            print(f"❌ Error in {dir_path}: {e}")

# === Entry point ===
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python reorder_values.py <path/to/Chart.yaml> <dir1> <dir2> ...")
        sys.exit(1)

    chart_yaml_path = sys.argv[1]
    values_dirs = sys.argv[2:]

    process_values_dirs(chart_yaml_path, values_dirs)
