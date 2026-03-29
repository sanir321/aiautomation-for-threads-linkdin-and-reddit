# Master Documentation: Sovereign AI Social Media Agent

## Table of Contents
1. [Product Requirements Document (PRD)](#1-product-requirements-document-prd)
2. [Security & Privacy Protocol](#2-security--privacy-protocol)
3. [Technical Architecture & Schema](#3-technical-architecture--schema)

---

## 1. Product Requirements Document (PRD)

### 1.1 Executive Summary
A local, autonomous AI social media agent designed to run 24/7 on a mobile environment (Termux/Ubuntu proot). It manages content creation and engagement across Threads, Reddit, and LinkedIn. Unlike generic AI posters, this system relies on a user-defined persona, document-based context (RAG), and live trend scraping from the user's actual feeds to generate highly authentic, platform-specific content.

### 1.2 Target Audience
Solo founders, indie hackers, and developers building in public who need high-quality social presence without the daily time sink or the cost of premium SaaS tools.

### 1.3 Core Features
* **Frictionless Onboarding (Zero-Auth):** No traditional email/password signup. The user's account is implicitly created upon connecting their first social platform or entering their Kilo Gateway API key.
* **The "Brain" (Context Engine):**
    * **Persona Editor:** Save persistent system prompts defining tone, format, and boundaries.
    * **Knowledge Base (Document RAG):** Upload project docs (PDF, MD, TXT - e.g., architecture docs, PRDs) for the AI to reference in posts.
* **The "Eyes" (Feed Intelligence):**
    * Daily scraping of the user's logged-in feeds (Threads, Reddit, LinkedIn).
    * Extraction of trending topics and formats specific to the user's niche.
    * Smart Auto-Follow rules based on engagement metrics and niche relevance.
* **The "Hands" (Publishing Engine):**
    * Platform-specific formatting (Threads: short hooks; Reddit: value-heavy text; LinkedIn: professional storytelling).
    * Automated daily scheduling via APScheduler.

### 1.4 User Flow
1.  **Launch:** User starts the local web server and opens `localhost:5000` in their browser.
2.  **Configure:** User pastes the Kilo Gateway API key and defines their Persona.
3.  **Connect:** User authenticates Threads, Reddit, and LinkedIn (via OAuth or session cookies).
4.  **Upload Context:** User uploads relevant project files.
5.  **Automate:** System takes over, running the daily loop (Scrape -> Generate -> Post).

---

## 2. Security & Privacy Protocol

Because this system handles sensitive session cookies, OAuth tokens, and API keys, security is the highest priority, even for a local application.

### 2.1 Threat Model & Mitigations
* **Threat:** Unauthorized access to API keys or social accounts.
    * *Mitigation:* The application runs strictly on `localhost`. It is not exposed to the public internet. All data remains on the device.
* **Threat:** Plaintext storage of credentials in the database.
    * *Mitigation:* Use symmetric encryption (e.g., Python's `cryptography.fernet`) to encrypt the Kilo Gateway API key, LinkedIn cookies, and Reddit OAuth tokens before storing them in SQLite. The encryption key is generated locally on first run and stored safely in the environment variables.

### 2.2 Data Handling
* **API Keys:** Sent directly to Kilo Gateway via HTTPS. Never logged in plaintext.
* **Scraped Data:** Ephemeral. Trend data is stored temporarily to generate posts and is overwritten or archived daily.
* **Document Uploads:** Parsed locally using libraries like `pymupdf`. Text is extracted and stored locally; original files can be discarded after parsing to save space.

### 2.3 Environment Security
* Running within Termux provides a natural Android sandbox layer.
* Dependencies should be strictly pinned in `requirements.txt` to prevent supply chain attacks via malicious updates.

---

## 3. Technical Architecture & Schema

### 3.1 Tech Stack
* **Environment:** Termux (Android) with Ubuntu proot-distro.
* **Backend:** Python with Flask (or FastAPI) for the local UI.
* **Database:** SQLite3.
* **Task Scheduling:** APScheduler (BackgroundScheduler).
* **AI Integration:** Kilo Gateway API (`requests` library).
* **Platform Connectors:**
    * *Reddit:* PRAW (Python Reddit API Wrapper).
    * *LinkedIn:* `linkedin-api` (unofficial Python wrapper) or Playwright.
    * *Threads:* Unofficial Threads API wrappers (e.g., `threads-net` Python port).
* **Document Parsing:** `PyMuPDF` (PDFs), native string parsing (TXT/MD).

### 3.2 Database Schema (SQLite)

**Table: `config`** (Single row)
* `id` (INT)
* `kilo_api_key` (TEXT, encrypted)
* `system_prompt` (TEXT)
* `posting_time` (TEXT, e.g., "09:00")

**Table: `accounts`**
* `platform` (TEXT, e.g., "reddit", "linkedin")
* `credentials` (TEXT, encrypted JSON of cookies/tokens)
* `status` (TEXT, "active", "disconnected")

**Table: `knowledge_base`**
* `id` (INTEGER PRIMARY KEY)
* `filename` (TEXT)
* `content` (TEXT, parsed text from doc)
* `uploaded_at` (TIMESTAMP)

**Table: `trends_cache`**
* `id` (INTEGER PRIMARY KEY)
* `platform` (TEXT)
* `trending_topic` (TEXT)
* `scraped_at` (TIMESTAMP)

**Table: `post_history`**
* `id` (INTEGER PRIMARY KEY)
* `platform` (TEXT)
* `content` (TEXT)
* `status` (TEXT, "success", "failed")
* `timestamp` (TIMESTAMP)

### 3.3 System Directory Structure
```text
social-agent/
├── app.py                 # Local web server & UI routes
├── config.py              # Encryption keys & environment vars
├── database.py            # SQLite setup & CRUD operations
├── scheduler.py           # APScheduler configuration
├── ai_engine/
│   ├── kilo_client.py     # Communicates with Kilo Gateway
│   └── prompt_builder.py  # Assembles persona + trends + docs
├── platforms/
│   ├── reddit_client.py   # PRAW logic
│   ├── linkedin_client.py # Cookie/Session logic
│   └── threads_client.py  # Unofficial API logic
├── scraper/
│   └── feed_analyzer.py   # Extracts trends from timelines
├── uploads/               # Temporary folder for raw docs
└── requirements.txt