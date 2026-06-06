from fastapi import FastAPI
import requests

app = FastAPI(
    title="ResearchPulse AI",
    description="AI-Driven Scholarly Intelligence and Research Impact Monitoring Platform",
    version="0.2"
)

# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "application": "ResearchPulse AI",
        "version": "0.2",
        "status": "running",
        "creator": "Prof. Mohit Tiwari",
        "developer": "Prof. Mohit Tiwari",
        "institution": "Bharati Vidyapeeth's College of Engineering, Delhi",
        "message": "Welcome to ResearchPulse AI - Scholarly Intelligence Platform"
    }

# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

# --------------------------------------------------
# CREATOR PROFILE
# --------------------------------------------------

@app.get("/profile")
def profile():
    return {
        "name": "Prof. Mohit Tiwari",
        "designation": "Assistant Professor",
        "department": "Computer Science and Engineering",
        "institution": "Bharati Vidyapeeth's College of Engineering, Delhi",
        "specialization": [
            "Cybersecurity",
            "Linux",
            "Artificial Intelligence",
            "Cloud Computing",
            "Research Analytics"
        ],
        "linkedin": "https://linkedin.com/in/mtiw",
        "email": "mohit.t.bvcoe@gmail.com",
        "platform": "ResearchPulse AI",
        "role": "Creator and Lead Developer"
    }

# --------------------------------------------------
# ABOUT RESEARCHPULSE AI
# --------------------------------------------------

@app.get("/about")
def about():
    return {
        "platform": "ResearchPulse AI",
        "creator": "Prof. Mohit Tiwari",
        "mission": "Automate publication discovery, scholarly intelligence, citation tracking and research impact monitoring.",
        "current_version": "0.2",
        "technology_stack": [
            "FastAPI",
            "Google Cloud Run",
            "Docker",
            "GitHub",
            "Cloud Build"
        ],
        "future_modules": [
            "ORCID Integration",
            "OpenAlex Integration",
            "Publication Alerts",
            "Citation Monitoring",
            "Research Impact Dashboard",
            "AI Research Analytics"
        ]
    }

# --------------------------------------------------
# OPENALEX AUTHOR SEARCH
# --------------------------------------------------

@app.get("/author-search")
def author_search(name: str):

    url = f"https://api.openalex.org/authors?search={name}"

    response = requests.get(url)

    if response.status_code != 200:
        return {
            "error": "Unable to fetch data from OpenAlex"
        }

    data = response.json()

    authors = []

    for author in data.get("results", [])[:10]:

        authors.append({
            "name": author.get("display_name"),
            "works_count": author.get("works_count"),
            "cited_by_count": author.get("cited_by_count"),
            "openalex_id": author.get("id")
        })

    return {
        "search_query": name,
        "results_found": len(authors),
        "authors": authors
    }