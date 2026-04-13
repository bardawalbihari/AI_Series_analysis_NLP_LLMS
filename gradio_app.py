import os
import re
from functools import lru_cache
from pathlib import Path

import gradio as gr
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_CHATBOT_MODEL = "AbdullahTarek/Naruto_Llama-3-8B"
DEFAULT_HOSTED_CHAT_MODEL = "meta-llama/Meta-Llama-3-8B-Instruct"
DEFAULT_TEXT_CLASSIFIER_MODEL = "demo-auto"
JUTSU_LABELS = ["Ninjutsu", "Genjutsu", "Taijutsu"]


def _resolve_path(path_str):
    path = Path(path_str)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _path_exists(path_str):
    return _resolve_path(path_str).exists()


def _repo_exists(repo_id):
    try:
        from huggingface_hub import repo_exists

        return repo_exists(repo_id, token=os.getenv("huggingface_token"))
    except Exception:
        return False


def _model_path_exists(model_path):
    if not model_path or model_path == DEFAULT_TEXT_CLASSIFIER_MODEL:
        return False
    return _path_exists(model_path) or _repo_exists(model_path)


def _clean_chat_text(text):
    cleaned = re.sub(r"\(.*?\)", " ", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _require_huggingface_token():
    huggingface_token = os.getenv("huggingface_token")
    if not huggingface_token:
        raise gr.Error(
            "Missing huggingface_token in .env. Add a Hugging Face token before using the chatbot."
        )
    return huggingface_token


class HostedNarutoChatbot:
    def __init__(self, model_name, huggingface_token):
        from huggingface_hub import InferenceClient

        self.client = InferenceClient(
            base_url="https://router.huggingface.co/v1",
            api_key=huggingface_token,
        )
        self.model_name = model_name
        self.system_prompt = (
            'You are Naruto Uzumaki from the anime "Naruto". '
            "Respond in-character, energetic, determined, and concise. "
            "Handle both everyday small-talk and Naruto-specific questions naturally."
        )

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt}]
        for user_message, assistant_message in history:
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": assistant_message})
        messages.append({"role": "user", "content": message})

        output = self.client.chat_completion(
            model=self.model_name,
            messages=messages,
            max_tokens=256,
            temperature=0.7,
            top_p=0.9,
        )
        return output.choices[0].message.content.strip()


class LocalNarutoDemoChatbot:
    def __init__(self, data_path):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        transcript_df = pd.read_csv(_resolve_path(data_path)).dropna(subset=["name", "line"])
        transcript_df["name"] = transcript_df["name"].astype(str).str.strip()
        naruto_lines = transcript_df.loc[transcript_df["name"] == "Naruto", "line"]
        self.lines = [_clean_chat_text(line) for line in naruto_lines.tolist()]
        self.lines = [line for line in self.lines if len(line) > 20]
        self.default_lines = [
            "I never go back on my word. That's my nindo, my ninja way!",
            "Believe it! I'm going to keep pushing until I figure this out.",
            "If you want to protect your friends, you don't give up halfway.",
        ]
        self.intent_responses = [
            (("hello", "hi", "hey", "yo"), "Hey! I'm Naruto Uzumaki. What's up? Believe it!"),
            (("how are you", "how're you", "hows it going"), "I'm fired up and ready to go! Nothing's gonna stop me from becoming Hokage."),
            (("who are you", "what is your name", "your name"), "I'm Naruto Uzumaki, future Hokage of the Hidden Leaf Village!"),
            (("what can you do", "help me", "can you help"), "I can chat with you, talk about Konoha, my friends, ramen, jutsu, and what it means to never give up."),
            (("thank you", "thanks"), "Heh, no problem! That's what comrades are for."),
            (("bye", "goodbye", "see you"), "See ya! Keep training and don't give up!"),
            (("favorite food", "favourite food", "ramen"), "Easy. Ramen. Ichiraku ramen is the best, no question."),
            (("hokage", "become hokage", "why hokage"), "I'm going to become Hokage so everyone acknowledges me and I can protect the village."),
            (("nindo", "ninja way"), "My ninja way is simple: I never go back on my word. That's my nindo!"),
            (("sasuke",), "Sasuke's my rival and my friend. Even when he pushes people away, I don't give up on him."),
            (("sakura",), "Sakura is strong, smart, and not someone you should underestimate."),
            (("kakashi",), "Kakashi-sensei acts lazy, but he's one of the smartest and strongest ninja around."),
            (("iruka",), "Iruka-sensei was one of the first people who really believed in me. I won't forget that."),
            (("kurama", "nine tails", "nine-tailed fox"), "Kurama and I had a rough start, but real strength comes from understanding each other."),
            (("konoha", "leaf village", "hidden leaf"), "Konoha is my home. No matter what happens, I'll protect it."),
            (("shadow clone", "clone jutsu"), "Shadow Clone Jutsu lets me make solid copies of myself. It's one of my signature moves."),
            (("chakra",), "Chakra is the energy ninja use for techniques. Controlling it properly is a huge part of becoming strong."),
            (("ninjutsu",), "Ninjutsu are ninja techniques powered by chakra. Shadow Clones, Rasengan, all that good stuff."),
            (("genjutsu",), "Genjutsu messes with your senses. You've gotta break the illusion if you want to win."),
            (("taijutsu",), "Taijutsu is hand-to-hand combat. No tricks, just pure fighting skill and guts."),
            (("rasengan",), "The Rasengan is a high-level chakra technique. Hard to master, but totally worth it."),
            (("dream", "goal"), "My goal is to become Hokage and earn everyone's respect the right way."),
        ]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.embeddings = self.vectorizer.fit_transform(self.lines)
        self.cosine_similarity = cosine_similarity

    def _normalize_message(self, message):
        normalized = _clean_chat_text(message).lower()
        normalized = re.sub(r"[^a-z0-9\s'-]", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    def _get_curated_response(self, message):
        normalized = self._normalize_message(message)

        if not normalized:
            return self.default_lines[0]

        for keywords, response in self.intent_responses:
            if any(re.search(rf"\b{re.escape(keyword)}\b", normalized) for keyword in keywords):
                return response

        if normalized.endswith("?") or normalized.startswith(("what", "why", "how", "when", "where", "can ", "do ", "are ")):
            return (
                "Heh, I might not know every single thing, but ask me about my friends, Konoha, ramen, jutsu, or becoming Hokage and I've got plenty to say."
            )

        return None

    def chat(self, message, history):
        used_responses = {assistant_message.strip() for _, assistant_message in history if assistant_message}
        curated_response = self._get_curated_response(message)
        if curated_response is not None:
            return curated_response

        query_parts = [message]
        if history:
            query_parts.extend(text for pair in history[-2:] for text in pair if text)
        query = _clean_chat_text(" ".join(query_parts))

        if not query:
            return self.default_lines[0]

        similarity_scores = self.cosine_similarity(
            self.vectorizer.transform([query]),
            self.embeddings,
        ).ravel()

        ranked_indexes = similarity_scores.argsort()[::-1]
        for index in ranked_indexes[:10]:
            candidate = self.lines[index]
            if candidate not in used_responses:
                if similarity_scores[index] < 0.05:
                    break
                return candidate

        return self.default_lines[len(history) % len(self.default_lines)]


class CharacterChatbotFacade:
    def __init__(self):
        self.primary_chatbot = None
        self.primary_disabled = False
        self.primary_error = None
        self.local_model_attempted = False
        self.local_model_chatbot = None
        self.demo_chatbot = None

    def _get_primary_chatbot(self):
        if self.primary_disabled:
            return None
        if self.primary_chatbot is not None:
            return self.primary_chatbot

        token = os.getenv("huggingface_token")
        if not token:
            self.primary_disabled = True
            self.primary_error = "Missing huggingface_token in .env."
            return None

        self.primary_chatbot = HostedNarutoChatbot(
            os.getenv("NARUTO_CHATBOT_HOSTED_MODEL", DEFAULT_HOSTED_CHAT_MODEL),
            token,
        )
        return self.primary_chatbot

    def _should_try_local_model(self):
        if os.getenv("NARUTO_CHATBOT_FORCE_LOCAL_MODEL") == "1":
            return True

        if os.name == "nt":
            return False

        try:
            import torch

            return torch.cuda.is_available()
        except Exception:
            return False

    def _get_local_model_chatbot(self):
        if self.local_model_attempted:
            return self.local_model_chatbot

        self.local_model_attempted = True
        if not self._should_try_local_model():
            return None

        from character_chatbot import CharacterChatBot

        self.local_model_chatbot = CharacterChatBot(
            DEFAULT_CHATBOT_MODEL,
            data_path=str(_resolve_path("data/naruto.csv")),
            huggingface_token=os.getenv("huggingface_token"),
        )
        return self.local_model_chatbot

    def _get_demo_chatbot(self):
        if self.demo_chatbot is None:
            self.demo_chatbot = LocalNarutoDemoChatbot("data/naruto.csv")
        return self.demo_chatbot

    def chat(self, message, history):
        primary_chatbot = self._get_primary_chatbot()
        if primary_chatbot is not None:
            try:
                return primary_chatbot.chat(message, history)
            except Exception as exc:
                self.primary_chatbot = None
                self.primary_disabled = True
                self.primary_error = str(exc)

        try:
            local_model_chatbot = self._get_local_model_chatbot()
            if local_model_chatbot is not None:
                return local_model_chatbot.chat(message, history)
        except Exception as exc:
            self.primary_error = str(exc)

        return self._get_demo_chatbot().chat(message, history)


@lru_cache(maxsize=1)
def _get_zero_shot_classifier():
    import torch
    from transformers import pipeline

    device = 0 if torch.cuda.is_available() else -1
    return pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=device,
    )


@lru_cache(maxsize=1)
def _get_character_chatbot():
    return CharacterChatbotFacade()

def get_themes(theme_list_str,subtitles_path,save_path):
    from theme_classifier import ThemeClassifier

    theme_list = [theme.strip() for theme in theme_list_str.split(',') if theme.strip()]
    theme_classifier = ThemeClassifier(theme_list)
    output_df = theme_classifier.get_themes(subtitles_path,save_path)

    for theme in theme_list:
        if theme not in output_df.columns:
            output_df[theme] = 0.0

    # Remove dialogue from the theme list
    theme_list = [theme for theme in theme_list if theme != 'dialogue']
    output_df = output_df[theme_list]

    output_df = output_df[theme_list].sum().reset_index()
    output_df.columns = ['Theme','Score']

    output_chart = gr.BarPlot(
        output_df,
        x="Theme",
        y="Score",
        title="Series Themes",
        tooltip=["Theme","Score"],
        vertical=False,
        width=500,
        height=260
    )

    return output_chart

def get_character_network(subtitles_path,ner_path):
    from character_network import NamedEntityRecognizer, CharacterNetworkGenerator

    ner = NamedEntityRecognizer()
    ner_df = ner.get_ners(subtitles_path,ner_path)

    character_network_generator = CharacterNetworkGenerator()
    relationship_df = character_network_generator.generate_character_network(ner_df)
    html = character_network_generator.draw_network_graph(relationship_df)

    return html

def classify_text(text_classifcation_model,text_classifcation_data_path,text_to_classify):
    if _model_path_exists(text_classifcation_model):
        from text_classification import JutsuClassifier

        jutsu_classifier = JutsuClassifier(model_path = text_classifcation_model,
                                           data_path = text_classifcation_data_path,
                                           huggingface_token = os.getenv('huggingface_token'))
        
        output = jutsu_classifier.classify_jutsu(text_to_classify)
        output = output[0]
        return output

    zero_shot_classifier = _get_zero_shot_classifier()
    output = zero_shot_classifier(
        text_to_classify,
        JUTSU_LABELS,
        multi_label=False,
        hypothesis_template="This jutsu belongs to {}.",
    )
    return f"{output['labels'][0]} (demo fallback, score={output['scores'][0]:.2f})"

def chat_with_character_chatbot(message, history):
    character_chatbot = _get_character_chatbot()
    output = character_chatbot.chat(message, history)
    if isinstance(output, dict):
        return output.get('content', '').strip()
    return str(output).strip()


def main():
    with gr.Blocks() as iface:
        gr.Markdown(
            "# Naruto Series Analysis\n"
            "This UI starts locally on your machine. The chatbot will use hosted or local Llama inference when available, and automatically fall back to a local demo chatbot when those paths are unavailable."
        )

        # Theme Classification Section
        with gr.Row():
            with gr.Column():
                gr.HTML("<h1>Theme Classification (Zero Shot Claasifiers)</h1>")
                with gr.Row():
                    with gr.Column():
                        plot = gr.BarPlot()
                    with gr.Column():
                        theme_list = gr.Textbox(label="Themes", value="friendship, rivalry, hard work, dialogue")
                        subtitles_path = gr.Textbox(label="Subtitles or script Path", value="data/Subtitles")
                        save_path = gr.Textbox(label="Save Path", value="stubs/theme_classifier_output.csv")
                        get_themes_button =gr.Button("Get Themes")
                        get_themes_button.click(get_themes, inputs=[theme_list,subtitles_path,save_path], outputs=[plot])

        # Character Network Section
        with gr.Row():
            with gr.Column():
                gr.HTML("<h1>Character Network (NERs and Graphs)</h1>")
                with gr.Row():
                    with gr.Column():
                        network_html = gr.HTML()
                    with gr.Column():
                        subtitles_path = gr.Textbox(label="Subtutles or Script Path", value="data/Subtitles")
                        ner_path = gr.Textbox(label="NERs save path", value="stubs/ner_output.csv")
                        get_network_graph_button = gr.Button("Get Character Network")
                        get_network_graph_button.click(get_character_network, inputs=[subtitles_path,ner_path], outputs=[network_html])

        # Text Classification with LLMs
        with gr.Row():
            with gr.Column():
                gr.HTML("<h1>Text Classification with LLMs</h1>")
                with gr.Row():
                    with gr.Column():
                        text_classification_output = gr.Textbox(label="Text Classification Output")
                    with gr.Column():
                        text_classifcation_model = gr.Textbox(label='Model Path', value=DEFAULT_TEXT_CLASSIFIER_MODEL)
                        text_classifcation_data_path = gr.Textbox(label='Data Path', value='data/jutsus.jsonl')
                        text_to_classify = gr.Textbox(label='Text input', value='Shadow Clone Jutsu creates copies of the user to overwhelm the enemy.')
                        classify_text_button = gr.Button("Clasify Text (Jutsu)")
                        classify_text_button.click(classify_text, inputs=[text_classifcation_model,text_classifcation_data_path,text_to_classify], outputs=[text_classification_output])

        # Character Chatbot Section
        with gr.Row():
            with gr.Column():
                gr.HTML("<h1>Character Chatbot</h1>")
                gr.ChatInterface(chat_with_character_chatbot)

    iface.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
        share=False,
        _frontend=False,
    )
            

if __name__ == '__main__':
    main()
