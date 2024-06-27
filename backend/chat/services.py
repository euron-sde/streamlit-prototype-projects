import re
import logging
import requests

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy_file.file import File


logger = logging.getLogger(__name__)


async def save_image_from_url(db: AsyncSession, image_url: str):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching image from URL: {e}")
        raise HTTPException(
            status_code=400, detail=f"Error fetching image from URL: {str(e)}"
        ) from e

    file_content = response.content
    filename = image_url.split("/")[-1]
    content_type = response.headers.get("Content-Type", "application/octet-stream")

    file = File(content=file_content, filename=filename, content_type=content_type)
    chat_image = ChatImage(file=file)

    db.add(chat_image)
    await db.commit()
    await db.refresh(chat_image)

    return chat_image


def contains_any_url(text: str, domain: str) -> bool:
    try:
        pattern = re.compile(r'https?://[^\s\)]+')
        matches = pattern.findall(text)
        return any(domain in url for url in matches)
    except Exception as e:
        logger.error(f"Error checking if URL contains domain: {e}")
        raise e


async def find_image_urls(text: str) -> list:
    try:
        pattern = re.compile(r'!\[([^\]]+)\]\((https?://[^\)]+)\)')
        matches = pattern.findall(text)
        return [match[1] for match in matches]
    except Exception as e:
        logger.error(f"Error finding image URLs: {e}")
        raise e


async def url_mapper(request: Request, db: AsyncSession, image_url: str) -> dict:
    try:
        chat_image = await save_image_from_url(db, image_url)
        chat_image_id = chat_image.file["thumbnail"]["file_id"]
        new_image_url = str(request.url_for("get_chat_image", image_id=chat_image_id))

        return {"id": chat_image.id, "url_mapping": {image_url: new_image_url}}
    except Exception as e:
        logger.error(f"Error mapping URL: {e}")
        raise e


async def map_all_urls(request: Request, db: AsyncSession, text: str) -> dict:
    try:
        image_urls = await find_image_urls(text)
        url_mapping = {}
        chat_image_ids = []

        for url in image_urls:
            result = await url_mapper(request, db, url)
            url_mapping |= result["url_mapping"]
            chat_image_ids.append(result["id"])

        return {
            "url_mapping": url_mapping,
            "chat_image_ids": chat_image_ids
        }
    except Exception as e:
        logger.error(f"Error mapping all URLs: {e}")
        raise e


# async def update_chat_image_chat_id(db: AsyncSession, chat_image_id: int, chat_id: int) -> ChatImage:
#     try:
#         chat_image = await db.get(ChatImage, chat_image_id)
#         if not chat_image:
#             raise HTTPException(
#                 status_code=404, detail=f"ChatImage with id {chat_image_id} not found."
#             )
#         chat_image.chat_id = chat_id
#         await db.commit()
#         await db.refresh(chat_image)
#         return chat_image
#     except Exception as e:
#         logger.error(f"Error updating chat image chat ID: {e}")
#         raise e
