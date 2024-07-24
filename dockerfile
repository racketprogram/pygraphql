FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip cache purge && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]