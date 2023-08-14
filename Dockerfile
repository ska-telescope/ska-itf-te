# FROM artefact.skao.int/ska-tango-images-pytango-builder:9.3.32 AS buildenv
# RUN apt-get update && apt-get install gnupg2 -y

ARG BUILD_IMAGE="artefact.skao.int/ska-tango-images-pytango-builder:9.3.32"
ARG BASE_IMAGE="artefact.skao.int/ska-tango-images-pytango-runtime:9.3.19"
FROM $BUILD_IMAGE AS buildenv
FROM $BASE_IMAGE

USER root

RUN apt-get update && apt-get install gnupg2 -y
RUN poetry config virtualenvs.create false

WORKDIR /app
COPY --chown=tango:tango . /app

RUN pip install --upgrade poetry
RUN poetry install

# # hangs on: • Installing untokenize (0.1.1)
# # so use pip instead
# RUN poetry export --format requirements.txt --output poetry-requirements.txt --without-hashes && \
#     pip install -r poetry-requirements.txt && \
#     rm poetry-requirements.txt && pip install .

USER tango

RUN poetry config virtualenvs.create false
RUN poetry shell && poetry install
