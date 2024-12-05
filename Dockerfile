FROM python:3.14-rc-bookworm

RUN apt-get update && \
    apt-get install -y --no-install-recommends tmux graphviz
