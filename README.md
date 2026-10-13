# Webhook Provider & Subscriber demo

This project demonstrates a simple webhook architecture implemented with FastAPI and Docker Compose. It consists of a **Provider** (server) that streams automated events and a **Subscriber** (client) that registers for, receives, and eventually unregisters from the event stream.

---

## Architecture overview

* **Provider (`server.py`)**: A FastAPI application running on port `8000`. It manages webhook registrations and spawns background threads to send continuous event streams to registered subscribers.
* **Subscriber (`client.py`)**: A FastAPI application running on port `9000`. It automatically registers itself with the provider upon startup, listens for incoming webhook payloads, and unregisters itself after receiving 3 events.
* **Docker Compose (`docker-compose.yml`)**: Orchestrates both containers, linking them on a shared network environment.

---

## Project files

* `server.py`: The webhook provider server.
* `client.py`: The webhook subscriber client.
* `Dockerfile`: Container configuration for building both Python services.
* `docker-compose.yml`: Multi-container orchestration definition.
* `requirements.txt`: Project Python dependencies (`fastapi`, `uvicorn`, `requests`, `pydantic`).

---

## Running with Docker Compose

The easiest way to run the application is using Docker Compose.

### Prerequisites
* [Docker](https://docs.docker.com/get-docker/) installed on your machine.
* [Docker Compose](https://docs.docker.com/compose/install/) installed.

### Running the application

1. Open a terminal in the directory containing the project files.
2. Build and start the containers using Docker Compose:
       docker compose up --build
3. Watch the logs as:
   * The server starts up on port 8000.
   * The client starts up on port 9000, waits briefly, and registers its webhook endpoint with the server.
   * The server begins pushing events every second
   * Once the client receives 3 events, it automatically triggers an unregistration request and stops the stream
4. Stop and clean up the containers by pressing `Ctrl+C` in your terminal, then running:

## Running standalone

This produces more clear output by running the server and client in separate terminal windows:

1. `python ./server.py`
2. `python ./client.py`
