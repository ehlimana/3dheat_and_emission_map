FROM python:3.11

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 7860

CMD ["panel", "serve", "hugging_app.py", \
     "--address", "0.0.0.0", \
     "--port", "7860", \
     "--allow-websocket-origin=*"]