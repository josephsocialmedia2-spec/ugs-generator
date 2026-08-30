from __future__ import annotations

import re
from urllib.parse import urlparse

import requests

API_VERSION = "2026-07"


def normalize_shop_domain(value: str) -> str:
    value = str(value or "").strip().lower()
    if not value:
        return ""
    if "://" in value:
        value = urlparse(value).netloc
    value = value.split("/")[0].strip()
    if not value:
        return ""
    if "." not in value:
        value += ".myshopify.com"
    if not re.fullmatch(r"[a-z0-9][a-z0-9.-]*[a-z0-9]", value):
        raise ValueError("Dominio Shopify non valido")
    return value


def _graphql(shop: str, token: str, query: str, variables: dict | None = None, timeout: int = 30) -> dict:
    shop = normalize_shop_domain(shop)
    if not shop or not token:
        raise ValueError("Configura negozio e access token Shopify")
    url = f"https://{shop}/admin/api/{API_VERSION}/graphql.json"
    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": token,
        },
        json={"query": query, "variables": variables or {}},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        msg = "; ".join(str(x.get("message") or x) for x in payload["errors"])
        raise RuntimeError(msg)
    return payload.get("data") or {}


CATALOG_QUERY = """
query UGCProducts($first: Int!, $query: String) {
  products(first: $first, query: $query, sortKey: UPDATED_AT, reverse: true) {
    nodes {
      id
      title
      handle
      description
      vendor
      status
      onlineStoreUrl
      featuredMedia {
        preview { image { url altText } }
      }
      media(first: 8) {
        nodes {
          preview { image { url altText } }
        }
      }
      priceRangeV2 {
        minVariantPrice { amount currencyCode }
      }
    }
  }
}
"""


def list_products(shop: str, token: str, search: str = "", limit: int = 30) -> list[dict]:
    data = _graphql(shop, token, CATALOG_QUERY, {"first": max(1, min(50, int(limit))), "query": search or None})
    nodes = ((data.get("products") or {}).get("nodes") or [])
    out = []
    for node in nodes:
        images = []
        featured = (((node.get("featuredMedia") or {}).get("preview") or {}).get("image") or {})
        if featured.get("url"):
            images.append(str(featured["url"]))
        for media in ((node.get("media") or {}).get("nodes") or []):
            image = (((media or {}).get("preview") or {}).get("image") or {})
            if image.get("url") and image["url"] not in images:
                images.append(str(image["url"]))
        price = ((node.get("priceRangeV2") or {}).get("minVariantPrice") or {})
        handle = str(node.get("handle") or "")
        public_url = node.get("onlineStoreUrl") or (f"https://{normalize_shop_domain(shop)}/products/{handle}" if handle else "")
        description = str(node.get("description") or "").strip()
        features = [x.strip() for x in re.split(r"(?<=[.!?])\s+", description) if 18 <= len(x.strip()) <= 180][:8]
        out.append({
            "id": node.get("id"),
            "url": public_url,
            "title": str(node.get("title") or ""),
            "description": description,
            "vendor": str(node.get("vendor") or ""),
            "price": str(price.get("amount") or ""),
            "currency": str(price.get("currencyCode") or "EUR"),
            "status": str(node.get("status") or ""),
            "images": images,
            "features": features,
        })
    return out
