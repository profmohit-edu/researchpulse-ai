from fastapi import FastAPI

app = FastAPI(
    title="ResearchPulse AI",
    description="AI-Driven Scholarly Intelligence and Research Impact Monitoring Platform",
    version="0.1"
)

@app.get("/")
def home():
    return {
        "application": "ResearchPulse AI",
        "status": "running",
        "version": "0.1"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }