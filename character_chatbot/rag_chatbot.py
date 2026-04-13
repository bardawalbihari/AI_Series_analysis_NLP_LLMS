import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd


def _clean_text(text):
    cleaned = re.sub(r"\(.*?\)", " ", str(text))
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _normalize_text(text):
    return re.sub(r"[^a-z0-9 ]+", " ", _clean_text(text).lower()).strip()


def _extract_introduced_name(text):
    normalized = _normalize_text(text)
    match = re.fullmatch(
        r"(?:hi|hello|hey)?\s*(?:i am|i m|my name is|call me)\s+([a-z][a-z\-']*(?:\s+[a-z][a-z\-']*){0,2})",
        normalized,
    )
    if not match:
        return None
    raw_name = match.group(1).strip()
    return " ".join(part.capitalize() for part in raw_name.split())


def _contains_phrase(text, phrases):
    return any(re.search(rf"\b{re.escape(phrase)}\b", text) for phrase in phrases)


def _contains_greeting(text):
    return bool(re.search(r"\b(?:h+i+|h+e+y+|hello+|yo+)\b", text))


def _has_similar_token(text, targets, cutoff=0.72):
    tokens = text.split()
    for token in tokens:
        for target in targets:
            if SequenceMatcher(None, token, target).ratio() >= cutoff:
                return True
    return False


def _truncate(text, max_chars=280):
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


@dataclass
class KnowledgeChunk:
    source_type: str
    title: str
    text: str

    def prompt_text(self):
        return f"[{self.source_type}] {self.title}: {self.text}"

    def source_label(self):
        return f"{self.source_type}: {self.title}"


class NarutoKnowledgeBase:
    def __init__(self, repo_root, transcript_path, jutsu_path, facts_path):
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.repo_root = Path(repo_root)
        self.transcript_path = self.repo_root / transcript_path
        self.jutsu_path = self.repo_root / jutsu_path
        self.facts_path = self.repo_root / facts_path
        self.chunks = self._load_chunks()
        self.identity_chunks = [
            chunk for chunk in self.chunks if chunk.source_type in {"character", "location", "concept", "team", "motivation", "jutsu_fact"}
        ]
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.embeddings = self.vectorizer.fit_transform([chunk.prompt_text() for chunk in self.chunks])

    def _load_chunks(self):
        chunks = []
        chunks.extend(self._load_fact_chunks())
        chunks.extend(self._load_jutsu_chunks())
        chunks.extend(self._load_dialogue_chunks())
        if not chunks:
            raise ValueError("No knowledge chunks were loaded for the grounded chatbot.")
        return chunks

    def _load_fact_chunks(self):
        if not self.facts_path.exists():
            return []

        chunks = []
        with self.facts_path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                item = json.loads(line)
                title = item.get("title", "Untitled Fact")
                category = item.get("category", "fact")
                summary = _clean_text(item.get("summary", ""))
                if summary:
                    chunks.append(KnowledgeChunk(category, title, summary))
        return chunks

    def _load_jutsu_chunks(self):
        if not self.jutsu_path.exists():
            return []

        df = pd.read_json(self.jutsu_path, lines=True).fillna("")
        chunks = []
        for _, row in df.iterrows():
            name = _clean_text(row.get("jutsu_name", ""))
            description = _clean_text(row.get("jutsu_description", ""))
            jutsu_type = _clean_text(row.get("jutsu_type", ""))
            if not name or not description:
                continue
            text = f"{name} is described as: {description}"
            if jutsu_type:
                text += f" Type: {jutsu_type}."
            chunks.append(KnowledgeChunk("jutsu", name, text))
        return chunks

    def _load_dialogue_chunks(self):
        if not self.transcript_path.exists():
            return []

        df = pd.read_csv(self.transcript_path).dropna(subset=["name", "line"])
        chunks = []
        for _, row in df.iterrows():
            speaker = _clean_text(row.get("name", "Unknown"))
            line = _clean_text(row.get("line", ""))
            if len(line) < 20:
                continue
            chunks.append(KnowledgeChunk("dialogue", f"{speaker} quote", f"{speaker} says: {line}"))
        return chunks

    def search(self, query, top_k=4):
        from sklearn.metrics.pairwise import cosine_similarity

        query = _clean_text(query)
        if not query:
            return []

        scores = cosine_similarity(self.vectorizer.transform([query]), self.embeddings).ravel()
        ranked_indexes = scores.argsort()[::-1]

        results = []
        for index in ranked_indexes:
            score = float(scores[index])
            if score <= 0:
                break
            chunk = self.chunks[index]
            results.append((chunk, score))
            if len(results) >= top_k:
                break
        return results

    def match_identity_chunks(self, query, top_k=3):
        normalized_query = _normalize_text(query)
        if not normalized_query:
            return []

        matches = []
        query_tokens = set(normalized_query.split())
        for chunk in self.identity_chunks:
            normalized_title = _normalize_text(chunk.title)
            if not normalized_title:
                continue

            title_tokens = normalized_title.split()
            aliases = {normalized_title}
            if len(title_tokens) > 1 and chunk.source_type == "character":
                aliases.add(title_tokens[0])

            score = 0.0
            if any(alias and re.search(rf"\b{re.escape(alias)}\b", normalized_query) for alias in aliases):
                score = 1.0
            elif query_tokens and set(title_tokens).issubset(query_tokens):
                score = 0.9
            elif query_tokens and len(set(title_tokens) & query_tokens) >= 2:
                score = 0.75

            if score > 0:
                matches.append((chunk, score))

        matches.sort(key=lambda item: item[1], reverse=True)
        return matches[:top_k]


class GroundedNarutoRAGChatbot:
    def __init__(
        self,
        repo_root,
        transcript_path="data/naruto.csv",
        jutsu_path="data/jutsus.jsonl",
        facts_path="data/naruto_rag_facts.jsonl",
        model_name="meta-llama/Meta-Llama-3-8B-Instruct",
        huggingface_token=None,
    ):
        self.knowledge_base = NarutoKnowledgeBase(
            repo_root=repo_root,
            transcript_path=transcript_path,
            jutsu_path=jutsu_path,
            facts_path=facts_path,
        )
        self.model_name = model_name
        self.client = None
        self.last_error = None
        if huggingface_token:
            try:
                from huggingface_hub import InferenceClient

                self.client = InferenceClient(
                    base_url="https://router.huggingface.co/v1",
                    api_key=huggingface_token,
                )
            except Exception as exc:
                self.last_error = str(exc)

    def _build_query(self, message, history):
        query_parts = [message]
        if history:
            for user_message, assistant_message in history[-2:]:
                if user_message:
                    query_parts.append(user_message)
                if assistant_message:
                    query_parts.append(assistant_message)
        return " ".join(query_parts)

    def _build_context(self, message, history, top_k=4):
        query = self._build_query(message, history)
        semantic_matches = self.knowledge_base.search(query, top_k=top_k)
        if not self._is_identity_query(message):
            return semantic_matches

        direct_matches = self.knowledge_base.match_identity_chunks(query, top_k=top_k)
        combined = []
        seen = set()
        for chunk, score in direct_matches + semantic_matches:
            key = (chunk.source_type, chunk.title, chunk.text)
            if key in seen:
                continue
            combined.append((chunk, score))
            seen.add(key)
            if len(combined) >= top_k:
                break
        return combined

    def _is_identity_query(self, message):
        normalized = _normalize_text(message)
        if self._self_query_intent(message) is not None:
            return True
        return any(
            phrase in normalized
            for phrase in [
                "who are you",
                "who is",
                "tell me about",
                "what about",
                "your character",
                "about yourself",
                "describe yourself",
            ]
        )

    def _self_query_intent(self, message):
        normalized = _normalize_text(message)
        tokens = set(normalized.split())

        if "who are you" in normalized or "what are you" in normalized:
            return "intro"

        if _contains_phrase(normalized, ["introduce yourself", "about yourself", "describe yourself"]):
            return "summary"

        has_you_reference = _has_similar_token(normalized, ["you", "your", "yourself"], cutoff=0.8)
        has_about = _has_similar_token(normalized, ["about"], cutoff=0.6)
        has_describe_verb = _has_similar_token(normalized, ["explain", "tell", "describe", "introduce"], cutoff=0.72)

        if has_you_reference and "character" in tokens:
            return "summary"

        if has_you_reference and has_describe_verb and has_about:
            return "summary"

        return None

    def _self_intro_response(self):
        naruto_matches = self.knowledge_base.match_identity_chunks("naruto", top_k=1)
        if naruto_matches:
            naruto_chunk = naruto_matches[0][0]
            return (
                f"I'm Naruto Uzumaki. {naruto_chunk.text} "
                "My ninja way is to never go back on my word."
            )
        return "I'm Naruto Uzumaki, a shinobi from the Hidden Leaf Village who wants to become Hokage."

    def _character_summary_response(self):
        naruto_matches = self.knowledge_base.match_identity_chunks("naruto", top_k=1)
        if naruto_matches:
            naruto_chunk = naruto_matches[0][0]
            return (
                f"I'm Naruto Uzumaki. {naruto_chunk.text} "
                "I'm loud, stubborn, and I never quit when it comes to protecting my friends and chasing my goal of becoming Hokage."
            )
        return self._self_intro_response()

    def _format_identity_response(self, chunk):
        if chunk.source_type == "character":
            return f"{chunk.text}"
        return f"{chunk.title}: {chunk.text}"

    def _small_talk_response(self, message, history):
        normalized = _normalize_text(message)
        introduced_name = _extract_introduced_name(message)

        if introduced_name:
            return (
                f"Nice to meet you, {introduced_name}. I'm Naruto Uzumaki. "
                "Stick with me and ask anything about Konoha, Team 7, chakra, or my journey to becoming Hokage."
            )

        if _contains_greeting(normalized):
            return (
                "Hey! I'm Naruto Uzumaki. Ask me about characters, jutsu, Konoha, chakra, or anything from the Naruto story."
            )

        if _contains_phrase(normalized, ["how are you", "howre you", "how r you"]):
            return (
                "I'm doing great. I'm fired up and ready to talk about Naruto, jutsu, and the Hidden Leaf Village."
            )

        if (
            _contains_phrase(normalized, ["help me", "help me out", "need help"]) or
            (_contains_phrase(normalized, ["stuck", "problem", "issue", "critical situation"]) and "you" not in normalized)
        ):
            return (
                "I hear you. If you're stuck, break the problem into one step at a time and tell me the exact part you want help with. "
                "If it is urgent or serious in real life, contact someone nearby who can help you right now."
            )

        if _contains_phrase(normalized, ["thank you", "thanks", "thx"]):
            return "You got it. Ask your next question and I'll keep going with you."

        if _contains_phrase(normalized, ["bye", "goodbye", "see you"]):
            return "See you later. Come back when you want to talk more about Naruto or the shinobi world."

        if history and _contains_phrase(normalized, ["okay", "ok", "got it", "nice", "cool"]):
            return "Good. Ask the next one and I'll keep the thread going."

        return None

    def _direct_conversational_response(self, message, history):
        self_query_intent = self._self_query_intent(message)
        if self_query_intent == "intro":
            return self._self_intro_response()
        if self_query_intent == "summary":
            return self._character_summary_response()
        return self._small_talk_response(message, history)

    def _chat_with_llm(self, message, history, context_chunks):
        context_block = "\n".join(chunk.prompt_text() for chunk, _ in context_chunks)
        messages = [
            {
                "role": "system",
                "content": (
                    'You are Naruto Uzumaki from the anime "Naruto". '
                    "Answer in a natural, energetic Naruto voice, but stay grounded in the provided context. "
                    "Do not invent facts outside the context. If the context is insufficient, say so clearly."
                ),
            },
            {
                "role": "system",
                "content": f"Grounding context:\n{context_block}",
            },
        ]

        for user_message, assistant_message in history[-3:]:
            messages.append({"role": "user", "content": user_message})
            messages.append({"role": "assistant", "content": assistant_message})
        messages.append({"role": "user", "content": message})

        output = self.client.chat_completion(
            model=self.model_name,
            messages=messages,
            max_tokens=280,
            temperature=0.5,
            top_p=0.9,
        )
        response = output.choices[0].message.content.strip()
        sources = ", ".join(chunk.source_label() for chunk, _ in context_chunks[:2])
        return f"{response}\n\nSources: {sources}"

    def _fallback_response(self, message, history, context_chunks):
        normalized = _clean_text(message).lower()

        if not context_chunks:
            return (
                "I don't have enough grounded info in the local dataset to answer that confidently yet. "
                "Ask me about Naruto, Team 7, chakra, Konoha, Hokage, Rasengan, Shadow Clone Jutsu, or specific jutsu."
            )

        top_chunk, top_score = context_chunks[0]
        if top_score < 0.12:
            return (
                "I found only weak matches in the local knowledge base, so I don't want to make something up. "
                "Try asking more specifically about a character, jutsu, or Naruto concept."
            )

        supporting = [chunk for chunk, score in context_chunks[1:3] if score >= 0.08]
        answer_lines = []

        if any(term in normalized for term in ["who is", "tell me about", "what about"]):
            answer_lines.append(self._format_identity_response(top_chunk))
        elif any(term in normalized for term in ["what is", "explain", "how does", "why"]):
            answer_lines.append(f"Here's the grounded summary I found: {_truncate(top_chunk.text, 260)}")
        else:
            answer_lines.append(f"Best grounded match: {_truncate(top_chunk.text, 260)}")

        if supporting:
            answer_lines.append("Related context: " + " | ".join(_truncate(chunk.text, 140) for chunk in supporting))

        sources = ", ".join(chunk.source_label() for chunk, _ in context_chunks[:3])
        answer_lines.append(f"Sources: {sources}")
        return "\n\n".join(answer_lines)

    def chat(self, message, history):
        direct_response = self._direct_conversational_response(message, history)
        if direct_response is not None:
            return direct_response

        context_chunks = self._build_context(message, history)
        if self.client is not None and context_chunks:
            try:
                return self._chat_with_llm(message, history, context_chunks)
            except Exception as exc:
                self.last_error = str(exc)
        return self._fallback_response(message, history, context_chunks)