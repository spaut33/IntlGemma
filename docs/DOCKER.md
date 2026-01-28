# Docker Usage

Run TranslateGemma CLI in a container with GPU support.

## Requirements

- Docker Engine 24+
- Docker Compose v2 (`docker compose`)
- NVIDIA Container Toolkit (for GPU acceleration)

## Build

```bash
docker compose build cli
```

## Run (recommended)

```bash
./docker-run.sh translate-missing ./messages --all-languages
```

## Run without the helper script

```bash
docker compose run --rm cli translate-intl translate-missing ./messages -t de
```

## Direct docker run

```bash
docker build -t translategemma .

docker run --rm --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v $(pwd)/messages:/app/messages \
  translategemma \
  uv run translate-intl translate-missing ./messages -t de
```

## Volumes

- `./messages` is mounted to `/app/messages` in `docker-compose.yml`.
- `~/.cache/huggingface` is mounted to keep the model cache between runs.

To use a different messages directory, update `docker-compose.yml` or override
with `-v /path/to/messages:/app/messages`.

## Troubleshooting

- GPU not detected:
  ```bash
  docker run --rm --gpus all nvidia/cuda:13.0.0-base-ubuntu24.04 nvidia-smi
  ```
- Out of memory: lower `--batch-size`.
- Model download issues: ensure `~/.cache/huggingface` is writable and has space.

## Makefile Shortcuts (Docker)

```bash
make build
make translate-missing
make check
make languages
```
