"""Core OpenAlex retrieval, deterministic metrics, monitoring and bounded ML interpretation."""

from __future__ import annotations

import math
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import requests

OPENALEX = "https://api.openalex.org"
MODEL_VERSION = "trajectory-logit-v1.0"


class OpenAlexError(RuntimeError):
    """Raised when OpenAlex cannot return usable scholarly data."""


def _get(path: str, params: dict[str, Any], timeout: float = 20) -> dict[str, Any]:
    try:
        response = requests.get(f"{OPENALEX}{path}", params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise OpenAlexError("OpenAlex is temporarily unavailable") from exc
    if not isinstance(payload, dict):
        raise OpenAlexError("OpenAlex returned an invalid response")
    return payload


def search_authors(query: str, limit: int = 8) -> list[dict[str, Any]]:
    query = query.strip()
    if len(query) < 2:
        raise ValueError("Enter at least two characters")
    payload = _get("/authors", {"search": query, "per-page": limit})
    return [normalize_author(item) for item in payload.get("results", [])]


def normalize_author(item: dict[str, Any]) -> dict[str, Any]:
    institution = None
    last_known = item.get("last_known_institutions") or []
    if last_known:
        institution = last_known[0].get("display_name")
    ids = item.get("ids") or {}
    stats = item.get("summary_stats") or {}
    return {
        "id": (item.get("id") or "").rsplit("/", 1)[-1],
        "name": item.get("display_name"),
        "orcid": ids.get("orcid") or item.get("orcid"),
        "institution": institution,
        "works_count": int(item.get("works_count") or 0),
        "cited_by_count": int(item.get("cited_by_count") or 0),
        "h_index": int(stats.get("h_index") or 0),
        "i10_index": int(stats.get("i10_index") or 0),
    }


def fetch_author(author_id: str) -> dict[str, Any]:
    clean_id = author_id.rsplit("/", 1)[-1]
    if not clean_id.startswith("A"):
        raise ValueError("Select a valid OpenAlex author")
    return _get(f"/authors/{clean_id}", {})


def fetch_works(author_id: str, limit: int = 50) -> list[dict[str, Any]]:
    clean_id = author_id.rsplit("/", 1)[-1]
    payload = _get(
        "/works",
        {
            "filter": f"author.id:{clean_id}",
            "sort": "publication_date:desc",
            "per-page": min(max(limit, 1), 100),
            "select": "id,doi,display_name,publication_year,publication_date,cited_by_count,type,primary_topic,open_access,authorships",
        },
    )
    return [normalize_work(work) for work in payload.get("results", [])]


def normalize_work(work: dict[str, Any]) -> dict[str, Any]:
    topic = work.get("primary_topic") or {}
    domain = topic.get("domain") or {}
    return {
        "id": (work.get("id") or "").rsplit("/", 1)[-1],
        "title": work.get("display_name") or "Untitled work",
        "year": work.get("publication_year"),
        "date": work.get("publication_date"),
        "citations": int(work.get("cited_by_count") or 0),
        "doi": work.get("doi"),
        "type": work.get("type"),
        "topic": topic.get("display_name"),
        "domain": domain.get("display_name"),
        "open_access": bool((work.get("open_access") or {}).get("is_oa")),
    }


def yearly_series(author: dict[str, Any], current_year: int | None = None) -> list[dict[str, int]]:
    current_year = current_year or datetime.now(timezone.utc).year
    rows = []
    for item in author.get("counts_by_year") or []:
        year = int(item.get("year") or 0)
        if current_year - 11 <= year <= current_year:
            rows.append({"year": year, "works": int(item.get("works_count") or 0), "citations": int(item.get("cited_by_count") or 0)})
    return sorted(rows, key=lambda row: row["year"])


def _change(recent: float, prior: float) -> float | None:
    if prior == 0:
        return None if recent == 0 else 100.0
    return round((recent - prior) / prior * 100, 1)


def calculate_metrics(author: dict[str, Any], works: list[dict[str, Any]], current_year: int | None = None) -> dict[str, Any]:
    current_year = current_year or datetime.now(timezone.utc).year
    normalized = normalize_author(author)
    series = yearly_series(author, current_year)
    completed = [row for row in series if row["year"] < current_year]
    recent = [row for row in completed if row["year"] >= current_year - 5]
    prior = [row for row in completed if current_year - 10 <= row["year"] < current_year - 5]
    recent_works = sum(row["works"] for row in recent)
    prior_works = sum(row["works"] for row in prior)
    recent_citations = sum(row["citations"] for row in recent)
    prior_citations = sum(row["citations"] for row in prior)
    topics = Counter(work["topic"] for work in works if work.get("topic"))
    domains = Counter(work["domain"] for work in works if work.get("domain"))
    oa_count = sum(1 for work in works if work.get("open_access"))
    return {
        **normalized,
        "sampled_publications": len(works),
        "open_access_share": round(oa_count / len(works) * 100, 1) if works else 0.0,
        "recent_5y_works": recent_works,
        "prior_5y_works": prior_works,
        "publication_change_pct": _change(recent_works, prior_works),
        "recent_5y_citations": recent_citations,
        "prior_5y_citations": prior_citations,
        "citation_change_pct": _change(recent_citations, prior_citations),
        "top_topics": [{"name": name, "count": count} for name, count in topics.most_common(5)],
        "top_domains": [{"name": name, "count": count} for name, count in domains.most_common(3)],
        "yearly": series,
        "window_note": "Five-year monitoring windows exclude the current partial year.",
    }


def bounded_ai(metrics: dict[str, Any]) -> dict[str, Any]:
    """Transparent fixed-weight multinomial logit over deterministic metrics."""
    pub = max(-100.0, min(200.0, metrics.get("publication_change_pct") or 0.0)) / 100
    cite = max(-100.0, min(200.0, metrics.get("citation_change_pct") or 0.0)) / 100
    h_norm = min(float(metrics.get("h_index") or 0) / 100, 1.5)
    recent_norm = min(float(metrics.get("recent_5y_works") or 0) / 100, 2.0)
    features = {"publication_momentum": pub, "citation_momentum": cite, "h_index_scale": h_norm, "recent_output_scale": recent_norm}
    weights = {
        "ACCELERATING": {"bias": -0.15, "publication_momentum": 1.35, "citation_momentum": 1.05, "h_index_scale": 0.25, "recent_output_scale": 0.35},
        "STABLE": {"bias": 0.35, "publication_momentum": -0.15, "citation_momentum": 0.05, "h_index_scale": 0.15, "recent_output_scale": 0.10},
        "WATCH": {"bias": -0.10, "publication_momentum": -1.10, "citation_momentum": -0.65, "h_index_scale": -0.10, "recent_output_scale": -0.20},
    }
    logits = {label: spec["bias"] + sum(spec[k] * v for k, v in features.items()) for label, spec in weights.items()}
    peak = max(logits.values())
    exps = {label: math.exp(value - peak) for label, value in logits.items()}
    total = sum(exps.values())
    probs = {label: round(value / total * 100, 1) for label, value in exps.items()}
    label = max(probs, key=probs.get)
    pub_text = format_change(metrics.get("publication_change_pct"))
    cite_text = format_change(metrics.get("citation_change_pct"))
    topics = metrics.get("top_topics") or []
    topic_text = topics[0]["name"] if topics else "no dominant topic in the retrieved sample"
    interpretation = (
        f"The bounded model classifies the monitored trajectory as {label}. "
        f"This is grounded in a {pub_text} in five-year publication output, "
        f"a {cite_text} in citations received across the same monitoring windows, "
        f"h-index {metrics.get('h_index', 0)}, and {metrics.get('recent_5y_works', 0)} works in the recent completed five-year window. "
        f"The most frequent topic in the retrieved publication sample is {topic_text}."
    )
    return {
        "model": MODEL_VERSION,
        "label": label,
        "probability": probs[label],
        "probabilities": probs,
        "features": {key: round(value, 3) for key, value in features.items()},
        "interpretation": interpretation,
        "guidance": "Use this signal to prioritize human review of the yearly series and retrieved works; it is not a research-quality judgment or forecasting claim.",
        "grounding": ["publication_change_pct", "citation_change_pct", "h_index", "recent_5y_works", "top_topics"],
    }


def format_change(value: float | None) -> str:
    if value is None:
        return "not-computable"
    direction = "increase" if value >= 0 else "decrease"
    return f"{abs(value):.1f}% {direction}"


def build_intelligence(author_id: str) -> dict[str, Any]:
    author = fetch_author(author_id)
    works = fetch_works(author_id)
    metrics = calculate_metrics(author, works)
    return {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source": {"name": "OpenAlex", "author_url": author.get("id"), "license": "CC0"},
        "author": normalize_author(author),
        "publications": works,
        "metrics": metrics,
        "ai_interpretation": bounded_ai(metrics),
    }
