"""Tests for real-agent adapters (graceful degradation without optional deps)."""

import pytest

from recreadteam.agents.langgraph_adapter import LangGraphShoppingAgent
from recreadteam.agents.openai_adapter import OpenAIAgentsShoppingAgent
from recreadteam.envs.shop import ShoppingEnv, build_catalog


def _env():
    return ShoppingEnv(build_catalog())


def test_langgraph_adapter_importable():
    import recreadteam.agents.langgraph_adapter as mod

    assert hasattr(mod, "LangGraphShoppingAgent")


def test_langgraph_requires_dependency():
    try:
        LangGraphShoppingAgent(_env())
    except RuntimeError as exc:
        assert "langgraph" in str(exc)
    except ModuleNotFoundError:
        pytest.skip("langgraph installed; adapter constructed")


def test_openai_adapter_importable():
    import recreadteam.agents.openai_adapter as mod

    assert hasattr(mod, "OpenAIAgentsShoppingAgent")


def test_openai_requires_dependency():
    try:
        OpenAIAgentsShoppingAgent(_env())
    except RuntimeError as exc:
        assert "openai-agents" in str(exc)
    except ModuleNotFoundError:
        pytest.skip("openai-agents installed; adapter constructed")
