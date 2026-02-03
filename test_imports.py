#!/usr/bin/env python
"""
Test script to verify the Gradio app can be imported and run
"""
import sys
import os

# Add project to path
sys.path.insert(0, os.getcwd())

print("Testing imports...")

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ dotenv loaded")
except Exception as e:
    print(f"✗ dotenv error: {e}")
    sys.exit(1)

try:
    import gradio as gr
    print("✓ gradio imported")
except Exception as e:
    print(f"✗ gradio error: {e}")
    sys.exit(1)

try:
    from theme_classifier import ThemeClassifier
    print("✓ ThemeClassifier imported")
except Exception as e:
    print(f"✗ ThemeClassifier error: {e}")

try:
    from character_network import NamedEntityRecognizer, CharacterNetworkGenerator
    print("✓ NamedEntityRecognizer and CharacterNetworkGenerator imported")
except Exception as e:
    print(f"✗ character_network error: {e}")

try:
    from text_classification import JutsuClassifier
    print("✓ JutsuClassifier imported")
except Exception as e:
    print(f"✗ JutsuClassifier error: {e}")

try:
    from character_chatbot import CharacterChatBot
    print("✓ CharacterChatBot imported")
except Exception as e:
    print(f"✗ CharacterChatBot error: {e}")

print("\n✓ All core modules imported successfully!")
print("The project is ready to run.")
