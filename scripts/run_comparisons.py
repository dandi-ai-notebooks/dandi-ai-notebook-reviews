from typing import List, Dict
import os
import subprocess
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
failed_folders = []
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
            else:
                failed_folders.append(folder)
    else:
        print(f"Warning: No qualification test results found for {folder}")

print(f"\nFound {len(passing_folders)} passing notebooks:")
for folder in passing_folders:
    print(f"- {folder}")

print("")

print(f"\nFound {len(failed_folders)} failing notebooks:")
for folder in failed_folders:
    print(f"- {folder}")

# Compare each pair of passing notebooks
pairs = list(itertools.combinations(passing_folders, 2))
total_pairs = len(pairs)
print(f"\nComparing {total_pairs} pairs of notebooks...")

results = []

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
    json_path = f'{this_dir}/../reviews/{model_second_part}/dandisets/{dandiset_id}/{subfolder1}/comparisons/{subfolder2}/comparison.json'
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
            results.append((subfolder1, subfolder2, data['selection']))

# Print summary after all processing is complete
if results:
    print("\nSummary of comparison results:")
    print("-" * 40)
    for subfolder1, subfolder2, selection in results:
        print(f"{subfolder1} vs {subfolder2}: Selected notebook {selection}")

def rank_notebooks(nodes1: List[str],
                   nodes2: List[str],
                   selections: List[int],
                   *,
                   max_iter: int = 1000,
                   tol: float = 1e-8) -> List[str]:
    """
    Rank notebooks given pair‑wise outcomes using the Bradley‑Terry model.

    Parameters
    ----------
    nodes1, nodes2 : List[str]
        Paired notebook identifiers.  nodes1[i] competed against nodes2[i].
    selections : List[int]
        For each pair, 1 means nodes1[i] won, 2 means nodes2[i] won.
    max_iter : int, optional
        Maximum MM iterations (default 1000).
    tol : float, optional
        Convergence threshold on max parameter change (default 1e‑8).

    Returns
    -------
    List[str]
        Notebook names sorted from highest to lowest estimated ability.
    """
    if not (len(nodes1) == len(nodes2) == len(selections)):
        raise ValueError("nodes1, nodes2 and selections must be the same length")

    if len(nodes1) == 0:
        return []

    # All unique notebooks start with the same ability
    items = set(nodes1) | set(nodes2)
    theta: Dict[str, float] = {item: 1.0 for item in items}

    for _ in range(max_iter):
        wins  = {item: 0.0 for item in items}   # w_i
        denom = {item: 0.0 for item in items}   # d_i

        # accumulate wins and denominators
        for a, b, s in zip(nodes1, nodes2, selections):
            if s == 1:
                wins[a] += 1
            elif s == 2:
                wins[b] += 1
            else:
                raise ValueError("selections must contain only 1 or 2")

            inv_sum = 1.0 / (theta[a] + theta[b])
            denom[a] += inv_sum
            denom[b] += inv_sum

        # MM‑update: θ_i ← w_i / d_i   (leave θ_i unchanged if d_i == 0)
        new_theta = {i: (wins[i] / denom[i] if denom[i] else theta[i])
                     for i in items}

        # normalise for identifiability (mean θ = 1)
        mean_theta = sum(new_theta.values()) / len(new_theta)
        for i in items:
            new_theta[i] /= mean_theta or 1.0  # avoid division by 0

        # check convergence
        if max(abs(new_theta[i] - theta[i]) for i in items) < tol:
            theta = new_theta
            break
        theta = new_theta

    # sort by estimated ability (descending)
    return sorted(theta.keys(), key=lambda k: theta[k], reverse=True)

nodes1 = []
nodes2 = []
selections = []
num_wins = {
    k: 0 for k in passing_folders
}
num_losses = {
    k: 0 for k in passing_folders
}
for subfolder1, subfolder2, selection in results:
    nodes1.append(subfolder1)
    nodes2.append(subfolder2)
    selections.append(selection)
    if selection == 1:
        num_wins[subfolder1] += 1
        num_losses[subfolder2] += 1
    elif selection == 2:
        num_wins[subfolder2] += 1
        num_losses[subfolder1] += 1
ranked_notebooks = rank_notebooks(nodes1, nodes2, selections)
print(f"\nRanked notebooks for model {model} and dandiset {dandiset_id}:")
for i, notebook in enumerate(ranked_notebooks):
    print(f"{i + 1}: {notebook} (wins: {num_wins[notebook]}, losses: {num_losses[notebook]})")

this_dir = os.path.dirname(os.path.abspath(__file__))
ranking_json_fname = f'{this_dir}/../reviews/{model_second_part}/dandisets/{dandiset_id}/rankings.json'
with open(ranking_json_fname, 'w') as f:
    json.dump({
        'ranked_notebooks': [
            {
                'name': notebook,
                'wins': num_wins[notebook],
                'losses': num_losses[notebook]
            }
            for notebook in ranked_notebooks
        ]
    }, f, indent=4)


