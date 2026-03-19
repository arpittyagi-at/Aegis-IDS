import asyncio
import websockets

async def main():
    uri = "ws://localhost:8000/stream"
    async with websockets.connect(uri) as websocket:
        print("connected")
        msg = await websocket.recv()
        print(msg)

if __name__ == "__main__":
    asyncio.run(main())
