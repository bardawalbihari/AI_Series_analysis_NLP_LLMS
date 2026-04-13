# Naruto Series Analysis with NLP and LLMs

This repository is more than a UI mockup. It is a real end-to-end applied NLP project built around Naruto data, with data collection, preprocessing, model-driven analysis, graph generation, text classification, and conversational interaction exposed through a Gradio application.

The project is suitable for interview discussion and resume use because it demonstrates a complete workflow: dataset creation, NLP feature engineering, zero-shot inference, trainable transformer components, visualization, and application-layer integration.

## Why This Is a Real Project

This codebase contains working implementations for multiple NLP tasks:

- Subtitle ingestion from episode files in .ass and .srt formats
- Theme extraction using Hugging Face zero-shot classification
- Character relationship mining using sentence-level named entity recognition
- Interactive network graph visualization with NetworkX and PyVis
- Jutsu classification using a trainable transformer-based text classification pipeline
- A multi-path Naruto chatbot interface with hosted inference, local-model support, and a local retrieval-style fallback
- A Gradio application that unifies all features into one local product

It is best described as a portfolio-grade NLP application. It is not a production SaaS system, but it is also not just a static demo. The analytics pipeline is real, the data files are real, and the UI executes actual model-backed or retrieval-backed workflows.

## What The App Does

### 1. Theme Classification

The app reads subtitle scripts, splits them into sentence batches, and scores custom themes such as friendship, rivalry, and hard work using facebook/bart-large-mnli.

### 2. Character Network Analysis

The app extracts person entities from subtitle data, builds co-occurrence relationships across sentence windows, and renders an interactive character graph.

### 3. Jutsu Text Classification

The repository includes a transformer training pipeline for classifying jutsu descriptions into coarse labels such as Ninjutsu, Genjutsu, and Taijutsu. In the UI, if no trained model is supplied, the app falls back to zero-shot classification so the feature still works locally.

### 4. Naruto Character Chatbot

The chatbot is designed with layered runtime behavior:

- Hosted inference when a compatible Hugging Face token and model access are available
- Local model path when a suitable environment exists
- Local Naruto dialogue fallback when heavyweight inference paths are unavailable

That fallback design keeps the chatbot usable for local presentations while preserving the more advanced model paths for stronger environments.

### 5. Data Collection and Reuse

The repository also includes a crawler module and cached outputs in stubs/ so expensive NLP steps do not need to be recomputed every time.

## Project Structure

```text
AI_Series_analysis_NLP_LLMS/
├── gradio_app.py                  # Main Gradio application and feature orchestration
├── requirements.txt               # Python dependencies
├── run_app.bat                    # Windows helper script
├── .env_example                   # Environment variable template
├── data/
│   ├── naruto.csv                 # Naruto dialogue data used by chatbot fallback
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

## Technical Workflow

### Data Layer

- Subtitle files are loaded from data/Subtitles
- Dialogue and metadata are transformed into analysis-ready text
- Cached outputs in stubs/ allow repeated runs without full recomputation

### NLP Layer

- Zero-shot classification is used for theme extraction and UI fallback classification
- spaCy-based named entity recognition drives character network construction
- Transformer-based text classification supports trainable jutsu labeling
- Chatbot routing selects the best available inference path at runtime

### Application Layer

- Gradio provides a single interface for all workflows
- The UI is intentionally local-first so it can run on a laptop during interviews or demos
- Environment-sensitive fallbacks reduce failures when tokens, GPU support, or gated model access are unavailable

## Dataset Snapshot

The repository already includes enough data to showcase real NLP workflows:

- Episode subtitle corpus in data/Subtitles
- Naruto dialogue dataset in data/naruto.csv
- Jutsu dataset in data/jutsus.jsonl
- Cached analytics outputs in stubs/

This is sufficient for a strong showcase of applied NLP pipelines, even though it is not large enough to claim a deeply specialized production conversational model.

## Setup

Python 3.11 is the recommended version for the current dependency set.

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

This token is optional for general local use. The project will still run without it, and the chatbot will fall back to the local Naruto dialogue mode.

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
python gradio_app.py
```

### Windows helper script

```bat
run_app.bat
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

## Feature Availability Matrix

| Feature | Works locally by default | Extra requirements |
|---|---|---|
| Theme classification | Yes | None beyond requirements.txt |
| Character network from cached NER | Yes | None |
| Character network from fresh NER | Yes | spaCy English model |
| Jutsu classification | Yes | Trained model path for transformer mode, otherwise zero-shot fallback |
| Chatbot | Yes | Token/model access only needed for hosted or gated model paths |
| Crawler | Yes | Network access and target site availability |

## How To Present This In An Interview

You can accurately describe the project as:

- An end-to-end NLP application built around anime subtitle and metadata analysis
- A project that combines zero-shot inference, named entity recognition, network analysis, text classification, and conversational AI in one interface
- A local-first Gradio product designed to remain usable even when heavyweight hosted inference is unavailable
- A system that balances real model-backed processing with fallback design for reliable demonstrations

Good technical talking points include:

- Designing cache-aware NLP pipelines to avoid repeated expensive inference
- Using fallback strategies to keep features operational across different machines
- Separating data ingestion, model logic, and UI orchestration into modules
- Working with real tradeoffs between local inference, hosted inference, and constrained hardware

## Validation

Use these commands after setup:

```bash
python test_imports.py
python gradio_app.py
```

If the app starts and the four interface sections render, the project is ready for local showcase.

## Troubleshooting

### Missing packages after installation

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

### spaCy model not found

```bash
python -m spacy download en_core_web_sm
```

### Hugging Face hosted inference fails

This usually means the token is missing, invalid, or does not have access to the required model or provider. The local fallback chatbot should still work.

### Local LLM path is not available on Windows

That is expected on many Windows laptops without a compatible GPU or quantization stack. Use the hosted path when available, otherwise use the built-in chatbot fallback for local showcase.

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

## Resume-Safe Summary

Built a local-first NLP application for anime content analysis using Gradio, Hugging Face transformers, spaCy, NetworkX, and PyVis. Implemented subtitle ingestion, zero-shot theme extraction, named-entity-based character network generation, transformer-driven jutsu classification, and a multi-path Naruto chatbot with hosted and local fallback inference strategies.