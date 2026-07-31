"""
AI layer for Stud-OS.

Embeddings (semantic search) always run locally -- see embeddings.py --
regardless of any API provider a user configures elsewhere. There is no
provider abstraction in this package yet; that's Phase 2 (chat-completion
features like suggestions/study coach), a separate, larger piece of work.
"""
