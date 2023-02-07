ARG BUILD_IMAGE="artefact.skao.int/ska-tango-images-pytango-builder:9.3.32"
ARG BASE_IMAGE="artefact.skao.int/ska-tango-images-pytango-runtime:9.3.19"
FROM $BUILD_IMAGE AS buildenv
FROM $BASE_IMAGE

USER root

RUN apt-get update && apt-get install openssh-client gnupg2 gawk yamllint curl git vim -y
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

RUN poetry config virtualenvs.create false

WORKDIR /app
COPY --chown=tango:tango . /app

RUN pip install --upgrade poetry
RUN poetry install

USER tango

RUN poetry config virtualenvs.create false
RUN poetry shell && poetry install

ENTRYPOINT [ "/bin/bash" ]
