from unittest.mock import Mock, patch

import pytest
import requests

from researchpulse import (
    OpenAlexError,
    bounded_ai,
    calculate_metrics,
    fetch_works,
    normalize_author,
    search_authors,
)


AUTHOR = {
    "id": "https://openalex.org/A123",
    "display_name": "Ada Scholar",
    "works_count": 42,
    "cited_by_count": 350,
    "summary_stats": {"h_index": 11, "i10_index": 18},
    "last_known_institutions": [{"display_name": "Example University"}],
    "counts_by_year": [
        {"year": year, "works_count": works, "cited_by_count": cites}
        for year, works, cites in [
            (2016, 2, 8), (2017, 2, 9), (2018, 3, 10), (2019, 3, 12), (2020, 4, 14),
            (2021, 5, 18), (2022, 6, 22), (2023, 7, 28), (2024, 8, 34), (2025, 9, 40), (2026, 2, 5),
        ]
    ],
}
WORKS = [
    {"title": "Secure Systems", "year": 2025, "citations": 10, "topic": "Cybersecurity", "domain": "Computer Science", "open_access": True},
    {"title": "Trusted AI", "year": 2024, "citations": 8, "topic": "Cybersecurity", "domain": "Computer Science", "open_access": False},
]


def test_normalize_author_preserves_source_metrics():
    normalized = normalize_author(AUTHOR)
    assert normalized["id"] == "A123"
    assert normalized["works_count"] == 42
    assert normalized["h_index"] == 11


def test_metrics_use_completed_five_year_windows():
    metrics = calculate_metrics(AUTHOR, WORKS, current_year=2026)
    assert metrics["recent_5y_works"] == 35
    assert metrics["prior_5y_works"] == 14
    assert metrics["publication_change_pct"] == 150.0
    assert metrics["citation_change_pct"] == 167.9
    assert metrics["open_access_share"] == 50.0


def test_monitoring_changes_with_trajectory():
    declining = {**AUTHOR, "counts_by_year": [
        {"year": y, "works_count": 10 if y < 2021 else 2, "cited_by_count": 20 if y < 2021 else 5}
        for y in range(2016, 2026)
    ]}
    metrics = calculate_metrics(declining, WORKS, current_year=2026)
    assert metrics["publication_change_pct"] == -80.0
    assert bounded_ai(metrics)["label"] == "WATCH"


def test_ai_is_grounded_and_does_not_mutate_metrics():
    metrics = calculate_metrics(AUTHOR, WORKS, current_year=2026)
    before = metrics.copy()
    result = bounded_ai(metrics)
    assert metrics == before
    assert set(result["grounding"]) == {"publication_change_pct", "citation_change_pct", "h_index", "recent_5y_works", "top_topics"}
    assert str(metrics["h_index"]) in result["interpretation"]


def test_invalid_ambiguous_query_rejected():
    with pytest.raises(ValueError, match="two characters"):
        search_authors("A")


@patch("researchpulse.requests.get")
def test_external_api_failure_is_explicit(mock_get):
    mock_get.side_effect = requests.Timeout("timeout")
    with pytest.raises(OpenAlexError, match="temporarily unavailable"):
        search_authors("Ada Scholar")


@patch("researchpulse.requests.get")
def test_retrieval_parsing(mock_get):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"results": [{
        "id": "https://openalex.org/W1", "display_name": "A Paper", "publication_year": 2025,
        "publication_date": "2025-01-01", "cited_by_count": 7, "type": "article",
        "primary_topic": {"display_name": "Security", "domain": {"display_name": "Computer Science"}},
        "open_access": {"is_oa": True}, "doi": "https://doi.org/10.1/test",
    }]}
    mock_get.return_value = response
    works = fetch_works("A123")
    assert works[0]["title"] == "A Paper"
    assert works[0]["citations"] == 7
    assert works[0]["open_access"] is True
