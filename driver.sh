#!/bin/bash

export DANDI_AI_NOTEBOOKS_3_DIR=../dandi-ai-notebooks-3

export DANDISET_ID=000690
# export DANDISET_ID=001375

# export MODEL=google/gemini-2.5-pro-preview-03-25
# export MODEL=google/gemini-2.0-flash-001
export MODEL=anthropic/claude-3.7-sonnet

python scripts/run_qualification_tests.py
python scripts/run_comparisons.py
python scripts/assemble_results.py
