# Contributing to Chronos-K8s-Scheduler

Thank you for your interest in contributing to Chronos! This guide will help you get started.

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker and Docker Compose
- Git

### Local Setup

```bash
# Clone the repo
git clone https://github.com/gpshukla/DistributedTaskScheduler-Chronos.git
cd DistributedTaskScheduler-Chronos

# Install Python dependencies
pip install -e ".[dev]"

# Copy environment config
cp .env.example .env

# Start infrastructure (PostgreSQL, Redis, etcd)
docker compose up -d postgres redis etcd

# Run database migrations
alembic upgrade head

# Run the master
uvicorn chronos.master.app:create_app --factory --reload

# Run a worker (separate terminal)
python -m chronos.worker.main

# Run the dashboard (separate terminal)
cd dashboard && npm install && npm run dev
```

## How to Contribute

### Reporting Bugs

Open an issue with:
- A clear, descriptive title
- Steps to reproduce the behavior
- Expected vs actual behavior
- Logs or screenshots if applicable
- Your environment (OS, Python version, Docker version)

### Suggesting Features

Open an issue with the `enhancement` label describing:
- The problem you're trying to solve
- Your proposed solution
- Any alternatives you've considered

### Submitting Changes

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** following the code style guidelines below
4. **Write or update tests** for your changes
5. **Run the test suite** to ensure nothing is broken:
   ```bash
   make test-unit
   ```
6. **Commit** with a clear message:
   ```bash
   git commit -m "feat: add support for custom scheduling algorithms"
   ```
7. **Push** and open a **Pull Request** against `main`

## Code Style

### Python (Backend)

- **Formatter/Linter**: [Ruff](https://docs.astral.sh/ruff/) (configured in `pyproject.toml`)
- **Type checking**: [mypy](https://mypy-lang.org/) with strict mode
- **Line length**: 100 characters
- **Target**: Python 3.12

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/
```

### TypeScript (Dashboard)

- Follow existing patterns in `dashboard/src/`
- Use TypeScript interfaces for all data types (see `dashboard/src/types/`)

## Commit Message Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Usage |
|---|---|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `refactor:` | Code change that neither fixes a bug nor adds a feature |
| `test:` | Adding or updating tests |
| `chore:` | Build process, CI, or tooling changes |

## Testing

```bash
# Unit tests (no external dependencies)
make test-unit

# Integration tests (requires Docker daemon)
pytest tests/integration/ -m integration

# Coverage report
make test-cov
```

- All new features should include unit tests
- Integration tests are required for Docker execution or infrastructure changes
- Aim for meaningful coverage, not 100% line coverage

## Project Structure

Key areas for contribution:

| Area | Path | Description |
|---|---|---|
| Scheduler | `src/chronos/master/scheduler/` | Scheduling algorithms, preemption |
| Worker | `src/chronos/worker/` | Task execution, Docker lifecycle |
| API | `src/chronos/master/api/` | FastAPI routes |
| Dashboard | `dashboard/src/` | React frontend |
| Helm/K8s | `k8s/` | Kubernetes deployment |
| Tests | `tests/` | Unit and integration tests |

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR
- Update documentation if behavior changes
- Ensure all CI checks pass
- Be responsive to review feedback

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Questions?

Open a [Discussion](https://github.com/gpshukla/DistributedTaskScheduler-Chronos/discussions) or reach out via Issues.
