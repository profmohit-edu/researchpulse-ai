# ResearchPulse-AI

**AI-Driven Scholarly Intelligence and Research Impact Monitoring Prototype**

ResearchPulse-AI is a working FastAPI and browser-based prototype that retrieves live scholarly records from OpenAlex, resolves author candidates, calculates transparent bibliometric indicators, monitors longitudinal publication/citation trajectories, and applies a bounded explainable machine-learning model to the deterministic evidence.

Creator: **Mohit Tiwari**, Department of Computer Science and Engineering, Bharati Vidyapeeth's College of Engineering, New Delhi.

## Evidence chain

1. General author search against the live OpenAlex author index.
2. Explicit identity selection to handle ambiguous names.
3. Live author and recent-publication retrieval.
4. Source-derived works, citation counts, h-index and i10-index.
5. Deterministic five-year publication and citation monitoring windows; the current partial year is excluded.
6. Topic extraction from retrieved works and longitudinal visualization.
7. A bounded multinomial-logit trajectory interpretation grounded only in calculated metrics.

The AI model cannot create publications, modify citations, resolve identity, judge research quality, or forecast future impact. Its fixed features and versioned weights are disclosed in `researchpulse.py` and `app.js`.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`. API documentation is available at `/docs`.

## Tests

```bash
pytest -q
```

Tests cover retrieval parsing, bibliometric calculations, longitudinal monitoring, invalid query handling, external API failure, and the AI grounding boundary.

## Provenance

- Scholarly data: [OpenAlex](https://openalex.org/) API, CC0.
- Retrieval timestamp is displayed for each analysis.
- Metrics remain visibly separate from bounded AI interpretation.
