FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# 4. DEPENDENCIES LAYER (changes rarely → cached)
#    Copy ONLY the files that define dependencies, then install them, without your code yet
COPY pyproject.toml uv.lock ./
COPY services/generator/pyproject.toml services/generator/
RUN uv sync --frozen --no-dev --package fraudguard-generator --no-install-workspace

# 5. CODE LAYER (changes often → rebuilt every time, but fast)
COPY services/generator/ services/generator/
RUN uv sync --frozen --no-dev --package fraudguard-generator

# 6. Security: don't run as root inside the container
RUN useradd --create-home appuser
USER appuser

# 7. Put the virtual environment's commands on PATH, then set the default command
ENV PATH="/app/.venv/bin:$PATH"
CMD ["fraudguard-generator"]
