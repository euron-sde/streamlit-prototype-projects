import asyncio
import motor.motor_asyncio

from backend.config import settings

# Create a Motor client
client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI)

# Access the database
db = client.my_database

# Access the collection
collection = db.my_collection


async def insert_document(document):
    result = await collection.insert_one(document)
    return result.inserted_id

# Example usage


async def main():
    document = {"name": "John Doe", "email": "john.doe@example.com"}
    inserted_id = await insert_document(document)
    print(f"Inserted document with ID: {inserted_id}")

if __name__ == "__main__":
    asyncio.run(main())
