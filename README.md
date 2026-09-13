# CAREERX – Agentic AI Career & Skill Gap Navigator

> **IBM University Engagement — Agentic AI Project Submission**
> Domain: Education / Career Development

---

## Table of Contents
1. [Problem Statement](#problem-statement)
2. [Proposed Solution](#proposed-solution)
3. [Agent Architecture](#agent-architecture)
4. [RAG Workflow](#rag-workflow)
5. [Technology Stack](#technology-stack)
6. [Data Flow](#data-flow)
7. [User Workflow](#user-workflow)
8. [Project Structure](#project-structure)
9. [Quick Start](#quick-start)
10. [API Reference](#api-reference)
11. [AI Safety & Trust](#ai-safety--trust)
12. [Novelty & Uniqueness](#novelty--uniqueness)
13. [Future Scope](#future-scope)

---

## Problem Statement

Students today face a fragmented career planning experience:

- Job requirements are scattered across hundreds of job postings
- Certifications, skills, and project requirements differ by platform and source
- Generic career guidance (e.g., "learn Python") fails to account for a student's existing knowledge
- There is no structured tool that **compares a student's current profile against a target career** and produces an actionable, personalised roadmap

> The result: students graduate with skills misaligned to industry needs, or pursue certifications they don't yet need while missing foundational requirements.

---

## Proposed Solution

**CAREERX** is an Agentic AI system that:

1. **Accepts a student profile** (education, skills, projects, certifications, target career)
2. **Retrieves real career requirements** from a curated knowledge base using RAG
3. **Identifies skill gaps** — existing, missing, and partially developed
4. **Generates a step-by-step learning roadmap** ordered by prerequisites
5. **Recommends projects and certifications** directly tied to identified gaps
6. **Scores career fit** across multiple roles
7. **Tracks progress** and dynamically updates the roadmap

The system is powered by **IBM Granite** (via watsonx.ai) for natural language generation and **ChromaDB** for semantic vector retrieval.

---

## Agent Architecture

CAREERX uses a **Multi-Agent Architecture** with 8 specialist agents coordinated by an Orchestrator.

```
                        ┌─────────────────────────────────────────────────────────┐
                        │               ORCHESTRATOR AGENT                        │
                        │  Coordinates all agents and assembles the final report  │
                        └────────────────────────┬────────────────────────────────┘
                                                 │
           ┌──────────────┬──────────────┬───────┴────────┬──────────────┬──────────────┐
           ▼              ▼              ▼                 ▼              ▼              ▼
   ┌───────────┐  ┌──────────────┐ ┌──────────┐  ┌──────────────┐ ┌──────────┐ ┌──────────────┐
   │ Profile   │  │ Career RAG   │ │ Skill Gap│  │ Learning Path│ │ Project  │ │Certification │
   │ Analysis  │  │ Agent        │ │ Agent    │  │ Agent        │ │ Rec Agent│ │ Agent        │
   │ Agent     │  │ (ChromaDB)   │ │          │  │              │ │          │ │              │
   └───────────┘  └──────────────┘ └──────────┘  └──────────────┘ └──────────┘ └──────────────┘
                                                                               
   ┌──────────────────────────────────────┐     ┌───────────────────────────────────────┐
   │  Career Recommendation Agent         │     │  Progress Tracking Agent              │
   │  (scores all roles vs. profile)      │     │  (recalculates gaps on completion)    │
   └──────────────────────────────────────┘     └───────────────────────────────────────┘
```

### Agent Responsibilities

| Agent | Responsibility | Input | Output |
|---|---|---|---|
| **Profile Analysis Agent** | Assess capability level, score profile | Student profile | ProfileSummary |
| **Career Research Agent (RAG)** | Retrieve career requirements from knowledge base | Profile (target role) | RetrievedCareerInfo |
| **Skill Gap Analysis Agent** | Compare student skills to requirements | Profile + CareerInfo | SkillGapAnalysis |
| **Learning Path Agent** | Generate ordered learning roadmap | Profile + CareerInfo + SkillGap | LearningPath |
| **Project Recommendation Agent** | Recommend gap-closing projects | Profile + CareerInfo + SkillGap | ProjectRecommendations |
| **Certification Recommendation Agent** | Recommend relevant certifications | Profile + CareerInfo + ProfileSummary | CertificationRecommendations |
| **Career Recommendation Agent** | Score and rank all career roles | Profile + ProfileSummary | CareerRecommendations |
| **Progress Tracking Agent** | Recalculate gaps after student updates | Profile + SkillGap + Progress | ProgressReport |
| **Orchestrator Agent** | Coordinate all agents, assemble report | Student profile | CareerXReport |

---

## RAG Workflow

```
Student Profile (target career)
        │
        ▼
Career Research Agent
        │
        ├── 1. Resolve target role → role_id (keyword/semantic matching)
        │
        ├── 2. Semantic search: ChromaDB.query(
        │         query = "skills certifications projects for <role>",
        │         where = { role_id: <id> },
        │         n_results = 10
        │   )
        │
        ├── 3. Fetch structured role JSON (required_skills, certifications, projects)
        │
        └── 4. Return RetrievedCareerInfo with:
                - required_skills dict (by category)
                - retrieved_chunks (RAG results with source metadata)
                - source = "CAREERX Knowledge Base v1.0"
```

**RAG vs LLM distinction:**
- Career requirements, certifications, project templates → retrieved from knowledge base (source cited)
- Skill gap insights, roadmap narrative, match explanation → generated by IBM Granite LLM
- Every response includes a `source` or `llm_source` field for transparency

---

## Technology Stack

| Component | Technology |
|---|---|
| **Language Model** | IBM Granite 13B Instruct v2 |
| **LLM Platform** | IBM watsonx.ai |
| **Embedding Model** | ChromaDB default (all-MiniLM-L6-v2 via sentence-transformers) |
| **Vector Database** | ChromaDB (persistent, local) |
| **RAG Framework** | Custom implementation on ChromaDB |
| **Backend API** | FastAPI (Python) |
| **Data Validation** | Pydantic v2 |
| **Frontend** | Vanilla HTML5 / CSS3 / JavaScript |
| **Configuration** | Pydantic-settings + dotenv |
| **Knowledge Base** | Curated JSON (6 career roles, 40+ certifications, 25+ projects) |

---

## Data Flow

```
[Student fills profile form]
        │
        ▼
POST /api/analyze
        │
        ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR AGENT                                    │
│                                                                              │
│  1. profile_agent.run(profile)          → ProfileSummary                    │
│  2. career_rag_agent.run(profile)       → RetrievedCareerInfo  ← ChromaDB  │
│  3. skill_gap_agent.run(profile, info)  → SkillGapAnalysis  ← IBM Granite  │
│  4. learning_path_agent.run(...)        → LearningPath       ← IBM Granite  │
│  5. project_agent.run(...)              → ProjectRecommendations             │
│  6. certification_agent.run(...)        → CertificationRecommendations       │
│  7. career_rec_agent.run(...)           → CareerRecommendations ← Granite   │
│                                                                              │
│  Assembles → CareerXReport                                                   │
└──────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
[Dashboard displays all sections with source citations]
```

---

## User Workflow

1. **Open the dashboard** at `http://localhost:8000`
2. **Fill in your profile** (name, degree, skills, target career, hours/week)
3. Click **"Analyse My Career Path"** — the Orchestrator runs all 8 agents
4. **Explore the Dashboard** — profile summary, career match scores, AI insights
5. **View Skill Gap** — see exactly what's missing, partial, and existing
6. **Follow the Roadmap** — step-by-step learning plan with resources
7. **Pick Projects** — hands-on projects that directly close your gaps
8. **Pursue Certifications** — recommended certifications with IBM priority
9. **Track Progress** — check off completed skills and watch your roadmap update

---

## Project Structure

```
careerx/
├── app.py                          # FastAPI application entry point
├── config.py                       # Configuration via environment variables
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
│
├── agents/                         # Multi-agent modules
│   ├── __init__.py
│   ├── models.py                   # Pydantic data models (shared)
│   ├── orchestrator.py             # Orchestrator Agent (coordinates all)
│   ├── profile_agent.py            # Profile Analysis Agent
│   ├── career_rag_agent.py         # Career Research Agent (RAG)
│   ├── skill_gap_agent.py          # Skill Gap Analysis Agent
│   ├── learning_path_agent.py      # Learning Path Agent
│   ├── project_agent.py            # Project Recommendation Agent
│   ├── certification_agent.py      # Certification Recommendation Agent
│   ├── career_recommendation_agent.py  # Career Recommendation Agent
│   └── progress_agent.py           # Progress Tracking Agent
│
├── rag/                            # RAG / retrieval components
│   ├── __init__.py
│   ├── knowledge_base.py           # ChromaDB vector store + ingestion
│   └── llm_client.py               # IBM Granite LLM wrapper
│
├── data/                           # Knowledge base
│   ├── knowledge_base.json         # Career roles, skills, certs, projects
│   └── chroma_db/                  # ChromaDB vector store (auto-created)
│
├── frontend/                       # Dashboard UI
│   └── index.html                  # Single-page application
│
└── docs/                           # Documentation (this file + extras)
    └── README.md
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Optional: IBM Cloud account with watsonx.ai access

### 1. Clone / Download
```bash
cd careerx
```

### 2. Create Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your IBM watsonx.ai credentials (optional for demo mode)
```

### 5. Run the Application
```bash
python app.py
```

Open **http://localhost:8000** in your browser.

### 6. Demo Mode (No IBM Credentials)
The application works fully without IBM watsonx.ai credentials using a structured mock LLM. All RAG retrieval, skill gap analysis, and roadmap generation work offline. LLM-generated narrative text is replaced with rule-based responses.

To enable real IBM Granite responses, set `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` in your `.env` file.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | System health check |
| GET | `/api/roles` | List all career roles |
| GET | `/api/roles/{id}` | Get role details |
| POST | `/api/analyze` | **Run full analysis pipeline** |
| POST | `/api/progress` | Update student progress |
| POST | `/api/search` | Semantic search over knowledge base |
| POST | `/api/admin/rebuild-kb` | Rebuild ChromaDB vector store |

Full interactive docs: **http://localhost:8000/api/docs**

---

## AI Safety & Trust

CAREERX follows responsible AI principles:

- ✅ **Disclaimer shown on every report** — recommendations are guidance only
- ✅ **No employment guarantees** — explicitly stated in all career outputs
- ✅ **No fabricated statistics** — all role-specific data retrieved from curated knowledge base
- ✅ **Source citations** — every section indicates whether content is RAG-retrieved or LLM-generated
- ✅ **Transparent model** — `llm_source` field shows which model generated each response
- ✅ **Separation of retrieved vs. generated** — RAG content and LLM content are labelled differently

---

## Novelty & Uniqueness

| Feature | Novelty |
|---|---|
| **True multi-agent system** | 8 specialist agents with distinct responsibilities, not a single monolithic LLM call |
| **RAG-first approach** | Career requirements are retrieved from a knowledge base, not hallucinated by the LLM |
| **Source transparency** | Every output section carries provenance metadata (RAG source or LLM source) |
| **IBM-first certs** | Certification agent prioritises IBM certifications for IBM ecosystem alignment |
| **Progress-aware roadmap** | Student progress dynamically updates the remaining skill gap and roadmap |
| **Capability-aware matching** | Certifications filtered by student capability level (Beginner / Intermediate / Advanced) |
| **Prerequisite-ordered roadmap** | Learning steps follow the knowledge base's recommended learning order, not random order |

---

## Future Scope

1. **Real-time job market integration** — connect to LinkedIn Jobs API or Naukri to pull live job requirements
2. **IBM Watson Natural Language Understanding** — extract skills from resume PDFs automatically
3. **Peer comparison** — anonymised aggregate data to show how a student ranks vs. peers
4. **Multi-modal input** — accept resume/CV upload for automatic profile extraction
5. **Course integration** — direct links to Coursera, IBM SkillsBuild, and edX courses per roadmap step
6. **Mentor matching** — connect students with IBM mentors based on career alignment
7. **Industry trend analysis** — trend data showing which skills are growing or declining in demand
8. **Multi-language support** — Hindi, Tamil, and other regional languages for wider reach
9. **Mobile app** — React Native or Flutter wrapper over the existing API
10. **Enterprise version** — batch processing for university career cells to analyse entire cohorts

---

## Acknowledgements

- **IBM watsonx.ai** for Granite LLM infrastructure
- **IBM SkillsBuild** for open learning resources referenced in roadmaps
- **ChromaDB** for vector storage and semantic retrieval
- Career role data curated from publicly available job descriptions and certification documentation

---

*CAREERX is an educational prototype built for the IBM University Engagement Agentic AI project.*
*Recommendations are AI-generated guidance and do not guarantee employment outcomes.*
