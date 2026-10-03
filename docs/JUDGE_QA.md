# Judge Q&A
**Why multi-agent?** Separate domain roles make electrical reasoning, mechanical reasoning, evidence review and maintenance planning explicit and auditable.

**Why six agents?** The six roles map to distinct responsibilities in the specified factory-maintenance workflow.

**Why not one LLM?** One LLM can generate a narrative, but separating roles makes the reasoning pipeline easier to inspect and validate.

**Why RAG?** Maintenance evidence must come from supplied manuals/history rather than model memory.

**Why CrewAI?** It provides explicit Agent/Task/Crew orchestration and collaboration primitives.

**Why Groq?** The project uses the specified `openai/gpt-oss-120b` model through Groq.

**Why deterministic verification?** Arithmetic, schemas, citation mapping and safety checks are better handled by code than by probabilistic text generation.

**How are hallucinations reduced?** Structured schemas, local evidence retrieval, source metadata, deterministic calculations, safety checks and demo fallback reduce unsupported output.

**What happens if API fails?** The app records the failure and Demo Mode remains available.

**What happens if evidence is missing?** The UI states that evidence is insufficient rather than inventing citations.

**Is the data real?** No. Included demo telemetry/documents are synthetic fictional demonstration data.

**Can it operate machinery?** No. It is decision support and must not be used as authorization or a safety system.

**How would it become production-ready?** Add validated site data pipelines, authentication/authorization, approved safety workflows, industrial historian integration, rigorous model evaluation, observability, change control and domain validation.
