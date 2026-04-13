# Naruto Series Analysis with NLP and LLMs

Naruto Series Analysis is a Gradio-based application for subtitle analysis, character network generation, jutsu classification, and Naruto-focused chat using local project data.

## Features

- Theme classification from subtitle files with zero-shot inference
- Character network generation from named entity extraction and co-occurrence analysis
- Jutsu text classification with a transformer pipeline and zero-shot fallback
- Grounded Naruto chatbot using dialogue data, jutsu data, curated facts, and optional hosted inference
- Cached outputs for repeated runs in stubs/

## Project Structure

```text
AI_Series_analysis_NLP_LLMS/
├── gradio_app.py                  # Main Gradio application and feature orchestration
├── requirements.txt               # Python dependencies
├── run_app.bat                    # Windows helper script
├── .env_example                   # Environment variable template
├── data/
│   ├── naruto.csv                 # Dialogue data used by the grounded chatbot
│   ├── naruto_rag_facts.jsonl     # Curated facts used by chatbot retrieval
│   ├── jutsus.jsonl               # Jutsu dataset for text classification
│   └── Subtitles/                 # Episode subtitle files (.ass and .srt)
├── stubs/
│   ├── ner_output.csv             # Cached named entity output
│   └── theme_classifier_output.csv # Cached theme scoring output
├── crawler/
│   └── jutsu_crawler.py           # Data collection script
├── character_chatbot/
│   └── character_chatbot.py       # Local LLM chatbot path
├── character_network/
│   ├── named_entity_recognizer.py
│   └── character_netowork_generator.py
├── text_classification/
│   └── jutsu_classifier.py
├── theme_classifier/
│   └── theme_classifier.py
└── utils/
    └── data_loader.py
```

## Data

- data/Subtitles contains episode subtitle files in .ass and .srt format
- data/naruto.csv contains dialogue lines used by the chatbot
- data/jutsus.jsonl contains jutsu names, types, and descriptions
- data/naruto_rag_facts.jsonl contains short curated facts used by retrieval
- stubs contains cached outputs for theme classification and NER

## Setup

Python 3.11 is the recommended version for the current dependency set.

## Quick Start

### Windows

Double-click run_app.bat

### Git Bash

```bash
bash run_app.sh
```

### Direct Python launch

```bash
./.venv/Scripts/python.exe gradio_app.py
```

The launcher scripts create .venv if needed, install dependencies, verify the core runtime stack, copy .env from .env_example, choose a free port starting from 7860, and start the app.

### Windows PowerShell

```powershell
cd AI_Series_analysis_NLP_LLMS
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env_example .env -ErrorAction SilentlyContinue
```

### Windows Git Bash

```bash
cd AI_Series_analysis_NLP_LLMS
py -3.11 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp -n .env_example .env
```

### macOS or Linux

```bash
cd AI_Series_analysis_NLP_LLMS
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp -n .env_example .env
```

## Environment Variables

Add a Hugging Face token to .env if you want hosted or gated model access:

```env
huggingface_token=hf_your_token_here
```

This token is optional. Without it, the chatbot still answers using the local knowledge base and fallback logic.

## Optional Downloads

### spaCy English Model

If you want to regenerate NER results instead of using the cached output, install one of the supported spaCy models:

```bash
python -m spacy download en_core_web_sm
```

The code will attempt en_core_web_trf first and then en_core_web_sm.

### NLTK Resources

The theme classification module downloads required tokenizer resources automatically on first use.

## Run The App

### Main command

```bash
./.venv/Scripts/python.exe gradio_app.py
```

### Windows helper script

```bat
run_app.bat
```

### Git Bash helper script

```bash
bash run_app.sh
```

The app launches locally at http://127.0.0.1:7860 by default.

If port 7860 is busy, change the port before launching.

### Windows Command Prompt

```bat
set GRADIO_SERVER_PORT=7861
python gradio_app.py
```

### PowerShell

```powershell
$env:GRADIO_SERVER_PORT=7861
python gradio_app.py
```

### macOS or Linux

```bash
export GRADIO_SERVER_PORT=7861
python gradio_app.py
```

## Runtime Notes

- Theme classification runs from subtitle files or cached theme output
- Character network runs from cached NER output or fresh spaCy inference
- Jutsu classification uses a supplied trained model when available, otherwise zero-shot fallback
- Chatbot retrieves local context first, then uses hosted or local model inference when available

## Validation

Use these commands after setup:

```bash
python test_imports.py
python gradio_app.py
```

If the app starts and the interface renders, the setup is working.

## Troubleshooting

### Missing packages after installation

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

If Torch or SciPy was partially installed, rerun the launcher script. It now checks the core runtime imports before startup and reinstalls dependencies automatically when the environment is broken.

### spaCy model not found

```bash
python -m spacy download en_core_web_sm
```

### Hugging Face hosted inference fails

This usually means the token is missing, invalid, or does not have access to the required model or provider. The local chatbot path should still work.

### Local LLM path is not available on Windows

That can happen on Windows systems without a compatible GPU or quantization stack. Hosted or grounded local fallback behavior is still available.

### Feature feels slow on first run

The first execution can download models and tokenizer resources. Later runs are faster because models and cached outputs are reused.

## Key Dependencies

- gradio
- transformers
- torch
- spacy
- pandas
- scikit-learn
- networkx
- pyvis
- python-dotenv
- datasets

