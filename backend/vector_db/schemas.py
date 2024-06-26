from pydantic import BaseModel
from typing import List, Dict, Any, Union  # type: ignore


class Document(BaseModel):
    id: str
    page_content: Union[Dict[str, Any], str]
    embedding: List[float]
