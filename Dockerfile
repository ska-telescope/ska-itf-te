FROM registry.gitlab.com/ska-telescope/ska-mid-itf-engineering-tools/ska-mid-itf-engineering-tools:0.10.0

RUN rm -rf /app/.venv

WORKDIR /app/ska-mid-itf

COPY . .

ARG GIT_COMMIT_SHA
ENV GIT_COMMIT_SHA=$GIT_COMMIT_SHA

RUN git checkout $GIT_COMMIT_SHA && \
    git submodule init && \
    git submodule update && \
    mkdir -p config && \
    poetry config virtualenvs.in-project true && \
    rm -rf .venv && \
    poetry install --no-cache
