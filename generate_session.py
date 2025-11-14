import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

async def main():
    print("=== Telethon String Session Generator ===")
    api_id = input("Enter your API ID: ")
    api_hash = input("Enter your API Hash: ")
    
    client = TelegramClient(StringSession(), api_id, api_hash)
    await client.start()
    
    print("\n=== YOUR STRING SESSION ===")
    print(client.session.save())
    print("\n=== Save this string in your .env file as STRING_SESSION ===")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
