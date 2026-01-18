FROM nvidia/cuda:13.0.0-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY api.py .
COPY README.md .

# Install dependencies with uv
RUN uv sync

# Install Flask for API (optional dependency)
RUN uv pip install flask==3.1.2 pillow==12.1.0

# Expose API port
EXPOSE 5000

# Default command - run API server
# Can be overridden in docker-compose.yml or command line
CMD ["uv", "run", "python", "api.py"]
