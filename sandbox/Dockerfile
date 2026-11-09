FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir \
    pandas==2.2.3 \
    numpy==2.2.2

RUN useradd \
    --create-home \
    --uid 10001 \
    --shell /usr/sbin/nologin \
    sandboxuser

WORKDIR /sandbox

COPY --chown=sandboxuser:sandboxuser runner.py /sandbox/runner.py

RUN mkdir -p /input \
    && chown -R sandboxuser:sandboxuser /sandbox \
    && chmod -R 555 /sandbox

USER 10001:10001

ENTRYPOINT ["python", "-I", "/sandbox/runner.py"]