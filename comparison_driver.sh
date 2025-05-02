#!/bin/bash

export DANDI_AI_NOTEBOOKS_3_DIR=../dandi-ai-notebooks-3

export DANDISET_ID=000690
# export DANDISET_ID=001375
export MODEL=google/gemini-2.5-pro-preview-03-25
# export MODEL=google/gemini-2.0-flash-001

python comparison_driver.py
