FROM public.ecr.aws/ubuntu/ubuntu:latest

ARG USER=${USER}
ARG USER=${USER}


# Add sudo and openssh-server
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install openssh-server sudo sshpass -y

RUN groupadd atlas
RUN useradd -m ${USER}
RUN adduser ${USER} atlas
RUN adduser ${USER} sudo
RUN echo "${USER}:${USER}" | chpasswd

# start ssh with port exposed
USER root
RUN service ssh start

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
