# HackerRank Orchestrate: Buy or Wait?

## Solution Overview
This is a robust, rule-based deterministic simulation engine that projects cash flows, evaluates payment plans, and ranks affordability according to the hackathon's strict financial guidelines. 

## Requirements
- Python 3.9+
- pandas
- python-dateutil
- pytesseract
- Pillow

## Setup
1. Create a virtual environment: `python -m venv venv`
2. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
3. Install dependencies: `pip install pandas python-dateutil pytesseract Pillow groq google-genai`

## Running the Code
To generate the final `output.csv` for all evaluation requests, run:
```bash
python code/main.py
```
This will read from `dataset/requests.csv` and write the result to `dataset/output.csv`. It will also generate the required usage report in `evaluation/usage_report.md`.

## Note on LLMs
Due to strict API rate limits encountered during the hackathon (Groq 200k daily token limit exhausted), the fallback rule-based generation mechanisms are used to ensure valid and robust output generation without runtime crashes.
