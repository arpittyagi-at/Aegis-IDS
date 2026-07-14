# Contributing to AEGIS IDS

Thank you for helping improve AEGIS - Adaptive Explainable Generalized Intrusion Detection System. Contributions are welcome across machine learning, backend engineering, dashboard UX, deployment, and documentation.

## Reporting Bugs

Please use GitHub Issues for bugs. A strong report should include:

- Operating system and version
- Python version
- Node.js/npm version if the dashboard is involved
- Exact command that failed
- Full error message or traceback
- Steps to reproduce from a clean checkout
- Dataset and mode used, if relevant

## Suggesting Features

For large changes, open a GitHub Discussion before creating a pull request. This keeps the roadmap clear and avoids duplicated work.

Good feature proposals explain:

- The problem or user workflow
- Why the current behavior is insufficient
- Expected behavior
- Possible implementation approach
- Screenshots, examples, or references when useful

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/aegis-ids
cd aegis-ids
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows PowerShell
venv\Scripts\Activate.ps1

# Windows cmd
venv\Scripts\activate.bat

# macOS/Linux
source venv/bin/activate
```

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Train or verify model artifacts:

```bash
python -m backend.ml.train
python verify_artifacts.py
```

Run the backend:

```bash
uvicorn backend.server:app --reload --port 8000
```

Run the frontend:

```bash
cd frontend
npm install
npm start
```

Docker setup:

```bash
docker-compose up --build
```

## Code Style

- Python should follow PEP 8.
- JavaScript should follow the existing React style and ESLint rules.
- Keep functions focused and names descriptive.
- Prefer typed request/response models for API changes.
- Keep dashboard components readable and avoid hidden global state.
- Use meaningful commit messages, for example `Add CICIoT loader validation` or `Fix WebSocket reconnect state`.

## Pull Request Process

1. Fork the repository.
2. Create a branch using `feature/your-feature-name`, `fix/short-bug-name`, or `docs/topic-name`.
3. Make focused changes with tests or verification notes.
4. Run relevant checks locally.
5. Open a pull request with a clear summary and screenshots for UI changes.

Suggested PR template:

```markdown
## Summary
- 

## Verification
- 

## Screenshots

## Notes
```

## High-Impact Contribution Areas

- New dataset loaders
- Additional ML models and model comparison reports
- SHAP performance optimization
- Dashboard improvements
- Docker and deployment optimizations
- Documentation, tutorials, and demo assets

## Code of Conduct

Be respectful, constructive, and precise. Security tooling benefits from careful review and calm disagreement. Harassment, personal attacks, and dismissive behavior are not welcome.
