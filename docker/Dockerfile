FROM python:3.12-slim

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies (no-install-project keeps caching optimal)
RUN uv sync --frozen --no-cache --no-install-project

# Copy the entire project
COPY . /app

# Sync project
RUN uv sync --frozen --no-cache

# Make entrypoint executable
RUN chmod +x docker/entrypoint.sh

# Expose the API port
EXPOSE 8000

# Use the shell script as the entry point
ENTRYPOINT ["/app/docker/entrypoint.sh"]
