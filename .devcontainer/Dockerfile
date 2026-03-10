FROM registry.gitlab.com/ska-telescope/ska-mid-itf-engineering-tools/ska-mid-itf-engineering-tools:0.10.3

RUN curl -o ~/.git-completion.bash https://raw.githubusercontent.com/git/git/master/contrib/completion/git-completion.bash && \
    echo "source ~/.git-completion.bash" >> ~/.bashrc

ENV PIPX_BIN_DIR="/usr/local/bin"
ENV PIPX_VERSION="1.7.1"
ENV POETRY_VERSION="2.1.3"

RUN apt-get install -y --no-install-recommends pipx

RUN pipx install poetry==${POETRY_VERSION}
