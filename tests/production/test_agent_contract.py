from __future__ import annotations

from services.agent import AgentService


class DummyMemory:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str]] = []

    def add_conversation(self, video_id: str, question: str, answer: str) -> None:
        self.calls.append((video_id, question, answer))


def test_agent_service_provides_deterministic_fallback_without_client() -> None:
    memory = DummyMemory()
    agent = AgentService(groq_client=None, memory=memory)

    response = agent.answer_question(
        video_id="clip-001",
        question="What happened in the clip?",
        context={"summary": "A person walks through a lobby."},
    )

    assert "clip-001" in response["video_id"]
    assert response["answer"]
    assert memory.calls


def test_agent_service_builds_prompt_with_context() -> None:
    agent = AgentService(groq_client=None, memory=None)
    prompt = agent.build_prompt("Summarize", {"objects": ["person", "door"], "transcript": "hello"})

    assert "Summarize" in prompt
    assert "person" in prompt
    assert "hello" in prompt
