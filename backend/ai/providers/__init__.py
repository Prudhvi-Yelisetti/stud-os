"""Provider abstraction for chat-completion AI features (suggestions,
study coach, etc.). Embeddings (semantic search) never go through this --
they're always local, see backend/ai/embeddings.py."""
