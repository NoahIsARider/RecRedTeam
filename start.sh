#!/bin/bash
# Start the RecRedTeam Streamlit dashboard.
set -e

cd "$(dirname "$0")"

echo "== RecRedTeam dashboard =="
echo "Prereqs: pip install -e \".[dev,dashboard]\""
echo "LLM judge enabled if USER_LLM_API_KEY is set."

exec streamlit run app.py --server.port "${PORT:-8501}" --server.address 0.0.0.0
