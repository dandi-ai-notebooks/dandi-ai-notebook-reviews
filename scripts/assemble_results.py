import json
import os
from pathlib import Path
from typing import Dict, List

def process_qualification_test(file_path: str, rel_path: str) -> Dict:
    """Extract pass/fail result from qualification test file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    paths = rel_path.split('/')
    return {
        "type": "qualification_test",
        "model": paths[0],
        "dandiset_id": paths[2],
        "subfolder": paths[3],
        "passing": data.get("passing", False)
    }

def process_comparison_test(file_path: str, rel_path: str) -> Dict:
    """Extract selection from comparison test file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    paths = rel_path.split('/')
    return {
        "type": "comparison",
        "model": paths[0],
        "dandiset_id": paths[2],
        "subfolder1": paths[3],
        "subfolder2": paths[5],
        "selection": data.get("selection")
    }

def main():
    reviews_dir = Path("reviews")
    results = []

    # Recursively walk through reviews directory
    for root, _, files in os.walk(reviews_dir):
        root_path = Path(root)

        for file in files:
            if not file.endswith('.json'):
                continue

            file_path = root_path / file
            relative_path = file_path.relative_to(reviews_dir)

            if file == "qualification_test.json":
                result = process_qualification_test(str(file_path), str(relative_path))
                results.append(result)

            elif file == "comparison.json":
                result = process_comparison_test(str(file_path), str(relative_path))
                results.append(result)

    # Write aggregated results
    output = {
        "results": results,
        "summary": {
            "total_qualification_tests": len([r for r in results if r["type"] == "qualification_test"]),
            "total_passing_qualification_tests": len([r for r in results if r["type"] == "qualification_test" and r["passing"]]),
            "total_comparison_tests": len([r for r in results if r["type"] == "comparison"])
        }
    }

    with open('results.json', 'w') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
