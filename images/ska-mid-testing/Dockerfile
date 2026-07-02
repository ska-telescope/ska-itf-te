FROM registry.gitlab.com/ska-telescope/ska-mid-itf-engineering-tools/ska-mid-itf-engineering-tools:0.10.4

RUN rm -rf /app/.venv

WORKDIR /app

ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA=$GIT_COMMIT_SHA

RUN git clone https://gitlab.com/ska-telescope/ska-mid.git

WORKDIR /app/ska-mid

RUN git checkout $GIT_COMMIT_SHA && \
    git submodule init && \
    git submodule update && \
    mkdir -p config && \
    (command -v uv >/dev/null 2>&1 || python3 -m pip install uv) && \
    python3 -m pip install --no-cache-dir "packaging>=24.2" && \
    rm -rf .venv && \
    uv venv .venv && \
    uv pip install --python .venv/bin/python "setuptools>=68" "wheel" "packaging>=24.2" && \
    uv sync --all-groups --no-build-isolation

