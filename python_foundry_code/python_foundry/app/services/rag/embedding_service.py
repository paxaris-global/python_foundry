import hashlib
import struct

from openai import OpenAI

from app.core.config import get_settings


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None
        self.dim = 1536

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if self.client:
            response = self.client.embeddings.create(model=self.settings.embedding_model, input=texts)
            return [item.embedding for item in response.data]
        return [self._local_embed(text) for text in texts]

    def embed_query(self, query: str) -> list[float]:
        return self.embed_texts([query])[0]

    def _local_embed(self, text: str) -> list[float]:
        digest = hashlib.sha512(text.encode("utf-8")).digest()
        numbers = list(struct.unpack("!64B", digest))
        vec = []
        for i in range(self.dim):
            val = numbers[i % len(numbers)] / 255.0
            centered = (val * 2.0) - 1.0
            vec.append(centered)
        return vec
