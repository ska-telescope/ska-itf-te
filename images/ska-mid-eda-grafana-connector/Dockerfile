FROM artefact.skao.int/ska-build-python:0.1.1 as base

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git vim iputils-ping netcat

RUN git clone https://gitlab.com/tango-controls/hdbpp/libhdbpp-grafana-connector.git \
    --depth=1 \
    --branch=skao-poc-eda-pyhdbpp-grafana-connector

WORKDIR /app/libhdbpp-grafana-connector

RUN poetry install