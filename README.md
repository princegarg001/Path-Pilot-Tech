# 🚀 PathPilot-AI Backend

Production-grade career coaching API powered by **6 HuggingFace AI models**.

## 🧠 AI Models Used

| Model | Task | Purpose |
|-------|------|---------|
| `jjzha/jobbert_skill_extraction` | Token Classification | Extract skills from resume text |
| `facebook/bart-large-cnn` | Summarization | Generate professional resume summaries |
| `facebook/bart-large-mnli` | Zero-Shot Classification | Categorize skills into domains |
| `sentence-transformers/all-mpnet-base-v2` | Sentence Similarity | ATS semantic scoring |
| `mistralai/Mistral-7B-Instruct-v0.3` | Text Generation | Plan & question generation |
| `ml6team/keyphrase-extraction-kbir-inspec` | Token Classification | Keyphrase extraction |

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze-resume` | Multi-stage AI resume analysis |
| `POST` | `/ats-score` | Semantic + keyword ATS scoring |
| `POST` | `/generate-plan` | Personalized 7-day career plan |
| `POST` | `/generate-questions` | Role-specific interview questions |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI documentation |

## ⚡ Quick Start

### 1. Setup
```bash
cd pathpilot-backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure
```bash
copy .env.example .env
# Edit .env and add your HuggingFace API token
# Get one free at: https://huggingface.co/settings/tokens
```

### 3. Run
```bash
uvicorn main:app --reload --port 8000
```

### 4. Test
Open `http://localhost:8000/docs` for the interactive Swagger UI.

## 🐳 Docker

```bash
docker build -t pathpilot-api .
docker run -p 8000:8000 --env-file .env pathpilot-api
```

## 🌐 Deploy to Render

1. Push this folder to a GitHub repo
2. Connect to [Render.com](https://render.com)
3. Create a new Web Service → select Docker
4. Add `HF_API_TOKEN` environment variable
5. Deploy!

Or use the included `render.yaml` for one-click deploy.

## 📁 Project Structure

```
pathpilot-backend/
├── main.py                        # FastAPI entry point
├── requirements.txt               # Dependencies
├── Dockerfile                     # Production container
├── render.yaml                    # Render deploy config
├── .env.example                   # Environment template
│
├── app/
│   ├── config.py                  # Settings (env vars)
│   │
│   ├── routers/
│   │   ├── resume.py              # POST /analyze-resume
│   │   ├── ats.py                 # POST /ats-score
│   │   ├── plan.py                # POST /generate-plan
│   │   └── questions.py           # POST /generate-questions
│   │
│   ├── services/
│   │   ├── hf_client.py           # HF API wrapper (retry + cache)
│   │   ├── section_parser.py      # Resume section detection
│   │   ├── skill_extractor.py     # JobBERT NER extraction
│   │   ├── summarizer.py          # BART summarization
│   │   ├── classifier.py          # Zero-shot classification
│   │   ├── ats_scorer.py          # Dual ATS scoring
│   │   ├── plan_generator.py      # Mistral plan generation
│   │   ├── question_generator.py  # Mistral question generation
│   │   └── recommender.py         # Gap analysis & recommendations
│   │
│   ├── models/
│   │   ├── schemas.py             # Pydantic request/response models
│   │   └── prompts.py             # LLM prompt templates
│   │
│   └── data/
│       ├── role_taxonomy.py       # 20+ role skill requirements
│       ├── skill_categories.py    # 200+ skill categorization
│       └── resources.py           # Curated learning resources
```

## 🔑 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `HF_API_TOKEN` | Yes | HuggingFace API read token |
| `ALLOWED_ORIGINS` | No | CORS origins (default: `*`) |
| `CACHE_TTL` | No | Cache TTL in seconds (default: `3600`) |
| `MAX_RETRIES` | No | HF cold-start retries (default: `3`) |
