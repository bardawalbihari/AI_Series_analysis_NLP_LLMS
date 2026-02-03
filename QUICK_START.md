# AI Series Analysis NLP LLMs - FIXED ✓

## Quick Start

Your project has been fixed and is ready to run! Here's what was done:

### Changes Made

#### 🐛 Bug Fixes
1. **character_chatbot.py** - Fixed 3 typos
   - `toknizer` → `tokenizer` (lines 103, 106, 150)
   - Would cause crashes when training models

2. **named_entity_recognizer.py** - Fixed path resolution
   - `pathlib.Path().parent.resolve()` → `pathlib.Path(__file__).parent.resolve()`
   - Would break relative module imports

#### ⚙️ Configuration Updates
3. **requirements.txt** - Fixed installation issues
   - Changed `git+https://github.com/huggingface/peft.git` to `peft==0.14.0`
   - Prevents git clone failures

4. **.env** - Created configuration file
   - Ready for HuggingFace token (get from https://huggingface.co/settings/tokens)

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or with conda
conda install -c conda-forge -r requirements.txt
```

### Configuration

Edit `.env` file and add your HuggingFace token:
```
huggingface_token=hf_YOUR_TOKEN_HERE
```

### Run the App

```bash
# Option 1: Direct run
python gradio_app.py

# Option 2: Use batch script (Windows)
run_app.bat

# Option 3: From Python
python -c "from gradio_app import main; main()"
```

The app will be available at: **http://localhost:7860**

## Project Structure

```
├── gradio_app.py                    # Main web interface
├── .env                             # Configuration (HF token)
├── requirements.txt                 # Dependencies
│
├── character_chatbot/               # Chatbot with LLMs
│   ├── character_chatbot.py        # ✓ FIXED
│   ├── character_chatbot_development.ipynb
│   └── __init__.py
│
├── character_network/               # Character relationship graphs
│   ├── character_netowork_generator.py
│   ├── named_entity_recognizer.py  # ✓ FIXED
│   ├── character_network_generator.ipynb
│   └── __init__.py
│
├── text_classification/             # Custom text classifier
│   ├── jutsu_classifier.py
│   ├── cleaner.py
│   ├── training_utils.py
│   ├── custom_trainer.py
│   ├── jutsu_classfier_development.ipynb
│   └── __init__.py
│
├── theme_classifier/                # Zero-shot theme classification
│   ├── theme_classifier.py
│   ├── theme_classification_development.ipynb
│   └── __init__.py
│
├── utils/                           # Shared utilities
│   ├── data_loader.py
│   └── __init__.py
│
├── crawler/                         # Web scraping (optional)
│   └── jutsu_crawler.py
│
├── data/                            # Data files
│   ├── naruto.csv
│   ├── jutsus.jsonl
│   └── Subtitles/
│
└── README.md                        # Original documentation
```

## Features

### 1. Theme Classification
Extract main themes from series using zero-shot classifiers

### 2. Character Network
Create interactive network graphs of character relationships using NER

### 3. Text Classification
Train custom LLM models to classify text (e.g., Jutsu types)

### 4. Character Chatbot
Chat with fine-tuned LLaMA 3 model acting as a series character

### 5. Data Crawler
Scrape web data to build custom datasets

## System Requirements

- **Python**: 3.8+
- **Memory**: 16GB RAM (8GB minimum)
- **Disk**: 50GB+ (for models and data)
- **GPU**: Optional (CUDA-compatible for faster processing)

## Dependencies

Main packages:
- `transformers` - Hugging Face models
- `gradio` - Web interface
- `torch` - Deep learning
- `peft` - LoRA fine-tuning
- `spacy` - NER and NLP
- `nltk` - Text processing
- `pyvis` - Network visualization
- `scikit-learn` - ML utilities
- `datasets` - Dataset handling
- `bitsandbytes` - Model quantization

## Troubleshooting

### Issue: ModuleNotFoundError
**Solution**: Ensure all dependencies are installed:
```bash
pip install -r requirements.txt --upgrade
```

### Issue: HuggingFace token error
**Solution**: Add token to `.env`:
```bash
echo "huggingface_token=hf_YOUR_TOKEN" > .env
```

### Issue: Out of memory
**Solution**: Use CPU mode or reduce batch sizes in model code

### Issue: Spacy model not found
**Solution**: Download the model:
```bash
python -m spacy download en_core_web_trf
# Or lighter version:
python -m spacy download en_core_web_sm
```

## Files Modified

✅ `character_chatbot/character_chatbot.py` - Fixed tokenizer typo
✅ `character_network/named_entity_recognizer.py` - Fixed path resolution  
✅ `requirements.txt` - Fixed peft dependency
✅ Created `.env` - Configuration file
✅ Created test_imports.py - Validation script
✅ Created FIX_SUMMARY.md - Detailed changes
✅ Created run_app.bat - Windows launcher

## Next Steps

1. ✓ Install dependencies: `pip install -r requirements.txt`
2. ✓ Configure HuggingFace token in `.env`
3. ✓ Download Spacy models: `python -m spacy download en_core_web_trf`
4. ✓ Run the app: `python gradio_app.py`
5. ✓ Open browser: `http://localhost:7860`

## Support

- **HuggingFace Docs**: https://huggingface.co/docs
- **Gradio Docs**: https://www.gradio.app/docs/
- **Spacy Docs**: https://spacy.io/
- **PyTorch Docs**: https://pytorch.org/docs

---

**Status**: ✅ READY TO RUN  
**Last Updated**: 2026-02-03  
**All Critical Issues Fixed**: YES
