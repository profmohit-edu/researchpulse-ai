from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from researchpulse import OpenAlexError, build_intelligence, search_authors

app = FastAPI(
    title="ResearchPulse-AI",
    description="AI-Driven Scholarly Intelligence and Research Impact Monitoring Prototype",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


@app.get("/", include_in_schema=False)
def home():
    return FileResponse("index.html")


@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/api/authors")
def authors(q: str):
    try:
        return {"query": q, "source": "OpenAlex", "results": search_authors(q)}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except OpenAlexError as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/api/intelligence/{author_id}")
def intelligence(author_id: str):
    try:
        return build_intelligence(author_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except OpenAlexError as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/about")
def about():
    return {
        "application": "ResearchPulse-AI",
        "creator": "Mohit Tiwari",
        "institution": "Bharati Vidyapeeth's College of Engineering, New Delhi",
        "source": "OpenAlex",
        "model": "trajectory-logit-v1.0",
    }
