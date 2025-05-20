import asyncio
import websockets
import json

clients = {}  # client_id (str) => websocket
next_client_id = 1  # contador para IDs nuevos

async def handler(websocket):
    global next_client_id
    client_id = str(next_client_id)
    next_client_id += 1
    clients[client_id] = websocket
    print(f"Client {client_id} connected")

    try:
        # Enviar ID asignado al cliente
        await websocket.send(json.dumps({"client_id": client_id}))

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

                if target and target in clients:
                    # Mensaje privado
                    await clients[target].send(json.dumps(message_data))
                else:
                    # Mensaje público
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
        await asyncio.Future()  # corre para siempre

if __name__ == "__main__":
    asyncio.run(main())
