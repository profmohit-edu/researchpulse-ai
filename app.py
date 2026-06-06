from fastapi import FastAPI
import requests

app = FastAPI(
    title="ResearchPulse AI",
    description="AI-Driven Scholarly Intelligence and Research Impact Monitoring Platform",
    version="0.3"
)

# ==================================================
# HOME PAGE
# ==================================================

@app.get("/")
def home():
    return {
        "application": "ResearchPulse AI",
        "version": "0.3",
        "status": "running",
        "creator": "Prof. Mohit Tiwari",
        "developer": "Prof. Mohit Tiwari",
        "institution": "Bharati Vidyapeeth's College of Engineering, Delhi",
        "message": "Welcome to ResearchPulse AI"
    }

# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

# ==================================================
# CREATOR PROFILE
# ==================================================

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
        "role": "Creator and Lead Developer"
    }

# ==================================================
# ABOUT PLATFORM
# ==================================================

@app.get("/about")
def about():
    return {
        "platform": "ResearchPulse AI",
        "creator": "Prof. Mohit Tiwari",
        "mission": "Automate publication discovery, scholarly intelligence, citation tracking and research impact monitoring.",
        "current_version": "0.3",
        "technology_stack": [
            "FastAPI",
            "Google Cloud Run",
            "Docker",
            "GitHub",
            "Cloud Build",
            "OpenAlex API"
        ],
        "future_modules": [
            "ORCID Integration",
            "Citation Tracking",
            "Publication Alerts",
            "Scopus Monitoring",
            "Research Dashboard",
            "AI Research Analytics"
        ]
    }

# ==================================================
# AUTHOR SEARCH
# ==================================================

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

# ==================================================
# PUBLICATION SEARCH
# ==================================================

@app.get("/publications")
def publications(author: str):

    url = f"https://api.openalex.org/works?search={author}"

    response = requests.get(url)

    if response.status_code != 200:
        return {
            "error": "Unable to fetch publications"
        }

    data = response.json()

    publications = []

    for work in data.get("results", [])[:10]:

        publications.append({
            "title": work.get("display_name"),
            "publication_year": work.get("publication_year"),
            "cited_by_count": work.get("cited_by_count"),
            "doi": work.get("doi"),
            "type": work.get("type")
        })

    return {
        "author": author,
        "results_found": len(publications),
        "publications": publications
    }
