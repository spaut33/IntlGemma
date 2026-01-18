# Quick Start Guide

Get up and running with TranslateGemma in 5 minutes.

## Prerequisites

- Docker + Docker Compose
- NVIDIA GPU with CUDA support
- NVIDIA Container Toolkit

## Installation

```bash
# 1. Clone repository
git clone <repository-url>
cd translategemma

# 2. Build image (takes 5-10 minutes first time)
docker-compose build

# 3. Test installation
./docker-run.sh --help
```

## Your First Translation

```bash
# 1. Create test messages
mkdir -p my_messages
cat > my_messages/en.json << 'EOF'
{
  "hello": "Hello",
  "world": "World",
  "greeting": "Hello {name}!"
}
EOF

echo '{}' > my_messages/ru.json

# 2. Update docker-compose.yml to mount your directory
# Add under cli.volumes:
#   - ./my_messages:/app/my_messages

# 3. Translate
./docker-run.sh translate-missing ./my_messages -t ru

# 4. Check result
cat my_messages/ru.json
```

## Common Commands

```bash
# Translate missing keys to all languages
./docker-run.sh translate-missing ./messages --all-languages

# Translate specific languages
./docker-run.sh translate-missing ./messages -t ru -t de

# Check completeness
./docker-run.sh check ./messages --all-languages

# Show supported languages
./docker-run.sh languages

# Start API server
docker-compose up -d api
```

## Using Makefile (Even Easier)

```bash
# Build
make build

# Translate test messages
make translate-missing

# Check completeness
make check

# Show languages
make languages

# Start API
make up

# Stop API
make down
```

## Next Steps

- Read [DOCKER.md](DOCKER.md) for detailed Docker usage
- Read [EXAMPLES.md](EXAMPLES.md) for real-world examples
- Read [README.md](README.md) for complete documentation

## Troubleshooting

### GPU not detected

```bash
docker run --rm --gpus all nvidia/cuda:13.0.0-base-ubuntu24.04 nvidia-smi
```

### Out of memory

```bash
./docker-run.sh translate-missing ./messages -t ru --batch-size 10
```

### Slow downloads

Model downloads to `~/.cache/huggingface` (first run only, ~9GB).

## Support

- Issues: GitHub Issues
- Examples: [EXAMPLES.md](EXAMPLES.md)
- Docker guide: [DOCKER.md](DOCKER.md)
