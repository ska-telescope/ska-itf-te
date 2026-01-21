FROM registry.gitlab.com/ska-telescope/ska-mid-itf-engineering-tools/ska-mid-itf-engineering-tools:0.10.1-rc.2-dev.ce0b8d5ef

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
    poetry config virtualenvs.in-project true && \
    rm -rf .venv && \
    poetry install --no-cache

