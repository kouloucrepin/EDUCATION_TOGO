FROM python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de

RUN useradd -m -u 1000 user

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user:user app.py ./
COPY --chown=user:user scripts scripts/
COPY --chown=user:user modules_visu modules_visu/
COPY --chown=user:user agent_ia agent_ia/
COPY --chown=user:user connaissance_ia connaissance_ia/
COPY --chown=user:user static static/
COPY --chown=user:user templates templates/
COPY --chown=user:user data data/
COPY --chown=user:user data_togo data_togo/

USER user
ENV PYTHONUNBUFFERED=1 \
    HOME=/home/user

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "8", "--timeout", "300", "app:app"]
