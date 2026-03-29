# Sovereign AI Social Agent 🚀

A professional-grade, autonomous social media management agent designed for stability, stealth, and cross-platform engagement.

## ✨ Features

- **Cross-Platform Automation**: Fully operational drivers for:
  - **LinkedIn**: Context-aware posting with advanced ARIA-based selector stability.
  - **Reddit**: Community-compliant submission logic.
  - **Threads**: Seamless mobile-first web automation.
- **Stealth Engine**: Powered by Playwright with advanced anti-detection configurations (custom user-agents, randomized jitter, and human-like interaction timing).
- **Session Management**: Cookie-based authentication persistence (no passwords required after initial setup).
- **Intelligent Scheduling**: Automated posting with configurable time windows and randomized jitter to mimic human behavior.
- **Analytics Dashboard**: Integrated Flask-based UI for tracking post history, success rates, and performance trends.
- **Production-Ready CI/CD**: Validated via GitHub Actions for code quality and style consistency.

## 🛠️ Tech Stack

- **Backend**: Python 3.11, Flask
- **Automation**: Playwright (Chromium)
- **Database**: SQLite (local file persistence)
- **CI/CD**: GitHub Actions (Linting & Style Checks)

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.11+
- Virtual Environment (Recommended)
- System dependencies for Playwright (if on Linux)

### ☁️ Railway Deployment (Recommended)

1.  **Connect Repo**: Connect your GitHub repository to [Railway](https://railway.app/).
2.  **Add Volume**: In the Railway Dashboard, go to `Settings` -> `Volumes` and create a volume named `data`. Mount it to `/data`.
3.  **Set Variables**: Add the following Environment Variables:
    - `SECRET_KEY`: (Any random string)
    - `ENCRYPTION_KEY`: (Get this from your local `.env`)
    - `NIXPACKS_PLAYWRIGHT_INSTALLED`: `1`
4.  **Deploy**: Railway will automatically detect the `nixpacks.toml` and `Procfile` and deploy the app.

### 💻 Manual Local Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd aiauto

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers and system dependencies
playwright install --with-deps chromium

# Setup environment variables
cp .env.example .env
# Edit .env with your secret keys
```

### 3. Usage

```bash
# Start the Flask application and Scheduler
python app.py
```

The application will be accessible at `http://localhost:5000`.


## 🔐 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session security key | Auto-generated |
| `ENCRYPTION_KEY` | Fernet key for database encryption | Auto-generated |
| `DATABASE_PATH` | Path to SQLte database file | `agent.db` |

## 📦 Deployment Guide

The project includes a `.github/workflows/deploy.yml` that automatically:
1. Validates code linting using `flake8`.
2. Checks code formatting using `black`.

## 🛡️ License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Built with ❤️ for Sovereign Agents.*
