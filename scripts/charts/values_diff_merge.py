import os
import yaml
# from deepdiff import DeepDiff
from collections import defaultdict

def load_yaml(file_path):
    with open(file_path, 'r') as f:
        return yaml.safe_load(f) or {}

def write_yaml(file_path, data):
    with open(file_path, 'w') as f:
        yaml.dump(data, f, sort_keys=False)

def get_chart_name(chart_path):
    chart_yaml = os.path.join(chart_path, "Chart.yaml")
    if os.path.exists(chart_yaml):
        with open(chart_yaml, "r") as f:
            content = yaml.safe_load(f)
            return content.get("name")
    return os.path.basename(chart_path)

def merge_all_values(chart_dirs, output_path="charts/ska-mid/values.yaml", flatten=True):
    merged = {}
    collisions = defaultdict(list)

    for chart_dir in chart_dirs:
        chart_name = get_chart_name(chart_dir)
        values_path = os.path.join(chart_dir, "values.yaml")
        if not os.path.exists(values_path):
            print(f"⚠️  Skipping {chart_dir}, no values.yaml found.")
            continue

        values = load_yaml(values_path)

        if flatten:
            for key in values.keys():
                if key in merged:
                    collisions[key].append(chart_name)
            merged.update(values)
        else:
            merged[chart_name] = values

    if collisions and flatten:
        print("\n🚨 POTENTIAL KEY COLLISIONS:")
        for key, charts in collisions.items():
            print(f"  - Key '{key}' found in: {', '.join(charts)}")
        print("  ➤ Resolve these before continuing.\n")

    print(f"✅ Writing merged values.yaml to: {output_path}")
    write_yaml(output_path, merged)

# Example usage:
if __name__ == "__main__":
    chart_folders = [
        "charts/ska-mid-itf-dpd",
        "charts/ska-mid",
        # "charts/ska-mid-cbf-engineering-console-cache",
    ]
    merge_all_values(chart_folders)
