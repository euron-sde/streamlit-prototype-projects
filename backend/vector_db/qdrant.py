import os
import logging
from typing import List, Dict, Union  # type: ignore

from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from qdrant_client import QdrantClient, models
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from backend.vector_db.schemas import Document  # type: ignore

load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

# TODO: make qdrant manager function asynchronously


class QdrantManager:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.embedder = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def delete_collection(self, collection_name: str) -> bool:
        try:
            self.client.delete_collection(collection_name=collection_name)
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            return False

    def create_collection(self, collection_name: str, distance_strategy: str = "COSINE", hnsw_config: dict = None) -> bool:
        try:
            if not self.client.collection_exists(collection_name):
                vectors_config = models.VectorParams(
                    size=1536,
                    distance=getattr(models.Distance, distance_strategy),
                    hnsw_config=models.HnswConfigDiff(**hnsw_config) if hnsw_config else models.HnswConfigDiff(
                        m=16,
                        ef_construct=100,
                        full_scan_threshold=10000,
                        max_indexing_threads=0,
                        on_disk=False
                    )
                )
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=vectors_config
                )
                return True
            else:
                logger.debug(f"Collection {collection_name} already exists.")
                return False
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False

    def update_collection(self, collection_name: str) -> bool:
        try:
            if self.client.collection_exists(collection_name):
                self.client.update_collection(
                    collection_name=collection_name,
                    optimizer_config=models.OptimizersConfigDiff(
                        indexing_threshold=10000
                    ),
                    hnsw_config=models.HNSWConfig(
                        m=16, ef_construction=128, max_elements=10000
                    )
                )
                return True
            else:
                logger.debug(f"Collection {collection_name} does not exist.")
                return False
        except Exception as e:
            logger.error(f"Error updating collection: {e}")
            return False

    def add_document_to_collection(self, collection_name: str, documents: Union[Document, List[Document]]) -> bool:
        try:
            if isinstance(documents, list):
                points = [
                    models.PointStruct(
                        id=str(document.id),
                        vector=document.embedding,
                        payload=document.page_content,
                    )
                    for document in documents
                ]
                self.client.upsert(
                    collection_name=collection_name, points=points)
                return True
            else:
                logger.error(
                    "Documents should be a list of Document instances.")
                return False
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

    def search_documents(self, collection_name: str, query: str, k: int = 5) -> List[Union[SystemMessage, AIMessage, HumanMessage]]:
        try:
            response = self.client.search(
                collection_name=collection_name, query_vector=self.create_embedding(query), limit=k
            )
            data = [point.payload for point in response]
            # logger.info(f"Search documents: {data}")
            return self.sort_messages(data)
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def create_point(self, data: List[Dict[str, Union[str, int]]]) -> Union[List[Document], bool]:
        try:
            return [
                Document(
                    id=item["id"],
                    page_content={
                        "content": item["content"],
                        "role": item["role"],
                        "created_at": item["created_at"]
                    },
                    embedding=self.create_embedding(item["content"]),
                )
                for item in data if item["content"] != ""
            ]
        except Exception as e:
            logger.error(f"Error creating point: {e}")
            return False

    def create_embedding(self, query: str) -> List[float]:
        try:
            return self.embedder.embeddings.create(
                input=query, model="text-embedding-3-small"
            ).data[0].embedding
        except Exception as e:
            logger.error(f"Error creating embedding: {e}")
            return []

    def sort_messages(self, messages: List[Dict[str, Union[str, int]]]) -> List[Union[SystemMessage, AIMessage, HumanMessage]]:
        # Sort messages by 'created_at'
        sorted_messages = sorted(messages, key=lambda x: x['created_at'])
        # logger.info(f"Sorted messages: {sorted_messages}")
        result_messages = []
        # Assign messages to respective roles and append them to the result list
        for message in sorted_messages:
            if message['role'] == 'SYSTEM':
                result_messages.append(
                    SystemMessage(content=message['content']))
            elif message['role'] == 'ASSISTANT':
                result_messages.append(AIMessage(content=message['content']))
            elif message['role'] == 'USER':
                result_messages.append(
                    HumanMessage(content=message['content']))
            else:
                continue  # Skip if the role is not recognized
        return result_messages
