import os
import re
import subprocess
import sys
from datetime import datetime

# Submodule imports
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of the script
SUBMODULE_PATH = os.path.abspath(os.path.join(BASE_DIR, "../../.jupyter-notebooks/src"))
sys.path.append(SUBMODULE_PATH)

from notebook_tools.sequence_diagram_setup import *

class LogRetriever:
    """Class with function to get the pod logs from kubectl"""
    def get_iso_date_string_from_string(self, val: str):
        # Log example: 1|2024-11-08T08:38:30.211Z|INFO|...
        match = re.search(ISO_DATE_STRING_PATTERN, val)
        return match.group() if match else ""

    def get_pod_logs_and_timestamps(self, namespace, pod_name, since_time):
        command = f"kubectl logs {pod_name} -n {namespace} --since-time={since_time} --timestamps"
        # print(command)

        try:
            # Run the command and capture the output
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            api_response = result.stdout  # Capture standard output

            # Check if there is any error output (0 is success)
            if result.returncode != 0:
                print(f"Error for {pod_name} (return code {result.returncode}): {result.stderr.strip()}")
                return []
            
            # Make sure api_response is not empty
            if not api_response:
                print(f"Empty API response for {pod_name} STDERR: {result.stderr.strip()}")
                return []
            
            # Save logs to files for debugging
            # with open(f'{pod_name}-{date}-{time_start}.txt', 'w', encoding='utf-8') as f:
            #     f.write(api_response)

            logs = api_response.splitlines()
        except Exception as e:
            print(f"An error occurred while running the command for {pod_name}: {e}")
            return []

        # Extract times from each line in the logs (e.g. 2024-08-26T07:16:11.051Z)
        extracted_logs = []
        for log in logs:
            # Remove null characters from the line
            log = log.replace("\x00", "").strip()
            # Skip empty logs
            if log == "":
                continue
            
            # Search for the timestamp in each log entry
            iso_date_string = self.get_iso_date_string_from_string(log)
            if iso_date_string:
                try:
                    # Parse the timestamp and add it to the extracted logs
                    time_obj = datetime.strptime(iso_date_string, "%Y-%m-%dT%H:%M:%S.%fZ")
                    adjusted_timestamp = time_obj.timestamp()
                    if '|DEBUG|' in log:
                        adjusted_timestamp -= DEBUG_LOG_TIME_ADJUSTMENT_SECONDS
                    else:
                        adjusted_timestamp -= GENERAL_LOG_TIME_ADJUSTMENT_SECONDS

                    extracted_logs.append((adjusted_timestamp, f" Log  - {log}"))
                except ValueError as e:
                    print(f"Timestamp parsing error for log: {log} - {e}")
            else:
                # print(f"No timestamp found in log: {log}")
                continue

        return extracted_logs
