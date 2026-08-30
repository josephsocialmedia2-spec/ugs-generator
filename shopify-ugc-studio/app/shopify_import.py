from __future__ import annotations

import json
import re
from dataclasses import dataclass, asdict
from html import unescape
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


@dataclass
class Product:
    url: str
    title: str
    description: str
    vendor: str = ""
    price: str = ""
    currency: str = "EUR"
    images: list[str] | None = None
    features: list[str] | None = None

    def to_dict(self):
        data = asdict(self)
        data["images"] = data.get("images") or []
        data["features"] = data.get("features") or []
        return data


def _clean_text(value: str) -> str:
    value = BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _shopify_js_url(url: str) -> str | None:
    parsed = urlparse(url)
    m = re.search(r"(/products/[^/?#]+)", parsed.path)
    if not m:
        return None
    path = m.group(1).rstrip("/") + ".js"
    return urlunparse((parsed.scheme or "https", parsed.netloc, path, "", "", ""))


def _extract_features(description: str, max_items: int = 8) -> list[str]:
    text = _clean_text(description)
    chunks = re.split(r"(?<=[.!?])\s+|\s*[•·|]\s*|\s+-\s+", text)
    out = []
    for chunk in chunks:
        chunk = chunk.strip(" -•·")
        if 18 <= len(chunk) <= 180 and chunk.lower() not in {x.lower() for x in out}:
            out.append(chunk)
        if len(out) >= max_items:
            break
    return out


def fetch_product(url: str, timeout: int = 20) -> Product:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
    }

    js_url = _shopify_js_url(url)
    if js_url:
        try:
            r = requests.get(js_url, headers=headers, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            title = str(data.get("title") or "").strip()
            if title:
                description = _clean_text(data.get("description") or "")
                vendor = str(data.get("vendor") or "").strip()
                images = [str(x) for x in (data.get("images") or []) if x]
                price = ""
                variants = data.get("variants") or []
                if variants:
                    raw_price = variants[0].get("price")
                    if raw_price is not None:
                        price = str(raw_price)
                return Product(
                    url=url,
                    title=title,
                    description=description,
                    vendor=vendor,
                    price=price,
                    images=images,
                    features=_extract_features(description),
                )
        except Exception:
            pass

    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    title = ""
    description = ""
    vendor = ""
    price = ""
    currency = "EUR"
    images: list[str] = []

    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            payload = json.loads(tag.string or tag.get_text() or "{}")
        except Exception:
            continue
        nodes = payload if isinstance(payload, list) else [payload]
        for node in nodes:
            if isinstance(node, dict) and node.get("@graph"):
                nodes.extend([x for x in node["@graph"] if isinstance(x, dict)])
            if not isinstance(node, dict):
                continue
            kind = node.get("@type")
            if isinstance(kind, list):
                is_product = "Product" in kind
            else:
                is_product = kind == "Product"
            if not is_product:
                continue
            title = title or str(node.get("name") or "")
            description = description or _clean_text(str(node.get("description") or ""))
            brand = node.get("brand")
            if isinstance(brand, dict):
                vendor = vendor or str(brand.get("name") or "")
            image = node.get("image")
            if isinstance(image, str):
                images.append(image)
            elif isinstance(image, list):
                images.extend([str(x) for x in image if isinstance(x, str)])
            offers = node.get("offers")
            if isinstance(offers, dict):
                price = price or str(offers.get("price") or "")
                currency = str(offers.get("priceCurrency") or currency)

    def meta(prop: str) -> str:
        tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        return str(tag.get("content") or "").strip() if tag else ""

    title = title or meta("og:title") or (soup.title.get_text(strip=True) if soup.title else "Prodotto Shopify")
    description = description or meta("og:description") or meta("description")
    og_image = meta("og:image")
    if og_image:
        images.insert(0, og_image)

    seen = set()
    unique_images = []
    for image in images:
        image = image.strip()
        if image.startswith("//"):
            image = "https:" + image
        if image and image not in seen:
            seen.add(image)
            unique_images.append(image)

    return Product(
        url=url,
        title=_clean_text(title),
        description=_clean_text(description),
        vendor=_clean_text(vendor),
        price=price,
        currency=currency,
        images=unique_images,
        features=_extract_features(description),
    )
