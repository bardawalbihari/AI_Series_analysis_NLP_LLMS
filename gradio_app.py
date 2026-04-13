import html
import os
import re
import socket
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
DEFAULT_RAG_FACTS_PATH = "data/naruto_rag_facts.jsonl"
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


def _find_available_port(start_port, host="127.0.0.1", max_attempts=20):
    port = start_port
    for _ in range(max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind((host, port))
                return port
            except OSError:
                port += 1
    raise RuntimeError(f"Could not find an open port starting at {start_port}.")


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
        self.rag_chatbot = None

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

    def _get_rag_chatbot(self):
        if self.rag_chatbot is None:
            from character_chatbot import GroundedNarutoRAGChatbot

            self.rag_chatbot = GroundedNarutoRAGChatbot(
                repo_root=REPO_ROOT,
                transcript_path="data/naruto.csv",
                jutsu_path="data/jutsus.jsonl",
                facts_path=DEFAULT_RAG_FACTS_PATH,
                model_name=os.getenv("NARUTO_CHATBOT_HOSTED_MODEL", DEFAULT_HOSTED_CHAT_MODEL),
                huggingface_token=os.getenv("huggingface_token"),
            )
        return self.rag_chatbot

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

        return self._get_rag_chatbot().chat(message, history)


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


def _empty_chat_markup():
    return """
    <div class='qa-empty'>
        <div class='qa-empty-title'>Ask a Naruto question</div>
        <div class='qa-empty-copy'>Enter a question above and the generated answer will appear here in a clean stacked view.</div>
    </div>
    """


def _render_chat_response(history):
    if not history:
        return _empty_chat_markup()

    cards = []
    for turn_index, (message, response) in enumerate(history, start=1):
        safe_message = html.escape(str(message).strip())
        safe_response = html.escape(str(response).strip()).replace("\n", "<br>")
        cards.append(
            f"""
            <div class='qa-turn'>
                <div class='qa-turn-index'>Turn {turn_index}</div>
                <div class='qa-card qa-question'>
                    <div class='qa-label'>Question</div>
                    <div class='qa-text'>{safe_message}</div>
                </div>
                <div class='qa-card qa-answer'>
                    <div class='qa-label'>Naruto Chat</div>
                    <div class='qa-text'>{safe_response}</div>
                </div>
            </div>
            """
        )

    return f"<div class='qa-thread'>{''.join(cards)}</div>"


def ask_character_chatbot(message, history):
    cleaned_message = str(message or "").strip()
    if not cleaned_message:
        raise gr.Error("Enter a question before generating a response.")

    history = history or []
    response = chat_with_character_chatbot(cleaned_message, history)
    updated_history = history + [(cleaned_message, response)]
    return _render_chat_response(updated_history), updated_history, ""


def clear_character_chatbot_panel():
    return _empty_chat_markup(), [], ""


APP_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #f3ede3;
    --surface: rgba(255, 252, 247, 0.94);
    --surface-strong: #fffdf9;
    --surface-soft: rgba(255, 248, 239, 0.84);
    --border: rgba(43, 59, 74, 0.1);
    --ink: #15202b;
    --muted: #617080;
    --accent: #167c80;
    --accent-deep: #114b5f;
    --accent-soft: #d9eeef;
    --gold: #7d9fc0;
    --theme-accent: #1f8a70;
    --network-accent: #2d6a9f;
    --classify-accent: #3f5c9a;
    --chat-accent: #10a37f;
    --shadow-lg: 0 30px 70px rgba(42, 60, 79, 0.12);
    --shadow-md: 0 18px 36px rgba(42, 60, 79, 0.08);
}

body, .gradio-container {
    font-family: 'Manrope', sans-serif;
    background:
        radial-gradient(circle at top left, rgba(22, 124, 128, 0.12), transparent 24%),
        radial-gradient(circle at 88% 8%, rgba(125, 159, 192, 0.16), transparent 18%),
        linear-gradient(180deg, #f7f9fb 0%, #e9eff3 100%);
    color: var(--ink);
}

.gradio-container {
    max-width: 1320px !important;
    padding-top: 28px !important;
    padding-bottom: 48px !important;
}

.app-shell {
    border: 1px solid var(--border);
    border-radius: 32px;
    padding: 30px;
    background: rgba(255, 249, 242, 0.7);
    backdrop-filter: blur(14px);
    box-shadow: var(--shadow-lg);
}

.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 14px;
    margin-bottom: 16px;
    padding: 0 4px;
}

.brand-lockup {
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-mark {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--accent-deep), var(--accent), var(--gold));
    box-shadow: 0 12px 24px rgba(17, 75, 95, 0.2);
}

.brand-copy h1 {
    margin: 0;
    font-family: 'Fraunces', serif;
    font-size: 1.3rem;
    line-height: 1;
}

.brand-copy p {
    margin: 4px 0 0;
    color: var(--muted);
    font-size: 0.9rem;
}

.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 10px 14px;
    border-radius: 999px;
    border: 1px solid rgba(16, 163, 127, 0.16);
    background: rgba(16, 163, 127, 0.08);
    color: #176a60;
    font-size: 0.88rem;
    font-weight: 700;
}

.hero {
    background:
        linear-gradient(140deg, rgba(17, 75, 95, 0.98), rgba(22, 124, 128, 0.92) 50%, rgba(125, 159, 192, 0.94));
    color: #f5fbfc;
    border-radius: 30px;
    padding: 34px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 24px 52px rgba(17, 75, 95, 0.22);
}

.hero::after {
    content: '';
    position: absolute;
    right: -40px;
    bottom: -60px;
    width: 240px;
    height: 240px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
}

.hero::before {
    content: '';
    position: absolute;
    top: -60px;
    right: 140px;
    width: 180px;
    height: 180px;
    border-radius: 50%;
    border: 1px solid rgba(255, 255, 255, 0.12);
}

.hero-layout {
    position: relative;
    z-index: 1;
    display: flex;
    flex-wrap: wrap;
    gap: 28px;
}

.hero-main {
    flex: 1 1 620px;
    min-width: 0;
}

.hero-side {
    flex: 0 1 300px;
    min-width: 260px;
    padding: 18px;
    border-radius: 22px;
    background: rgba(245, 251, 252, 0.12);
    border: 1px solid rgba(245, 251, 252, 0.16);
    backdrop-filter: blur(10px);
}

.hero-kicker {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 7px 12px;
    border-radius: 999px;
    background: rgba(245, 251, 252, 0.14);
    border: 1px solid rgba(245, 251, 252, 0.2);
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.hero h1 {
    margin: 16px 0 0;
    font-family: 'Fraunces', serif;
    font-size: clamp(2.4rem, 4.6vw, 4rem);
    line-height: 0.96;
    letter-spacing: -0.04em;
    max-width: 680px;
}

.hero p {
    margin: 16px 0 0;
    max-width: 700px;
    color: rgba(245, 251, 252, 0.9);
    font-size: 1.02rem;
    line-height: 1.65;
}

.hero-grid {
    margin-top: 18px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
}

.hero-pill {
    padding: 10px 13px;
    border-radius: 999px;
    background: rgba(245, 251, 252, 0.12);
    border: 1px solid rgba(245, 251, 252, 0.12);
    font-size: 0.88rem;
    font-weight: 600;
}

.hero-side h3 {
    margin: 0;
    font-size: 1rem;
    letter-spacing: 0.02em;
}

.hero-side p {
    margin: 10px 0 0;
    font-size: 0.94rem;
    line-height: 1.6;
    color: rgba(245, 251, 252, 0.85);
}

.hero-list {
    margin: 14px 0 0;
    padding: 0;
    list-style: none;
}

.hero-list li {
    padding: 10px 0;
    border-top: 1px solid rgba(245, 251, 252, 0.12);
    font-size: 0.92rem;
}

.overview-strip {
    margin: 18px 0 20px;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
}

.overview-card {
    padding: 18px 18px 16px;
    border-radius: 22px;
    background: var(--surface);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-md);
}

.overview-card .label {
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
}

.overview-card .value {
    display: block;
    margin-top: 8px;
    font-family: 'Fraunces', serif;
    font-size: 1.5rem;
    line-height: 1;
}

.overview-card .meta {
    display: block;
    margin-top: 8px;
    color: var(--muted);
    font-size: 0.9rem;
}

.section-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 24px;
    padding: 24px;
    box-shadow: var(--shadow-md);
    position: relative;
}

.section-card::before {
    content: '';
    position: absolute;
    inset: 0 0 auto 0;
    height: 4px;
    border-radius: 22px 22px 0 0;
    background: var(--accent);
}

.theme-card::before {
    background: var(--theme-accent);
}

.network-card::before {
    background: var(--network-accent);
}

.classify-card::before {
    background: var(--classify-accent);
}

.chat-card::before {
    background: var(--chat-accent);
}

.section-header {
    margin-bottom: 20px;
}

.section-header .eyebrow {
    display: inline-block;
    margin-bottom: 8px;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--accent-deep);
}

.section-header h2 {
    margin: 0;
    font-family: 'Fraunces', serif;
    font-size: 1.8rem;
    line-height: 1.05;
    color: var(--ink);
}

.section-header p {
    margin: 8px 0 0;
    color: var(--muted);
    font-size: 0.95rem;
}

.workspace-tabs {
    margin-top: 8px;
}

.workspace-tabs .tab-nav {
    gap: 10px;
    background: transparent !important;
    border: none !important;
    margin-bottom: 16px;
}

.workspace-tabs .tab-nav button {
    border-radius: 999px !important;
    border: 1px solid rgba(83, 58, 35, 0.1) !important;
    background: rgba(255, 251, 246, 0.88) !important;
    color: var(--muted) !important;
    font-weight: 800 !important;
    padding: 12px 16px !important;
    box-shadow: 0 8px 18px rgba(78, 49, 22, 0.05);
}

.workspace-tabs .tab-nav button.selected {
    background: linear-gradient(135deg, var(--accent-deep), var(--accent)) !important;
    color: #f7fcfd !important;
    border-color: transparent !important;
}

.workspace-pane {
    min-height: 560px;
}

.control-stack {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.output-shell {
    padding: 14px;
    border-radius: 20px;
    background: var(--surface-strong);
    border: 1px solid rgba(83, 58, 35, 0.08);
    min-height: 360px;
}

.chat-shell {
    padding: 0;
    border-radius: 24px;
    background: #ffffff;
    border: 1px solid rgba(43, 59, 74, 0.08);
    overflow: hidden;
}

.section-footnote {
    margin-top: 14px;
    color: var(--muted);
    font-size: 0.9rem;
    line-height: 1.6;
}

.gr-button {
    border-radius: 16px !important;
    border: none !important;
    background: linear-gradient(135deg, var(--accent-deep), var(--accent)) !important;
    color: #f7fcfd !important;
    box-shadow: 0 14px 26px rgba(17, 75, 95, 0.18);
    font-weight: 800 !important;
    letter-spacing: 0.01em;
    min-height: 46px;
}

.gr-button:hover {
    filter: brightness(1.03);
}

.gr-textbox, .gr-html, .gr-chatbot, .gr-form, .gradio-html {
    border-radius: 18px !important;
}

.gr-box, .gr-panel {
    border-color: var(--border) !important;
}

label span,
.gr-form label,
.gr-block label {
    font-size: 0.82rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--muted) !important;
}

textarea,
input,
.gr-textbox textarea,
.gr-textbox input {
    background: rgba(255, 253, 248, 0.98) !important;
    border: 1px solid rgba(83, 58, 35, 0.12) !important;
    border-radius: 16px !important;
    color: var(--ink) !important;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
    min-height: 48px;
}

textarea:focus,
input:focus,
.gr-textbox textarea:focus,
.gr-textbox input:focus {
    border-color: rgba(217, 95, 45, 0.5) !important;
    box-shadow: 0 0 0 4px rgba(217, 95, 45, 0.12) !important;
}

.gr-chatbot {
    background: #ffffff !important;
    border: none !important;
}

.chat-input-area {
    padding: 18px 18px 14px;
    border-bottom: 1px solid rgba(43, 59, 74, 0.08);
    background: linear-gradient(180deg, #ffffff 0%, #f7fbfc 100%);
}

.chat-output-area {
    min-height: 430px;
    padding: 18px;
    background: #fbfdfe;
}

.qa-thread {
    max-width: 860px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 22px;
}

.qa-turn {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.qa-turn-index {
    align-self: flex-start;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(22, 124, 128, 0.08);
    color: var(--accent-deep);
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.qa-card {
    border-radius: 22px;
    padding: 18px 20px;
    border: 1px solid rgba(43, 59, 74, 0.08);
    background: #ffffff;
    box-shadow: 0 10px 24px rgba(42, 60, 79, 0.05);
}

.qa-question {
    background: #eef7f5;
    border-color: rgba(16, 163, 127, 0.14);
}

.qa-answer {
    background: #ffffff;
}

.qa-label {
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
}

.qa-text {
    font-size: 0.98rem;
    line-height: 1.75;
    color: var(--ink);
}

.qa-empty {
    max-width: 860px;
    min-height: 330px;
    margin: 0 auto;
    border: 1px dashed rgba(43, 59, 74, 0.14);
    border-radius: 24px;
    background: linear-gradient(180deg, #ffffff 0%, #f8fbfd 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 32px;
}

.qa-empty-title {
    font-family: 'Fraunces', serif;
    font-size: 1.7rem;
    line-height: 1.1;
}

.qa-empty-copy {
    margin-top: 10px;
    max-width: 560px;
    color: var(--muted);
    font-size: 0.98rem;
    line-height: 1.7;
}

.gradio-container .prose,
.gradio-container .markdown {
    color: var(--ink);
}

.plot-wrap,
.network-wrap,
.result-wrap {
    border-radius: 18px;
    background: rgba(255, 252, 247, 0.86);
    border: 1px solid rgba(83, 58, 35, 0.08);
    padding: 10px;
}

.chat-note {
    margin-top: 12px;
    color: var(--muted);
    font-size: 0.9rem;
    line-height: 1.5;
}

.app-footer {
    margin-top: 20px;
    padding-top: 14px;
    border-top: 1px solid rgba(43, 59, 74, 0.08);
    text-align: right;
    color: var(--muted);
    font-size: 0.92rem;
    letter-spacing: 0.02em;
}

@media (max-width: 768px) {
    .app-shell {
        padding: 14px;
    }

    .topbar {
        flex-direction: column;
        align-items: flex-start;
    }

    .hero {
        padding: 22px 18px;
    }

    .overview-strip {
        grid-template-columns: 1fr;
    }

    .section-card {
        padding: 18px;
    }

    .workspace-pane {
        min-height: auto;
    }
}
"""


APP_HEAD = """
<script>
(() => {
    if (window.__narutoChatHeadBindingAttached) {
        return;
    }

    window.__narutoChatHeadBindingAttached = true;
    document.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter' || event.shiftKey || event.isComposing) {
            return;
        }

        const activeElement = document.activeElement;
        if (!activeElement || activeElement.tagName !== 'TEXTAREA') {
            return;
        }

        const root = activeElement.closest('#naruto-chat-question');
        if (!root) {
            return;
        }

        const button = document.getElementById('naruto-chat-submit');
        if (!button) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();
        button.click();
    }, true);
})();
</script>
"""


def main():
    with gr.Blocks(css=APP_CSS, head=APP_HEAD, title="Naruto Series Analysis") as iface:
        with gr.Column(elem_classes=["app-shell"]):
            gr.HTML(
                """
                <div class='topbar'>
                    <div class='brand-lockup'>
                        <div class='brand-mark'></div>
                        <div class='brand-copy'>
                            <h1>Naruto Series Analysis</h1>
                            <p>NLP workspace for subtitle analysis, graphs, classification, and grounded chat.</p>
                        </div>
                    </div>
                    <div class='status-pill'>Grounded analysis workspace</div>
                </div>
                <section class='hero'>
                    <div class='hero-layout'>
                        <div class='hero-main'>
                            <div class='hero-kicker'>Naruto NLP Workspace</div>
                            <h1>One interface for story analysis, relationship mapping, jutsu classification, and character-grounded chat.</h1>
                            <p>This workspace turns subtitle and metadata assets into an interactive analysis app with reusable local outputs, structured feature flows, and a cleaner interface for exploring the project.</p>
                            <div class='hero-grid'>
                                <div class='hero-pill'>Theme scoring from subtitles</div>
                                <div class='hero-pill'>Graph-based character mapping</div>
                                <div class='hero-pill'>Jutsu type classification</div>
                                <div class='hero-pill'>Grounded Naruto knowledge chat</div>
                            </div>
                        </div>
                        <div class='hero-side'>
                            <h3>Workspace Flow</h3>
                            <p>Use the tabs below to move between analysis modules without the page feeling crowded.</p>
                            <ul class='hero-list'>
                                <li>Start with theme or graph generation from subtitle data.</li>
                                <li>Validate individual descriptions in the jutsu classifier.</li>
                                <li>Use the chatbot tab for grounded character and concept questions.</li>
                            </ul>
                        </div>
                    </div>
                </section>
                <section class='overview-strip'>
                    <div class='overview-card'>
                        <span class='label'>Theme Engine</span>
                        <span class='value'>Zero-shot</span>
                        <span class='meta'>Custom theme scoring on subtitle batches.</span>
                    </div>
                    <div class='overview-card'>
                        <span class='label'>Network View</span>
                        <span class='value'>Entity Graph</span>
                        <span class='meta'>Character relationships built from NER output.</span>
                    </div>
                    <div class='overview-card'>
                        <span class='label'>Classifier</span>
                        <span class='value'>Ninjutsu / Genjutsu / Taijutsu</span>
                        <span class='meta'>Model-backed classification with fallback support.</span>
                    </div>
                    <div class='overview-card'>
                        <span class='label'>Chat Layer</span>
                        <span class='value'>Grounded RAG</span>
                        <span class='meta'>Answers based on local dialogue, facts, and jutsu data.</span>
                    </div>
                </section>
                """
            )

            with gr.Tabs(elem_classes=["workspace-tabs"]):
                with gr.Tab("Theme Analysis"):
                    with gr.Column(elem_classes=["section-card", "theme-card", "workspace-pane"]):
                        gr.HTML(
                            """
                            <div class='section-header'>
                                <div class='eyebrow'>Analysis</div>
                                <h2>Theme Classification</h2>
                                <p>Score custom narrative themes from subtitle files and inspect the aggregate signal in a dedicated analysis view.</p>
                            </div>
                            """
                        )
                        with gr.Row(equal_height=True):
                            with gr.Column(scale=8, elem_classes=["output-shell"]):
                                plot = gr.BarPlot(height=340)
                            with gr.Column(scale=4, elem_classes=["control-stack"]):
                                theme_list = gr.Textbox(label="Themes", value="friendship, rivalry, hard work, dialogue")
                                subtitles_path = gr.Textbox(label="Subtitles Path", value="data/Subtitles")
                                save_path = gr.Textbox(label="Cached Output Path", value="stubs/theme_classifier_output.csv")
                                get_themes_button = gr.Button("Generate Theme Scores")
                                get_themes_button.click(get_themes, inputs=[theme_list,subtitles_path,save_path], outputs=[plot])
                                gr.HTML("<div class='section-footnote'>Use a short comma-separated theme list to keep the result chart readable and presentation-friendly.</div>")

                with gr.Tab("Character Network"):
                    with gr.Column(elem_classes=["section-card", "network-card", "workspace-pane"]):
                        gr.HTML(
                            """
                            <div class='section-header'>
                                <div class='eyebrow'>Graph</div>
                                <h2>Character Network</h2>
                                <p>Generate a relationship graph from subtitle entities and reuse cached named-entity output for faster runs.</p>
                            </div>
                            """
                        )
                        with gr.Row(equal_height=True):
                            with gr.Column(scale=8, elem_classes=["output-shell"]):
                                network_html = gr.HTML()
                            with gr.Column(scale=4, elem_classes=["control-stack"]):
                                network_subtitles_path = gr.Textbox(label="Subtitles Path", value="data/Subtitles")
                                ner_path = gr.Textbox(label="NER Output Path", value="stubs/ner_output.csv")
                                get_network_graph_button = gr.Button("Generate Character Graph")
                                get_network_graph_button.click(get_character_network, inputs=[network_subtitles_path,ner_path], outputs=[network_html])
                                gr.HTML("<div class='section-footnote'>Cached NER output makes this view much faster during live demos and repeated walkthroughs.</div>")

                with gr.Tab("Jutsu Classifier"):
                    with gr.Column(elem_classes=["section-card", "classify-card", "workspace-pane"]):
                        gr.HTML(
                            """
                            <div class='section-header'>
                                <div class='eyebrow'>Classifier</div>
                                <h2>Jutsu Classification</h2>
                                <p>Validate a jutsu description against the local classifier path or the zero-shot fallback when a trained model is not available.</p>
                            </div>
                            """
                        )
                        with gr.Row(equal_height=True):
                            with gr.Column(scale=5, elem_classes=["control-stack"]):
                                text_classifcation_model = gr.Textbox(label='Model Path', value=DEFAULT_TEXT_CLASSIFIER_MODEL)
                                text_classifcation_data_path = gr.Textbox(label='Data Path', value='data/jutsus.jsonl')
                                text_to_classify = gr.Textbox(label='Text Input', value='Shadow Clone Jutsu creates copies of the user to overwhelm the enemy.', lines=7)
                                classify_text_button = gr.Button("Classify Jutsu")
                            with gr.Column(scale=7, elem_classes=["output-shell"]):
                                text_classification_output = gr.Textbox(label="Classification Output", lines=12)
                        classify_text_button.click(classify_text, inputs=[text_classifcation_model,text_classifcation_data_path,text_to_classify], outputs=[text_classification_output])

                with gr.Tab("Naruto Chat"):
                    with gr.Column(elem_classes=["section-card", "chat-card", "workspace-pane"]):
                        gr.HTML(
                            """
                            <div class='section-header'>
                                <div class='eyebrow'>Chat</div>
                                <h2>Character Chatbot</h2>
                                <p>Ask a grounded Naruto question and review the response in a clean stacked question-and-answer layout.</p>
                            </div>
                            """
                        )
                        chat_history = gr.State([])
                        with gr.Column(elem_classes=["chat-shell"]):
                            with gr.Column(elem_classes=["chat-input-area"]):
                                chatbot_question = gr.Textbox(
                                    label="Ask Naruto Chat",
                                    placeholder="Ask who Naruto is, how Rasengan works, what Team 7 is, or any grounded Naruto question...",
                                    lines=3,
                                    elem_id="naruto-chat-question",
                                )
                                with gr.Row():
                                    ask_button = gr.Button("Generate Response", elem_id="naruto-chat-submit")
                                    clear_button = gr.Button("Clear", variant="secondary")
                            with gr.Column(elem_classes=["chat-output-area"]):
                                chatbot_response = gr.HTML(
                                    """
                                    <div class='qa-empty'>
                                        <div class='qa-empty-title'>Ask a Naruto question</div>
                                        <div class='qa-empty-copy'>Enter a question above and the generated answer will appear here in a clean stacked view.</div>
                                    </div>
                                    """
                                )
                        ask_button.click(
                            ask_character_chatbot,
                            inputs=[chatbot_question, chat_history],
                            outputs=[chatbot_response, chat_history, chatbot_question],
                        )
                        chatbot_question.submit(
                            ask_character_chatbot,
                            inputs=[chatbot_question, chat_history],
                            outputs=[chatbot_response, chat_history, chatbot_question],
                        )
                        clear_button.click(
                            clear_character_chatbot_panel,
                            outputs=[chatbot_response, chat_history, chatbot_question],
                        )
                        gr.HTML("<div class='chat-note'>The chatbot retrieves context from local project data before using hosted or local generation.</div>")

            gr.HTML("<div class='app-footer'>Bardawal Bihari</div>")

    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    requested_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    server_port = _find_available_port(requested_port, host=server_name)

    iface.launch(
        server_name=server_name,
        server_port=server_port,
        share=False,
        _frontend=False,
    )
            

if __name__ == '__main__':
    main()
