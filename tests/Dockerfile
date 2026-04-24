ARG BASE_IMAGE=ngapp-base
FROM ${BASE_IMAGE}

WORKDIR /app

COPY tests/ tests/

ENV PYTHONPATH=src:.

CMD ["pytest", "tests/", "-vv", "-s"]