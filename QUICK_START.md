# Quick Start

Use this file when you want the shortest path to running the project locally. The full project explanation, architecture, dataset notes, and interview-ready positioning are documented in README.md.

## What You Get

This repository is an end-to-end NLP portfolio project built around Naruto data. It includes:

- Theme extraction from episode subtitles using zero-shot classification
- Character relationship graph generation using named entity recognition and NetworkX
- Jutsu text classification with a trainable transformer pipeline and a zero-shot fallback in the UI
- A Naruto chatbot with hosted, local-model, and local retrieval-based runtime paths
- A Gradio interface that ties all features together in one local application

## Recommended Environment

- Python 3.11
- 8 GB RAM minimum, 16 GB recommended
- Windows, macOS, or Linux
- Optional Hugging Face token for hosted or gated model access

## Setup

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

## Optional Configuration

Add a Hugging Face token to .env if you want access to hosted or gated model paths:

```env
huggingface_token=hf_your_token_here
```

If you do not add a token, the app still runs locally. The chatbot will use the built-in local fallback instead of hosted inference.

## Optional NLP Model Downloads

The character network feature can use cached NER output from stubs/ner_output.csv. If you want to regenerate NER from scratch, install a spaCy English model:

```bash
python -m spacy download en_core_web_sm
```

The theme classifier uses NLTK sentence tokenization. NLTK resources are downloaded automatically the first time the feature runs.

## Run

### Cross-platform

```bash
python gradio_app.py
```

### Windows launcher

```bat
run_app.bat
```

Open the app at http://127.0.0.1:7860

## Runtime Behavior

- Theme classification works locally from subtitle files or the cached CSV output
- Character network works from cached NER output immediately, or from fresh spaCy inference if a model is installed
- Text classification uses a trained model only if you supply a valid model path or Hugging Face repo; otherwise the UI falls back to zero-shot classification across Ninjutsu, Genjutsu, and Taijutsu
- Chatbot tries hosted inference first when a valid token is available, then attempts a local model path when suitable, and finally falls back to a local Naruto dialogue-based chatbot so the interface remains usable

## Quick Validation

After setup, these checks should pass:

```bash
python test_imports.py
python gradio_app.py
```

## Troubleshooting

### Imports fail after installation

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

### spaCy model missing

```bash
python -m spacy download en_core_web_sm
```

### Hugging Face access errors

Confirm that your token is valid and has permission for the model or provider you want to use. The rest of the app can still run without that access.

### Port 7860 is already in use

Set a different port before launch:

```bash
set GRADIO_SERVER_PORT=7861
python gradio_app.py
```

On macOS or Linux:

```bash
export GRADIO_SERVER_PORT=7861
python gradio_app.py
```
