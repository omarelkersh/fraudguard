FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Dependencies layer: the dashboard reuses the investigator package, so both pyprojects
COPY pyproject.toml uv.lock ./
COPY services/dashboard/pyproject.toml services/dashboard/
COPY services/investigator/pyproject.toml services/investigator/
RUN uv sync --frozen --no-dev --package fraudguard-dashboard --no-install-workspace

# Code layer
COPY services/dashboard/ services/dashboard/
COPY services/investigator/ services/investigator/
RUN uv sync --frozen --no-dev --package fraudguard-dashboard

RUN useradd --create-home appuser
USER appuser

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8501
CMD ["streamlit", "run", "services/dashboard/src/fraudguard_dashboard/app.py", \
     "--server.headless", "true", "--browser.gatherUsageStats", "false", "--server.address", "0.0.0.0"]
