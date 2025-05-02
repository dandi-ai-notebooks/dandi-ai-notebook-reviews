import os
import subprocess
import glob
import json
import itertools

model = os.environ.get('MODEL')
if not model:
    raise ValueError('Environment variable MODEL is not set.')
if '/' not in model:
    raise ValueError('MODEL environment variable must be in format provider/name')

dandiset_id = os.environ.get('DANDISET_ID')
if not dandiset_id:
    raise ValueError('Environment variable DANDISET_ID is not set.')
model_second_part = model.split('/')[1]

# Find all folders with passing qualification tests
passing_folders = []
base_review_dir = f'reviews/{model_second_part}/dandisets/{dandiset_id}'

if not os.path.exists(base_review_dir):
    print(f"No reviews found for model {model} and dandiset {dandiset_id}")
    exit(0)

# Look through all subfolders in the review directory
for folder in os.listdir(base_review_dir):
    json_path = os.path.join(base_review_dir, folder, 'qualification_test.json')
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
            if data.get('passing', False):
                passing_folders.append(folder)

print(f"\nFound {len(passing_folders)} passing notebooks:")
for folder in passing_folders:
    print(f"- {folder}")

# Compare each pair of passing notebooks
pairs = list(itertools.combinations(passing_folders, 2))
total_pairs = len(pairs)
print(f"\nComparing {total_pairs} pairs of notebooks...")

# Dictionary to store results
results = {}

for idx, (subfolder1, subfolder2) in enumerate(pairs, 1):
    print(f"\nProcessing pair {idx}/{total_pairs}:")
    print(f"1: {subfolder1}")
    print(f"2: {subfolder2}")

    # Construct and run the command
    cmd = [
        'python',
        'scripts/comparison.py',
        '--dandiset_id', dandiset_id,
        '--subfolder1_name', subfolder1,
        '--subfolder2_name', subfolder2,
        '--model', model
    ]

    subprocess.run(cmd)

    # Check results immediately after processing
    this_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = f'{this_dir}/reviews/{model_second_part}/dandisets/{dandiset_id}/{subfolder1}/comparisons/{subfolder2}/comparison.json'
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
            results[(subfolder1, subfolder2)] = data['selection']

# Print summary after all processing is complete
if results:
    print("\nSummary of comparison results:")
    print("-" * 40)
    for (subfolder1, subfolder2), selection in results.items():
        print(f"{subfolder1} vs {subfolder2}: Selected notebook {selection}")
