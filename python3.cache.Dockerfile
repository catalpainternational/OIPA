FROM python:3.7.0
LABEL maintainer "Joshua Brooks<josh@catalpa.io>"
# When building this image, it's cached to the max. Requires host to
# be running apt-cacher-ng and devpi.
# --build-arg HOST=$(ip -4 addr show docker0 | grep -Po 'inet \K[\d.]+') .

# == Caching ==
ARG HOST

# Apt proxy
RUN echo "Acquire::http::Proxy \"http://${HOST}:3142\";" > /etc/apt/apt.conf.d/00aptproxy

# Installation of packages: pip, apt
RUN apt-get update && apt-get install -y \
    python3-dev \
    postgresql-client \
    git \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    python-dev \
    binutils \
    gdal-bin \
    libgeos-dev \
    libproj-dev \
    antiword \
    binutils \
    bzip2 \
    catdoc \
    docx2txt \
    gzip \
    html2text \
    libimage-exiftool-perl \
    odt2txt \
    perl \
    poppler-utils \
    unrar-free \
    unrtf \
    unzip \
    libsqlite3-dev  \
    libsqlite3-mod-spatialite \
    sqlite3 \
    libpq-dev \
    python3-psycopg2 \
    uwsgi \
    uwsgi-plugin-python3 \
    && apt-get clean

RUN useradd --create-home --shell /bin/sh djangorunner
RUN groupadd -r uwsgi && usermod --append --groups uwsgi djangorunner
# =================
# Pip cache
RUN mkdir -p ~djangorunner/.pip
RUN echo '[global]' > ~djangorunner/.pip/pip.conf && \
    echo "index-url = http://${HOST}:3141/root/pypi/+simple/" >> ~djangorunner/.pip/pip.conf && \
    echo '[search]' >> ~djangorunner/.pip/pip.conf && \
    echo "index = http://${HOST}:3141/root/pypi/" >> ~djangorunner/.pip/pip.conf
# =================

USER djangorunner
ENV PATH=/home/djangorunner/.local/bin:${PATH}

COPY OIPA/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade --user --trusted-host ${HOST} -r requirements.txt
    
# == Undo caching ==
USER root
RUN rm /etc/apt/apt.conf.d/00aptproxy
RUN rm ~djangorunner/.pip/pip.conf

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app/src
WORKDIR /app/src/OIPA
ADD . /app/src

USER root
RUN mkdir -p /app/src/public && chown -R djangorunner:uwsgi /app/src/public
RUN mkdir -p /var/log/oipa/oipa/ && chown -R djangorunner:uwsgi /var/log/oipa/oipa/

EXPOSE 8000
USER djangorunner
CMD ["/app/src/bin/docker-cmd.sh"]

