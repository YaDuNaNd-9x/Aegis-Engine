
from pydantic import BaseModel


class DocumentResponse(BaseModel):

    filename: str
    pages_extracted: int
    chunks_created: int
    chunks_stored: int
    status: str


class SearchRequest(BaseModel):

    query: str
    top_k: int = 5


class SearchResult(BaseModel):

    text: str
    citation: dict
    relevance_score: float
