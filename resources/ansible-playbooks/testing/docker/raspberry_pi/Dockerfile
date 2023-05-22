FROM public.ecr.aws/ubuntu/ubuntu:latest

ENV USER=ansible

# Add sudo and openssh-server
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install openssh-server sudo -y

# Setup running user on the container with sudo rights and
# password-less ssh login
RUN useradd -m ${USER}
RUN adduser ${USER} sudo
RUN echo "${USER} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/sudoers
RUN passwd -d ${USER}
RUN sed -i'' -e's/^#PermitRootLogin prohibit-password$/PermitRootLogin yes/' /etc/ssh/sshd_config \
        && sed -i'' -e's/^#PasswordAuthentication yes$/PasswordAuthentication yes/' /etc/ssh/sshd_config \
        && sed -i'' -e's/^#PermitEmptyPasswords no$/PermitEmptyPasswords yes/' /etc/ssh/sshd_config \
        && sed -i'' -e's/^UsePAM yes/UsePAM no/' /etc/ssh/sshd_config

RUN useradd -m gitlab-runner
RUN adduser gitlab-runner sudo
RUN echo "gitlab-runner ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/sudoers

# start ssh with port exposed
USER root
RUN service ssh start

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
