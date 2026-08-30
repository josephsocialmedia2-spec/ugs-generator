from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))

from avatar_engine import model_status
from settings_store import public_settings, save_settings
from shopify_admin import normalize_shop_domain


def test_normalize_shop_domain():
    assert normalize_shop_domain("mystore") == "mystore.myshopify.com"
    assert normalize_shop_domain("https://mystore.myshopify.com/admin") == "mystore.myshopify.com"


def test_settings_never_expose_shopify_secret(tmp_path: Path):
    settings = save_settings(tmp_path, {"shopify_access_token": "shop-secret-9999", "avatar_name": "Demo"})
    public = public_settings(settings)
    assert "shop-secret-9999" not in str(public)
    assert public["avatar_name"] == "Demo"


def test_avatar_engine_is_local_only(tmp_path: Path):
    status = model_status(tmp_path)
    assert status["name"] == "F1 Avatar Engine"
    assert status["local_only"] is True
    assert status["remote_provider"] is None
