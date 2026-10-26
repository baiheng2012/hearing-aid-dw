ARG SUPERSET_VERSION
FROM apache/superset:${SUPERSET_VERSION}

USER root
RUN . /app/.venv/bin/activate && uv pip install psycopg2-binary
USER superset