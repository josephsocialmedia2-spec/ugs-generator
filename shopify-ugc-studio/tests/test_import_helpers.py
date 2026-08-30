from app.shopify_import import _shopify_js_url, _extract_features


def test_shopify_js_url():
    assert _shopify_js_url("https://x.test/products/demo?variant=1") == "https://x.test/products/demo.js"


def test_features():
    assert _extract_features("Questa è una caratteristica sufficientemente lunga. Altra caratteristica utile e concreta.")
