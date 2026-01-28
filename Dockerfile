FROM nvidia/cuda:13.0.0-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/.local/bin:/app/.venv/bin:$PATH"
# Enable CUDA support for llama-cpp-python during compilation
ENV CMAKE_ARGS="-DLLAMA_CUDA=on"

RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

# --- CRITICAL FIX: CACHE DEPENDENCIES ---
# Copy ONLY the dependency files first.
# This layer will be cached unless pyproject.toml or uv.lock changes.
COPY pyproject.toml uv.lock ./

# Install dependencies. This compiles llama-cpp-python once and saves it.
RUN uv sync --no-install-project --no-dev

# --- COPY SOURCE CODE LATER ---
# Now copy the rest of the project. Changes here won't trigger re-compilation above.
COPY src/ src/
COPY README.md .

# Finalize the installation (this is fast, just links the project)
RUN uv sync --no-dev

# Default command
CMD ["uv", "run", "translate-intl", "--help"]
