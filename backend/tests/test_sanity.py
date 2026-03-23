from app.core.config import settings
from app.core.token_budget import estimate_text_tokens


def test_settings_have_safe_defaults():
    assert settings.TOKEN_BUDGET_TOTAL == 6000
    assert settings.TOKEN_BUDGET_GENERATOR <= settings.TOKEN_BUDGET_TOTAL
    assert settings.MAX_UPLOAD_FILES > 0


def test_token_estimator_behaves_deterministically():
    assert estimate_text_tokens("") == 0
    assert estimate_text_tokens("abcd") >= 1
    assert estimate_text_tokens("a" * 400) >= estimate_text_tokens("a" * 40)
