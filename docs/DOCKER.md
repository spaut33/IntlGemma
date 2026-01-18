# Docker Usage Guide

This guide covers running TranslateGemma in Docker containers with GPU support.

## Prerequisites

- Docker Engine 24.0+
- Docker Compose v2.0+
- NVIDIA Container Toolkit (for GPU support)
- NVIDIA GPU with CUDA 13.0+ support

### Install NVIDIA Container Toolkit

```bash
# Ubuntu/Debian
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## Quick Start

### 1. Build the Image

```bash
docker-compose build
```

This creates an image with:
- CUDA 13.0 runtime
- Python 3.12
- uv package manager
- All dependencies installed

### 2. Run API Server

```bash
# Start API server in background
docker-compose up -d api

# Check logs
docker-compose logs -f api

# API available at http://localhost:5000
```

### 3. Run CLI Commands

#### Using docker-run.sh (Recommended)

```bash
# Check help
./docker-run.sh --help

# Translate missing keys
./docker-run.sh translate-missing ./test_messages --all-languages

# Check completeness
./docker-run.sh check ./test_messages --all-languages

# Show supported languages
./docker-run.sh languages
```

#### Using docker-compose run

```bash
# Translate missing keys to Russian
docker-compose run --rm cli translate-intl translate-missing ./test_messages -t ru

# Translate all keys to all languages
docker-compose run --rm cli translate-intl translate-all ./test_messages --all-languages

# Check translation completeness
docker-compose run --rm cli translate-intl check ./test_messages --all-languages -o table

# Show supported languages
docker-compose run --rm cli translate-intl languages
```

#### Using docker run directly

```bash
# Build first
docker build -t translategemma .

# Run CLI
docker run --rm --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v $(pwd)/test_messages:/app/test_messages \
  translategemma \
  uv run translate-intl translate-missing ./test_messages -t ru
```

## Working with Your Messages

### Mount Your Messages Directory

Create or use existing `messages/` directory:

```bash
mkdir -p messages
# Add your en.json, ru.json, etc.
```

Update `docker-compose.yml` to mount your directory:

```yaml
cli:
  volumes:
    - ~/.cache/huggingface:/root/.cache/huggingface
    - ./messages:/app/messages  # Your messages directory
```

Then run:

```bash
./docker-run.sh translate-missing ./messages --all-languages
```

## Advanced Usage

### Custom Batch Size

```bash
./docker-run.sh translate-missing ./messages -t ru --batch-size 50
```

### Multiple Languages

```bash
./docker-run.sh translate-missing ./messages -t ru -t de -t fr
```

### Output Formats

```bash
# JSON output (for CI/CD)
./docker-run.sh check ./messages --all-languages -o json > report.json

# Markdown output
./docker-run.sh check ./messages --all-languages -o markdown > TRANSLATIONS.md
```

## Container Management

### Start API Server

```bash
# Start in background
docker-compose up -d api

# View logs
docker-compose logs -f api

# Restart
docker-compose restart api
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop specific service
docker-compose stop api
```

### Remove Containers and Images

```bash
# Remove containers
docker-compose down

# Remove images
docker rmi translategemma
```

## Troubleshooting

### GPU Not Detected

Check NVIDIA runtime:

```bash
docker run --rm --gpus all nvidia/cuda:13.0.0-base-ubuntu24.04 nvidia-smi
```

If error, ensure nvidia-container-toolkit is installed and Docker restarted.

### Out of Memory

Reduce batch size:

```bash
./docker-run.sh translate-missing ./messages -t ru --batch-size 10
```

### Model Download Issues

Model downloads to `~/.cache/huggingface` (mounted volume). Ensure:
- Stable internet connection
- ~20GB free space
- Write permissions

Check cache:

```bash
ls -lh ~/.cache/huggingface/hub/
```

### Permission Issues

If you encounter permission issues with mounted volumes:

```bash
# Run with current user
docker-compose run --rm --user $(id -u):$(id -g) cli translate-intl --help
```

## Performance

### GPU Memory Usage

- Model size: ~9GB
- Runtime VRAM: ~8GB (with batch_size=20)
- Recommended: RTX 3080 (10GB) or better

### Batch Size Recommendations

| GPU VRAM | Recommended Batch Size |
|----------|------------------------|
| 8GB      | 10-15                 |
| 10GB+    | 20-30                 |
| 16GB+    | 40-50                 |
| 24GB+    | 50-100                |

### Translation Speed

With RTX 3080:
- Batch processing: ~10-15 keys/second
- Individual processing: ~3-5 keys/second

## Example Workflows

### Complete Translation Pipeline

```bash
# 1. Check current status
./docker-run.sh check ./messages --all-languages -o table

# 2. Translate missing keys
./docker-run.sh translate-missing ./messages --all-languages --batch-size 30

# 3. Verify completeness
./docker-run.sh check ./messages --all-languages -o table
```

### CI/CD Integration

```bash
# In CI/CD pipeline
docker build -t translategemma .

docker run --rm --gpus all \
  -v $(pwd)/messages:/app/messages \
  translategemma \
  uv run translate-intl check ./messages --all-languages -o json > report.json

# Parse report.json and fail if completeness < 100%
```

## Development

### Interactive Shell

```bash
docker-compose run --rm cli bash
```

Inside container:

```bash
# Run CLI
uv run translate-intl --help

# Run API
uv run python api.py

# Check GPU
nvidia-smi
```

### Rebuild After Changes

```bash
# Rebuild image
docker-compose build cli

# Force rebuild without cache
docker-compose build --no-cache cli
```

## API Server Details

### Start API

```bash
docker-compose up -d api
```

### Test API

```bash
# Health check
curl http://localhost:5000/health

# Translate
curl -X POST http://localhost:5000/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world",
    "source_lang": "en",
    "target_lang": "ru"
  }'
```

### API Logs

```bash
# Follow logs
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

## Resource Limits

Default configuration in `docker-compose.yml`:
- Shared memory: 2GB
- GPU: All available
- No CPU/RAM limits

Adjust if needed:

```yaml
cli:
  shm_size: '4gb'
  deploy:
    resources:
      limits:
        cpus: '8'
        memory: 16G
      reservations:
        devices:
          - driver: nvidia
            device_ids: ['0']  # Specific GPU
            capabilities: [gpu]
```

## Support

For issues, see:
- Main README.md for general usage
- Check container logs: `docker-compose logs`
- GPU issues: Verify with `nvidia-smi`
