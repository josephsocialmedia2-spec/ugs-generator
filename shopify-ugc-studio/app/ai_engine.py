from __future__ import annotations

import json
from dataclasses import dataclass, asdict

import requests


@dataclass
class UGCConcept:
    angle: str
    hook: str
    script: str
    cta: str
    scenes: list[str]
    caption: str
    headline: str

    def to_dict(self):
        return asdict(self)


def _fallback(product: dict, audience: str, language: str, angle: str) -> UGCConcept:
    title = product.get("title") or "questo prodotto"
    feature = (product.get("features") or [product.get("description") or "semplice da usare"])[0]
    hook = f"Non pensavo che {title} mi sarebbe stato così utile."
    script = (
        f"Se anche tu {audience or 'cerchi una soluzione più semplice'}, guarda qui. "
        f"Ho provato {title} e la cosa che mi ha colpito di più è questa: {feature}. "
        "È uno di quei prodotti che capisci davvero quando lo usi nella vita di tutti i giorni. "
        "Se vuoi vedere tutti i dettagli, trovi il prodotto nello shop."
    )
    return UGCConcept(
        angle=angle,
        hook=hook,
        script=script,
        cta="Scopri il prodotto nello shop",
        scenes=["Hook selfie-style", "Dettaglio prodotto", "Dimostrazione del beneficio", "CTA finale"],
        caption=f"Lo proveresti? {title} in azione. #ugc #shopify #productdemo",
        headline=f"Perché tutti parlano di {title}",
    )


def generate_concepts(
    product: dict,
    audience: str,
    language: str = "Italiano",
    count: int = 3,
    model: str = "qwen2.5-coder:7b",
    base_url: str = "http://127.0.0.1:11434",
) -> list[UGCConcept]:
    product_json = json.dumps(product, ensure_ascii=False, indent=2)
    system = (
        "Sei un senior direct-response creative strategist specializzato in UGC ads per ecommerce. "
        "Scrivi in modo naturale, credibile, concreto e non inventare benefici non presenti nei dati prodotto. "
        "Non usare testimonianze false o affermazioni mediche/finanziarie non supportate."
    )
    user = f"""
Crea {count} concept UGC distinti per questo prodotto Shopify.
Lingua: {language}
Target: {audience or 'consumatore ecommerce generico'}
Dati prodotto:
{product_json}

Usa angoli diversi tra: problema-soluzione, demo, unboxing/prima impressione, testimonial-style senza dichiarare esperienze false, confronto, lifestyle.
Ogni video deve essere pensato per 15-25 secondi, verticale 9:16, con hook immediato, corpo, CTA e 4 scene.

Rispondi SOLO JSON:
{{"concepts":[{{"angle":"...","hook":"...","script":"...","cta":"...","scenes":["...","...","...","..."],"caption":"...","headline":"..."}}]}}
"""
    try:
        payload = {
            "model": model,
            "stream": False,
            "format": "json",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        r = requests.post(f"{base_url.rstrip('/')}/api/chat", json=payload, timeout=180)
        r.raise_for_status()
        raw = r.json().get("message", {}).get("content", "{}")
        data = json.loads(raw)
        out = []
        for item in data.get("concepts", [])[:count]:
            out.append(
                UGCConcept(
                    angle=str(item.get("angle") or "UGC"),
                    hook=str(item.get("hook") or ""),
                    script=str(item.get("script") or ""),
                    cta=str(item.get("cta") or "Scopri di più"),
                    scenes=[str(x) for x in (item.get("scenes") or [])][:4],
                    caption=str(item.get("caption") or ""),
                    headline=str(item.get("headline") or ""),
                )
            )
        if out:
            return out
    except Exception:
        pass

    angles = ["Problema → soluzione", "Demo prodotto", "Prima impressione"]
    return [_fallback(product, audience, language, angles[i % len(angles)]) for i in range(count)]
