import asyncio
import websockets
import json
import os

clients = {}  # client_id (str) => websocket
history_file = "chat_history.json"
chat_history = []

# Load chat history
if os.path.exists(history_file):
    with open(history_file, "r") as f:
        try:
            chat_history = json.load(f)
        except json.JSONDecodeError:
            chat_history = []

# IDs allowed
MAX_CLIENTS = 2
allowed_ids = {"1", "2"}

async def handler(websocket):
    # Assign an available ID or reject connection if full
    available_ids = allowed_ids - clients.keys()
    if not available_ids:
        # No ID available, refuse connection
        await websocket.send(json.dumps({"error": "Server full. Try later."}))
        await websocket.close()
        print("Connection refused: server full")
        return

    client_id = available_ids.pop()
    clients[client_id] = websocket
    print(f"Client {client_id} connected")

    try:
        # Send assigned ID to client
        await websocket.send(json.dumps({"client_id": client_id}))

        # Send chat history to the new client
        for msg in chat_history:
            await websocket.send(json.dumps(msg))

        async for message in websocket:
            print(f"Received from {client_id}: {message}")
            try:
                data = json.loads(message)
                text = data.get("message", "")
                target = data.get("target", "")

                message_data = {
                    "from": client_id,
                    "message": text
                }

                # Save to history and file
                chat_history.append(message_data)
                with open(history_file, "w") as f:
                    json.dump(chat_history, f)

                if target and target in clients:
                    # Private message
                    await clients[target].send(json.dumps(message_data))
                else:
                    # Broadcast message
                    for cid, ws in clients.items():
                        await ws.send(json.dumps(message_data))
            except Exception as e:
                print(f"Error processing message: {e}")

    except websockets.ConnectionClosed:
        print(f"Client {client_id} disconnected")
    finally:
        clients.pop(client_id, None)

async def main():
    print("Server started at ws://localhost:8888")
    async with websockets.serve(handler, "localhost", 8888):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
