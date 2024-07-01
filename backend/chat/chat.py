import os
import uuid  # type: ignore
import logging

from datetime import datetime, timezone  # type: ignore
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId

from fastapi import Request
from typing import Any, List, Union  # type: ignore

from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from backend.db import get_db
from backend.config import settings
from backend.chat.helpers import exa_search, get_generated_image
from backend.chat.schemas import ChatMessage, ChatRole, ChatMessageOut, AllChatMessage

logger = logging.getLogger(__name__)
GPT4 = "gpt-4o"
GPT3 = "gpt-3.5-turbo-0125"


class Chat:
    def __init__(self, user_id: uuid.UUID):
        self.db = get_db("virtual_assistant")
        self.db.chat_messages.create_index([("user_id", 1)])
        self.user_id = ObjectId(user_id)
        self.messages: List[ChatMessage] = []
        self.tools = [exa_search, get_generated_image]
        self.chat_model = ChatOpenAI(
            openai_api_key=settings.OPENAI_API_KEY, model=GPT3).bind_tools(self.tools)

    async def get_messages(self):
        return (
            await self.db.chat_messages.find({"user_id": self.user_id})
            .sort("created_at", 1)
            .to_list(length=None)
        )

    async def initialize_task_chat(
        self,
        stream: bool = False
    ) -> dict:
        try:
            system_prompt = (
                "You are a conversational AI assistant for Personal Assistance for fitness and health. You are designed to help users with their fitness and health goals. You are capable of providing personalized advice and support on a variety of topics, from nutrition to exercise to wellness. You are also capable of providing information on various fitness and health programs and products. You are designed to be a helpful and supportive resource for users in their fitness and health journey."
            )

            message = await self.add_system_message(
                content=system_prompt,
                commit=True,
            )

            message_history = await self.get_message_history()

            if stream:
                async def response():
                    content = ""
                    async for chunk in self.chat_model.astream(message_history):
                        content += chunk
                        yield chunk
                    message["content"] = content
                    await self.db.chat_messages.update_one({"_id": message["_id"]}, {"$set": {"content": message["content"]}})

                return response()
            else:
                completion = await self.chat_model.ainvoke(message_history)
                message = await self.add_assistant_message(content=completion.content, commit=True)
                logger.info(f"assistent message: {message}")

                return ChatMessageOut.model_validate(
                    {
                        "id": str(message["_id"]),
                        "role": message["role"],
                        "content": message["content"],
                        "created_at": message["created_at"],
                        "updated_at": message["updated_at"],
                    }
                )
        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    async def add_message(
        self,
        role: str,
        content: str,
        commit: bool = False,
    ):
        try:

            message = {
                "user_id": self.user_id,
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }

            result = await self.db.chat_messages.insert_one(message)
            message["_id"] = result.inserted_id

            if commit:
                await self.db.chat_messages.update_one({"_id": message["_id"]}, {"$set": message})

            self.messages.append(
                {
                    "id": str(message["_id"]),
                    "user_id": str(message["user_id"]),
                    "role": message["role"],
                    "content": message["content"],
                    "created_at": message["created_at"],
                    "updated_at": message["updated_at"],
                }
            )
            logger.info(f"self.messages: {self.messages}")
            return message

        except Exception as e:
            logger.error(f"Error adding message: {e}")
            raise e

    async def add_system_message(self, content: str, commit: bool = True):
        return await self.add_message(role="system", content=content, commit=commit)

    async def add_user_message(self, content: str, commit: bool = True):
        return await self.add_message(role="user", content=content, commit=commit)

    async def add_assistant_message(self, content: str, commit: bool = True):
        return await self.add_message(role="assistant", content=content, commit=commit)

    async def get_all_messages_roles(self):
        messages = await self.db.chat_messages.find({
            "user_id": self.user_id,
            "role": {"$in": [ChatRole.ASSISTANT, ChatRole.USER, ChatRole.SYSTEM]}
        }).sort("created_at", 1).to_list(length=None)

        return list(messages) if messages else None

    async def get_message_history(self):
        message_history: List[Union[HumanMessage, AIMessage, SystemMessage]] = []
        messages = await self.get_all_messages_roles()
        for message in messages:
            if message["role"] == "user":
                message_history.append(HumanMessage(content=message["content"]))
            elif message["role"] == "assistant":
                message_history.append(AIMessage(content=message["content"]))
            elif message["role"] == "system":
                message_history.append(SystemMessage(content=message["content"]))
        return message_history

    async def task_chat(
        self,
        user_message: str,
        stream: bool = False,
    ):
        try:
            await self.add_user_message(content=user_message)

            message_history = await self.get_message_history()
            if stream:
                async def response():
                    content = ""
                    async for chunk in self.chat_model.astream(message_history):
                        content += chunk
                        print(f"content: {content}")
                        yield chunk
                    message["content"] = content
                    await self.db.chat_messages.update_one({"_id": message["_id"]}, {"$set": {"content": content}})
                return response()

            message = await self.process_completion(message_history)

            return ChatMessageOut.model_validate(
                {
                    "id": str(message["_id"]),
                    "role": message["role"],
                    "content": message["content"],
                    "created_at": message["created_at"],
                    "updated_at": message["updated_at"],
                }
            )

        except Exception as e:
            logger.error(f"Error: {e}")
            raise

    async def process_completion(
        self,
        message_history: List[Union[HumanMessage, AIMessage, SystemMessage]],
    ):
        try:
            while True:
                completion = await self.chat_model.ainvoke(message_history)
                logger.info(f"completion: {completion}")

                tool_calls = completion.tool_calls
                if not tool_calls:
                    break

                message_history.append(completion)
                for tool_call in tool_calls:
                    if selected_tool := next(
                        (
                            tool
                            for tool in self.tools
                            if tool.name == tool_call.name
                        ),
                        None,
                    ):
                        tool_response = await selected_tool.invoke(tool_call.args)
                        message_history.append(ToolMessage(content=tool_response, tool_name=tool_call.name))
                    else:
                        logger.error(f"Tool {tool_call.name} not found.")
                        break

            return await self.add_assistant_message(content=completion.content, commit=True)
        except Exception as e:
            logger.error(f"Error processing completion: {e}")
            raise

    async def get_all_messages(self):
        messages = await self.db.chat_messages.find({
            "user_id": self.user_id,
            "role": {"$in": [ChatRole.ASSISTANT, ChatRole.USER]}
        }).sort("created_at", 1).to_list(length=None)
        logger.info(f"messages: {messages}")
        return (
            [
                AllChatMessage.model_validate(
                    {
                        "id": str(message["_id"]),
                        "role": message["role"],
                        "message": message["content"],
                        "created_at": message["created_at"],
                        "updated_at": message["updated_at"],
                    }
                )
                for message in messages
            ]
            if messages
            else None
        )