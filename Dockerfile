FROM python:3.13-slim

WORKDIR /code

# Copy dependencies and install them
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

WORKDIR /workspace
# Copy everything from your local directory into the container
COPY . .

EXPOSE 8000

# Run uvicorn pointing to the app module
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

