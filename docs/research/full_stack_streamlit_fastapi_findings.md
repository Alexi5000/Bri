# Bri Full-Stack Streamlit/FastAPI Research Notes

## Official Streamlit architecture findings

Source: https://docs.streamlit.io/develop/concepts/architecture/architecture

Streamlit applications use a client-server model. The Python process that runs `streamlit run` is the server and performs computation/storage for all users, while the browser is the client. For Bri, this means the Streamlit layer should be treated as a real server-side application frontend, not a purely static UI.

Key production implications for Bri:

| Area | Finding | Bri implementation implication |
|---|---|---|
| Compute and storage | The server provides compute and storage for all users. | Bri’s Streamlit frontend must avoid doing heavyweight multimodal processing directly in page code and should delegate through a middle layer/service boundary. |
| Uploaded files | Streamlit cannot access arbitrary user files; it can only access uploaded files through widgets. | Bri’s video workflow should use `st.file_uploader`, persist uploaded artifacts through a controlled storage service, and never assume local client filesystem access. |
| Processes | External programs run on the Streamlit server, not the user’s machine. | Video/audio processing commands must be handled through backend/middle-layer services with clear paths, error handling, and safe execution boundaries. |
| WebSockets and sessions | Each browser tab has a separate WebSocket-backed session. | Bri should centralize session initialization, avoid ad hoc global state, and persist workflow records in SQLite rather than relying only on `st.session_state`. |
| Scale and load balancing | Multi-replica deployments need session affinity or shared external storage for media. | Bri documentation and runtime design should call out sticky sessions or stable shared storage for production scaling. |

## Official FastAPI larger-application findings

Source: https://fastapi.tiangolo.com/tutorial/bigger-applications/

FastAPI recommends organizing larger applications into packages, routers, dependency modules, and application entrypoints rather than keeping all behavior in one file. `APIRouter` acts as a modular mini-application that supports path operations, dependencies, tags, responses, and router composition.

Key production implications for Bri:

| Area | Finding | Bri implementation implication |
|---|---|---|
| Modular routing | Larger APIs should split operations into routers and packages. | Bri’s MCP and application APIs should remain modular, with clear route/service boundaries. |
| Dependency reuse | Shared dependencies belong in dedicated modules. | Bri’s API keys, settings, persistence handles, and request safeguards should be injected consistently instead of duplicated. |
| Router metadata | Routers can declare prefixes, tags, dependencies, and response metadata. | Bri’s public API surface should expose well-documented health, tools, workflow, and analysis capabilities with predictable tags/contracts. |
| Package structure | `__init__.py` package organization supports imports and scalable code layout. | Bri’s middle layer should be implemented as importable application modules, not loose scripts. |

## Immediate architecture direction

Bri should remain a **Streamlit + FastAPI + SQLite** full-stack application, but the Streamlit UI should be upgraded into an enterprise product frontend that delegates durable work through a middle layer. The middle layer should encapsulate API clients, workflow orchestration, persistence calls, file lifecycle management, user-facing status models, and optional multimodal ML fallbacks.


## Official SQLite backup and durability findings

Source: https://sqlite.org/backup.html

SQLite’s Online Backup API exists to safely copy a live database into another database file. The documentation notes that direct file copying can block writers and can produce a corrupted backup if power or OS failure occurs during the copy. The Online Backup API supports incremental copying and creates a destination snapshot of the source database as it existed when copying began.

Key production implications for Bri:

| Area | Finding | Bri implementation implication |
|---|---|---|
| Live backups | SQLite supports online backups of live databases. | Bri should expose a controlled SQLite backup helper/service rather than instructing operators to copy the database file blindly. |
| Writer impact | Incremental backup reduces long exclusive lock windows. | Bri’s persistence layer should keep transactions short and use a backup method compatible with active usage. |
| Backup consistency | Completed backups are point-in-time snapshots. | Bri operational docs should describe backup files as consistent snapshots, not ad hoc file copies. |
| Error handling | Backup routines can encounter `SQLITE_BUSY` and should use timeouts/handlers. | Bri’s storage helper should configure connection timeouts and surface clear backup errors. |

## Official Streamlit testing findings

Source: https://docs.streamlit.io/develop/concepts/app-testing

Streamlit provides a native app testing framework. `AppTest` simulates a running Streamlit application and lets tests set up state, manipulate inputs, and inspect rendered output through an API rather than browser automation. The official guidance recommends using this with pytest locally or in CI.

Key production implications for Bri:

| Area | Finding | Bri implementation implication |
|---|---|---|
| UI testability | Streamlit has native test APIs. | Bri should include automated frontend smoke/contract tests for the Streamlit entrypoint and product-critical content. |
| Lower overhead | `AppTest` can replace heavier browser automation for many checks. | Bri can validate initial render, navigation copy, and session-state initialization in CI-friendly tests. |
| CI support | Streamlit tests can run locally and in CI with pytest. | Bri’s production validation gate should include frontend tests alongside API and persistence tests. |


## Multimodal AI product architecture findings

Source: https://www.ibm.com/think/topics/multimodal-ai

Multimodal AI systems process and integrate information across multiple modalities such as text, images, audio, and video. They can produce more comprehensive and nuanced understanding than single-modality systems, and can be more resilient when one modality is noisy or unavailable. IBM identifies core engineering challenges around representation, alignment, reasoning, generation, transference, and quantification, and describes early, mid, and late fusion patterns for combining modalities.

Key production implications for Bri:

| Area | Finding | Bri implementation implication |
|---|---|---|
| Multiple modalities | Useful systems combine text, image, audio, video, and other sensory inputs. | Bri should model video intelligence as a workflow with explicit artifacts: uploaded video, metadata, frame summaries, transcript/audio context, conversation state, and final empathetic insight. |
| Robustness | Multimodal systems can rely on other modalities when one is missing/noisy. | Bri should degrade gracefully when optional ML tools are unavailable by returning structured capability status and human-readable guidance. |
| Alignment | Video/audio/text require temporal and semantic alignment. | Bri’s middle layer should represent timestamps, extracted observations, and conversation turns as first-class domain objects. |
| Fusion | Early, mid, and late fusion patterns combine modalities at different stages. | Bri’s current production fit is late/mid fusion: independent extraction tools feed an orchestrator that produces a unified empathetic response. |

## GenAI and AI-application security findings

Source: https://owasp.org/www-project-top-10-for-large-language-model-applications/

OWASP’s GenAI Security Project focuses on identifying, mitigating, and documenting security and safety risks in generative AI, LLM, agentic, and AI-driven applications. The OWASP Top 10 for LLM Applications is a core component for critical LLM application vulnerabilities and provides actionable guidance for secure development and deployment.

Key production implications for Bri:

| Area | Finding | Bri implementation implication |
|---|---|---|
| AI application risk | GenAI applications require explicit security and safety risk management. | Bri should treat prompts, uploaded files, model outputs, and tool calls as untrusted boundaries. |
| Tool-enabled AI | Agentic and AI-driven applications need governance around tool behavior. | Bri’s MCP tool execution should preserve path traversal protections, bounded execution, standardized envelopes, and audit-friendly errors. |
| Secure deployment | Security controls should be documented and validated. | Bri docs should include production controls, environment handling, upload limits, and optional ML dependency posture. |

## Research-backed target architecture summary

Bri’s 110% production architecture should use Streamlit as the server-rendered product frontend, a dedicated Python middle layer for workflow orchestration and typed contracts, FastAPI MCP routes for API/tool interoperability, SQLite for durable local persistence with safe snapshot backup support, and optional multimodal ML integrations behind capability-aware service adapters. Tests should cover the frontend, API contracts, persistence lifecycle, ML fallback behavior, and repository hygiene.
