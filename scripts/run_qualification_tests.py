import os
import subprocess
import glob
import json

# Dictionary to store results
results = {}

if not os.environ.get('DANDI_AI_NOTEBOOKS_3_DIR'):
    raise ValueError('Environment variable DANDI_AI_NOTEBOOKS_3_DIR is not set.')

dandiset_id = os.environ.get('DANDISET_ID')
if not dandiset_id:
    raise ValueError('Environment variable DANDISET_ID is not set.')

model = os.environ.get('MODEL')
if not model:
    raise ValueError('Environment variable MODEL is not set.')

# Get base directory for dandiset
base_dir = os.path.join(os.environ['DANDI_AI_NOTEBOOKS_3_DIR'], 'dandisets', dandiset_id)

# Find all folders matching the pattern and containing the notebook file
pattern = os.path.join(base_dir, '2025-04-28-*')
matching_folders = glob.glob(pattern)

for folder_path in matching_folders:
    notebook_path = os.path.join(folder_path, f'{dandiset_id}.ipynb')
    if os.path.exists(notebook_path):
        # Get just the folder name without the full path
        subfolder = os.path.basename(folder_path)

        # Construct and run the command
        cmd = [
            'python',
            'scripts/qualification_test.py',
            '--dandiset_id', dandiset_id,
            '--subfolder_name', subfolder,
            '--model', model
        ]

        print(f'Processing folder: {subfolder}')
        subprocess.run(cmd)

        # Check results immediately after processing
        this_dir = os.path.dirname(os.path.abspath(__file__))
        model_second_part = model.split('/')[1]
        json_path = f'{this_dir}/reviews/{model_second_part}/dandisets/{dandiset_id}/{subfolder}/qualification_test.json'
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                data = json.load(f)
                results[subfolder] = "PASS" if data.get('passing', False) else "FAIL"

# Print summary after all processing is complete
if results:
    print("\nSummary of qualification test results:")
    print("-" * 40)
    for subfolder, status in results.items():
        print(f"{subfolder}: {status}")
