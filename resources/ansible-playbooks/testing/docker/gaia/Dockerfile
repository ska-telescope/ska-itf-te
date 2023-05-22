FROM public.ecr.aws/ubuntu/ubuntu:latest

ARG USER=${USER}

# Add sudo and openssh-server
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install openssh-server sudo sshpass -y

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

RUN groupadd atlas
RUN sh -x \
    && users="a.debeer benjamin.lunsky d.gammon g.leroux j.coetzer monde.manzini n.nzotho p.jordaan t.tsotetsi vhulahani.manukha" \
    && for u in ${users}; \
       do \
              useradd -m ${u}; \
              adduser ${u} atlas; \
              adduser ${u} sudo; \
              echo "${u}:${u}" | chpasswd; \
              echo "Processed ${u}"; \
       done

# start ssh with port exposed
USER root
RUN service ssh start

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
