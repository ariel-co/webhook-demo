import threading
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import requests

app = FastAPI(title="Webhook Provider")
PROVIDER_PORT = 8000

# webhook_id: target_url ...
subscriptions = {}
# active sender threads
active_threads = {}

class RegisterPayload(BaseModel):
    webhook_id: str
    url: HttpUrl

def event_sender(webhook_id: str, target_url: str):
    """Sends a webhook event every second until the subscription is deleted."""
    print(f"[Provider] Started event sender for subscription: {webhook_id}")
    event_count = 0
    
    while webhook_id in subscriptions:
        event_count += 1
        payload = {
            "webhook_id": webhook_id,
            "event_number": event_count,
            "message": f"event #{event_count}"
        }
        try:
            # Send event to subscriber
            requests.post(str(target_url), json=payload, timeout=2)
        except requests.exceptions.RequestException:
            print(f"[Provider] Failed to deliver event #{event_count} to {target_url}")
            
        time.sleep(1)
        
    print(f"[Provider] Stopped event sender for subscription: {webhook_id}")

@app.post("/api/register")
def register_webhook(data: RegisterPayload):
    webhook_id = data.webhook_id
    
    if webhook_id in subscriptions:
        raise HTTPException(status_code=400, detail="Webhook ID already registered")
        
    subscriptions[webhook_id] = data.url
    
    # Start the continuous 1-second event stream in a background thread
    t = threading.Thread(target=event_sender, args=(webhook_id, data.url), daemon=True)
    active_threads[webhook_id] = t
    t.start()
    
    return {"status": "registered", "webhook_id": webhook_id}

@app.delete("/api/unregister/{webhook_id}")
def unregister_webhook(webhook_id: str):
    if webhook_id not in subscriptions:
        raise HTTPException(status_code=404, detail="Webhook registration not found")
        
    # Removing from the dict causes the while loop in event_sender to exit
    del subscriptions[webhook_id]
    if webhook_id in active_threads:
        del active_threads[webhook_id]
        
    print(f"[Provider] deleted registration: {webhook_id}")
    return {"status": "deleted", "webhook_id": webhook_id}

@app.get("/")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print(f"[Provider] Starting webhook provider on port {PROVIDER_PORT}")
    uvicorn.run(app, host="127.0.0.1", port=PROVIDER_PORT)
