from contextlib import asynccontextmanager
import threading
import time
from fastapi import FastAPI
import requests
import os

is_docker = os.path.exists("/.dockerenv")

server_name = 'server' if is_docker else '127.0.0.1'
client_name = 'client' if is_docker else '127.0.0.1'

WEBHOOK_PORT = 9000
PROVIDER_URL = f"http://{server_name}:8000"
MY_WEBHOOK_ID = "sub_999_stream"
MY_LISTENER_URL = f"http://{client_name}:{WEBHOOK_PORT}/webhook-receiver"

def create_pidfile():
    for pidfile_dir in ["/app/tmp", "/tmp"]:
        pidfilename = f"{pidfile_dir}/webhook_client.pid"
        with open(pidfilename, 'w') as pidfile:
            print(os.getpid(), file=pidfile)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_pidfile()
    threading.Thread(target=register_with_provider, daemon=True).start()
    yield
    print("[Subscriber] Lifespan context exited. Subscriber is shutting down.")

app = FastAPI(title="Webhook Subscriber", lifespan=lifespan)

# Counter to track incoming events
event_counter = 0
counter_lock = threading.Lock()

def register_with_provider():
    """Runs in a brief delay to ensure the local FastAPI server has started first."""
    time.sleep(1) 
    print(f"[Subscriber] Sending registration request to Provider...")
    try:
        registration_data = {
            "webhook_id": MY_WEBHOOK_ID,
            "url": MY_LISTENER_URL
        }
        res = requests.post(f"{PROVIDER_URL}/api/register", json=registration_data, timeout=5)
        print(f"[Subscriber] Registration Server Response: {res.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[Subscriber] Registration failed! Is the Provider script running? Error: {e}")

def trigger_unregistration():
    """Sends a delete request to remove the webhook subscription."""
    print(f"[Subscriber] Sending unregistration command...")
    try:
        res = requests.delete(f"{PROVIDER_URL}/api/unregister/{MY_WEBHOOK_ID}", timeout=5)
        print(f"[Subscriber] Unregistration Server Response: {res.json()}")
    except requests.exceptions.RequestException as e:
        print(f"[Subscriber] Failed to cleanly unregister: {e}")

@app.post("/webhook-receiver")
def receive_event(payload: dict):
    global event_counter
    
    with counter_lock:
        event_counter += 1
        current_count = event_counter

    print(f"[Subscriber] Received event #{payload.get('event_number')} -> "
          f"Message: {payload.get('message')}")
    
    if current_count == 3:
        print("Done! Unregistering the webhook in a separate thread")
        # unregister in a separate thread to avoid blocking the webhook response
        threading.Thread(target=trigger_unregistration, daemon=True).start()
        print("Press Control-C to exit")
        
    return {"status": "acknowledged"}


if __name__ == "__main__":
    import uvicorn
    
    print(f"[Subscriber] Webhook listener running on port {WEBHOOK_PORT}")
    # uvicorn.run(app, host="127.0.0.1", port=WEBHOOK_PORT)
    uvicorn.run(app, host="0.0.0.0", port=WEBHOOK_PORT)
