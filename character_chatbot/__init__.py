from .rag_chatbot import GroundedNarutoRAGChatbot

__all__ = ["CharacterChatBot", "GroundedNarutoRAGChatbot"]


def __getattr__(name):
	if name == "CharacterChatBot":
		from .character_chatbot import CharacterChatBot

		return CharacterChatBot
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")