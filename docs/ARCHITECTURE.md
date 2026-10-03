# Architecture

The Streamlit UI creates an incident state. Python analyzes telemetry and calculates production impact. CrewAI runs the six specialized reasoning agents using a Groq-backed custom LLM adapter. The local RAG layer retrieves relevant chunks from supplied maintenance documents using TF-IDF cosine similarity. A deterministic verifier checks schema, citations, arithmetic, safety, and confidence.

CrewAI is used for agent/task structure; deterministic Python remains responsible for calculations and validation. This follows the project's central engineering principle and current CrewAI direct-code `Agent`, `Task`, `Crew`, and `Process.sequential` patterns.
