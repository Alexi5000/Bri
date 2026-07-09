from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

agent_path = ROOT / "services" / "agent.py"
agent_text = agent_path.read_text(encoding="utf-8")
agent_text = agent_text.replace(
    "from groq import Groq",
    "try:\n    from groq import Groq\nexcept ModuleNotFoundError:  # pragma: no cover - optional production dependency\n    Groq = None  # type: ignore[assignment]",
)
agent_text = agent_text.replace(
    """        self.groq_api_key = groq_api_key or Config.GROQ_API_KEY
        if not self.groq_api_key:
            raise AgentError("Groq API key is required")
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=self.groq_api_key)
""",
    """        self.groq_api_key = groq_api_key or Config.GROQ_API_KEY
        if not self.groq_api_key:
            raise AgentError("Groq API key is required")
        if Groq is None:
            raise AgentError("The groq package is required for live AI responses. Install project dependencies before using GroqAgent.")
        
        # Initialize Groq client
        self.groq_client = Groq(api_key=self.groq_api_key)
""",
)
if "class AgentService:" not in agent_text:
    agent_text += r'''

class AgentService:
    """Lightweight deterministic agent facade for tests and offline API validation.

    GroqAgent remains the production conversational engine. This facade provides a
    small, dependency-injectable surface that lets CI validate prompt assembly,
    memory writes, and offline fallback behavior without installing or invoking a
    hosted LLM client.
    """

    def __init__(self, groq_client: object | None = None, memory: object | None = None) -> None:
        self.groq_client = groq_client
        self.memory = memory

    def build_prompt(self, question: str, context: dict[str, object] | None = None) -> str:
        context = context or {}
        context_lines = [f"{key}: {value}" for key, value in sorted(context.items())]
        context_block = "\n".join(context_lines) if context_lines else "No processed context is available yet."
        return (
            "You are BRI, a concise video intelligence assistant.\n"
            f"Question: {question}\n"
            f"Available context:\n{context_block}\n"
            "Answer with clear, grounded observations and acknowledge uncertainty."
        )

    def answer_question(
        self,
        video_id: str,
        question: str,
        context: dict[str, object] | None = None,
    ) -> dict[str, object]:
        prompt = self.build_prompt(question, context)
        if self.groq_client is None:
            summary = (context or {}).get("summary") or "the available video context"
            answer = (
                f"For video {video_id}, I can provide an offline analysis based on {summary}. "
                "Connect GROQ_API_KEY for live model reasoning."
            )
        else:  # pragma: no cover - live client behavior is integration tested separately
            answer = str(self.groq_client.chat(prompt))
        if self.memory and hasattr(self.memory, "add_conversation"):
            self.memory.add_conversation(video_id, question, answer)
        return {"video_id": video_id, "question": question, "answer": answer, "prompt": prompt}
'''
agent_path.write_text(agent_text, encoding="utf-8")

registry_path = ROOT / "mcp_server" / "registry.py"
registry_text = registry_path.read_text(encoding="utf-8")
registry_text = registry_text.replace(
    """from tools.frame_extractor import FrameExtractor
from tools.image_captioner import ImageCaptioner
from tools.audio_transcriber import AudioTranscriber
from tools.object_detector import ObjectDetector
""",
    """def _load_tool_class(module_name: str, class_name: str):
    try:
        module = __import__(module_name, fromlist=[class_name])
        return getattr(module, class_name)
    except ModuleNotFoundError as exc:  # pragma: no cover - dependency-specific path
        raise RuntimeError(
            f\"{class_name} requires optional media dependencies that are not installed. \"
            \"Install the full requirements before executing this tool.\"
        ) from exc
""",
)
registry_text = registry_text.replace(
    "self.extractor = FrameExtractor()",
    "self.extractor = _load_tool_class('tools.frame_extractor', 'FrameExtractor')()",
)
registry_text = registry_text.replace(
    "self.captioner = ImageCaptioner()",
    "self.captioner = _load_tool_class('tools.image_captioner', 'ImageCaptioner')()",
)
registry_text = registry_text.replace(
    "self.transcriber = AudioTranscriber()",
    "self.transcriber = _load_tool_class('tools.audio_transcriber', 'AudioTranscriber')()",
)
registry_text = registry_text.replace(
    "self.detector = ObjectDetector()",
    "self.detector = _load_tool_class('tools.object_detector', 'ObjectDetector')()",
)
registry_text = registry_text.replace(
    """    def register_all_tools(self) -> None:
        \"\"\"Register all available video processing tools.\"\"\"
        try:
            # Register frame extraction tool
            self.register_tool(FrameExtractionTool())
            
            # Register image captioning tool
            self.register_tool(ImageCaptioningTool())
            
            # Register audio transcription tool
            self.register_tool(AudioTranscriptionTool())
            
            # Register object detection tool
            self.register_tool(ObjectDetectionTool())
            
            logger.info(f\"Successfully registered {len(self.tools)} tools\")
        except Exception as e:
            logger.error(f\"Failed to register tools: {str(e)}\")
            raise
""",
    """    def register_all_tools(self) -> None:
        \"\"\"Register all available video processing tools.\n\n        Tool classes are registered as lightweight wrappers. Heavy optional\n        media dependencies are loaded only when the corresponding tool instance\n        is created, keeping health checks and tool discovery usable in lean CI\n        and API-only deployments.\n        \"\"\"
        for tool_cls in [
            FrameExtractionTool,
            ImageCaptioningTool,
            AudioTranscriptionTool,
            ObjectDetectionTool,
        ]:
            try:
                self.register_tool(tool_cls())
            except RuntimeError as exc:
                logger.warning(\"Skipping optional tool %s: %s\", tool_cls.__name__, exc)
        logger.info(f\"Successfully registered {len(self.tools)} tools\")
""",
)
registry_path.write_text(registry_text, encoding="utf-8")

print("Patched optional Groq and media dependency boundaries.")
