FROM artefact.skao.int/ska-tango-images-pytango-builder:9.3.32

RUN apt-get update && apt-get install openssh-client gnupg2 gawk yamllint curl git vim graphviz telnet -y
RUN curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

ENV PATH=/root/.local/bin:$PATH

RUN python3 -m pip install --user pipx && python3 -m pipx ensurepath

RUN pipx install poetry==1.3.2

RUN poetry config virtualenvs.in-project true

RUN pip install virtualenv

# re-install poetry for user tango also

USER tango

ENV PATH=/home/tango/.local/bin:$PATH

RUN python3 -m pip install --user pipx && python3 -m pipx ensurepath

RUN pipx install poetry==1.3.2

RUN poetry config virtualenvs.in-project true

RUN pip install virtualenv
