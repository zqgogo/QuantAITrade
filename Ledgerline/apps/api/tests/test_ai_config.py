from app.core.ai_config import load_ai_config


def test_load_demo_ai_config() -> None:
    config = load_ai_config()

    assert config.active_provider == "ollama"
    assert config.active_llm.default_model
    assert config.embedding.provider == "local"
    assert config.agent.runtime in {"ledgerline", "pi_coding_agent"}
