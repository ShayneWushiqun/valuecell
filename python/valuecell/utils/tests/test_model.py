from __future__ import annotations

from types import SimpleNamespace

from agno.models.openai import OpenAILike as AgnoOpenAILikeModel

from valuecell.utils.model import model_should_use_json_mode


def test_model_should_use_json_mode_for_volcengine_openai_compatible() -> None:
    model = SimpleNamespace(
        provider=AgnoOpenAILikeModel.provider,
        name=AgnoOpenAILikeModel.name,
        base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
    )

    assert model_should_use_json_mode(model) is True
