"""Vector database adapters (Pinecone, Weaviate, Qdrant, Chroma).

Every meaningful RAG / agentic project touches a vector store. These
adapters surface the *indexes / collections* the project uses, plus the
embedding shape and the query primitives invoked — so the agent
immediately knows where vectors live and how they're being queried.
"""
