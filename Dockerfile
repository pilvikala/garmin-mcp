FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py auth_setup.py ./

# Token directory (mount a volume here)
RUN mkdir -p /data/garmin_tokens

ENV GARMIN_TOKEN_DIR=/data/garmin_tokens
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE 8000

CMD ["python", "server.py"]
