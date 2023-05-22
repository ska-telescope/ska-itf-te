FROM public.ecr.aws/ubuntu/ubuntu:latest

# Add sudo and openssh-server
ENV DEBIAN_FRONTEND=noninteractive
RUN apt update && apt install openssh-server sudo sshpass -y

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
