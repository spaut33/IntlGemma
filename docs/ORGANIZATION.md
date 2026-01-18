# Project Organization

## Directory Structure

```
translategemma/
├── api.py                   # Flask API server
├── docker-compose.yml       # Docker services configuration
├── Dockerfile              # Docker image definition
├── .dockerignore           # Docker build exclusions
├── docker-run.sh           # CLI convenience script
├── .env.example            # Environment variables template
├── .gitignore              # Git exclusions
├── Makefile                # Build commands
├── pyproject.toml          # Project configuration
├── README.md               # Main documentation
│
├── docs/                   # 📚 Documentation
│   ├── README.md           # Documentation index
│   ├── QUICKSTART.md       # Quick start guide
│   ├── DOCKER.md           # Docker usage
│   ├── EXAMPLES.md         # Real-world examples
│   ├── CHECKLIST.md        # Pre-launch checklist
│   ├── PROJECT_STRUCTURE.md # Architecture
│   ├── IMPLEMENTATION_SUMMARY.md # Implementation details
│   └── FILES_CREATED.md    # File inventory
│
├── src/                    # 📦 Python package
│   └── translate_intl/
│       ├── cli.py          # CLI interface
│       ├── __main__.py     # Entry point
│       ├── core/           # Translation engine
│       ├── services/       # Business logic
│       ├── models/         # Data models
│       └── utils/          # Utilities
│
└── test_messages/          # 🧪 Test files
    ├── en.json
    ├── ru.json
    ├── de.json
    └── fr.json
```

## File Organization

### Root Directory

**Configuration files:**
- `pyproject.toml` - Python project configuration
- `docker-compose.yml` - Docker services
- `Dockerfile` - Docker image
- `Makefile` - Build automation

**Scripts:**
- `docker-run.sh` - CLI wrapper script
- `api.py` - Flask API server

**Documentation:**
- `README.md` - Main entry point
- `docs/` - Detailed guides

### Documentation (`docs/`)

All documentation is organized in the `docs/` directory:

**Getting Started:**
- `QUICKSTART.md` - 5-minute setup
- `DOCKER.md` - Docker guide

**Usage:**
- `EXAMPLES.md` - Workflows and examples
- `CHECKLIST.md` - Pre-launch verification

**Technical:**
- `PROJECT_STRUCTURE.md` - Architecture
- `IMPLEMENTATION_SUMMARY.md` - Implementation overview
- `FILES_CREATED.md` - Complete file list

### Source Code (`src/translate_intl/`)

Python package with modular structure:

**Core:**
- `core/translator.py` - TranslateGemma engine
- `core/config.py` - Configuration

**Services:**
- `services/translation_service.py` - Orchestration
- `services/file_service.py` - File I/O

**Utilities:**
- `utils/json_handler.py` - JSON operations
- `utils/progress.py` - UI components

## Quick Navigation

### For First-Time Users
1. Read `README.md`
2. Follow `docs/QUICKSTART.md`
3. Check `docs/EXAMPLES.md`

### For Docker Users
1. Read `docs/DOCKER.md`
2. Run `./docker-run.sh --help`
3. Check `Makefile` targets

### For Developers
1. Review `docs/PROJECT_STRUCTURE.md`
2. Check `src/translate_intl/`
3. Read `docs/IMPLEMENTATION_SUMMARY.md`

## Ignored Files

`.gitignore` excludes:
- Python cache (`__pycache__/`, `*.pyc`)
- Virtual environments (`.venv/`)
- IDE files (`.vscode/`, `.idea/`)
- Local translations (`messages/`)
- Backups (`*.json.bak`)
- Logs (`*.log`)

## Makefile Targets

Common commands:
```bash
make build              # Build Docker image
make up                 # Start API server
make translate-missing  # Translate test messages
make check              # Check completeness
make languages          # Show supported languages
```

## Documentation Index

See `docs/README.md` for complete documentation index.
