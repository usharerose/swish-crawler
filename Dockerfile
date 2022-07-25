FROM python:3.8-alpine AS prod
MAINTAINER usharerose

RUN apk update && \
    apk add --no-cache tzdata bash make vim curl && \
    apk upgrade && \
    rm -rf /var/cache/apk/*

# Setup base folder
RUN addgroup -S -g 1000 swish && \
    adduser -S -G swish -u 1000 swish && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    mkdir -p /home/swish/.ssh && \
    mkdir -p /services/swish/ && \
    chown -R root:swish /services/swish/ && \
    chown -R swish:swish /home/swish/ && \
    chmod -R 750 /home/swish/ && \
    chmod -R 750 /services/swish/

# Set workdir
WORKDIR /services/swish/swish-crawler/
RUN chown -R swish:swish /services/swish/swish-crawler/

COPY requirements.txt requirements-test.txt ./

# install dependencies
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r /services/swish/swish-crawler/requirements.txt && \
    python -m pip install --no-cache-dir -r /services/swish/swish-crawler/requirements-test.txt && \
    find /usr/local/ -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete

# Remove requirements files
RUN find . -type f -name 'requirements*.txt' -delete

# set permission
RUN chmod -R o-w /services/swish/swish-crawler/

# Copy source code folder
COPY . .

# Add PYTHONPATH
ENV PYTHONPATH /services/swish/swish-crawler/

# User must be swish
USER swish

CMD ["sleep", "infinity"]
