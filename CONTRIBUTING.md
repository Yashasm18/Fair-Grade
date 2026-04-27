# Contributing to FairGrade AI

Thank you for your interest in contributing! This document outlines guidelines for contributing to this project.

## 🚀 Getting Started

1. **Fork** the repository and clone your fork:
   ```bash
   git clone https://github.com/<your-username>/Fair-Grade.git
   cd Fair-Grade
   ```

2. **Set up the backend**:
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env  # Add your GEMINI_API_KEY
   uvicorn app:app --reload --port 8000
   ```

3. **Set up the frontend**:
   ```bash
   cd fairgrade-ai
   npm install
   cp .env.example .env  # Add your Firebase config
   npm run dev
   ```

## 🌿 Branching Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, production-ready code |
| `feat/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `docs/<name>` | Documentation improvements |

## 💻 Code Style

**Python (Backend)**
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Each agent lives in `agents/<agent_name>_agent.py` — one responsibility per file
- Add docstrings to all public methods
- Run: `pip install flake8 && flake8 agents/ app.py`

**JavaScript (Frontend)**
- Follow the existing ESLint config (`eslint.config.js`)
- Prefer functional components and React hooks
- Run: `npm run lint` inside `fairgrade-ai/`

## ✅ Running Tests

```bash
# Install pytest if not already installed
pip install pytest

# Run all backend unit tests
pytest tests/ -v
```

## 📝 Pull Request Checklist

- [ ] All existing tests pass (`pytest tests/ -v`)
- [ ] New behaviour is covered by tests
- [ ] Linting passes (no new warnings)
- [ ] PR description explains **what** changed and **why**
- [ ] Commit messages follow the convention: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`

## 🐛 Reporting Bugs

Open a [GitHub Issue](https://github.com/Yashasm18/Fair-Grade/issues) with:
- Steps to reproduce
- Expected vs. actual behaviour
- Your OS, Python version, and Node version

## 📄 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
