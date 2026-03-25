from app.services.rag.chroma_service import ChromaService
from app.services.rag.embedding_service import EmbeddingService


class RAGRetriever:
    def __init__(self) -> None:
        self.chroma = ChromaService()
        self.embedding = EmbeddingService()

    def search(self, query: str, top_k: int = 5, min_similarity: float = 0.0) -> list[dict]:
        collection = self.chroma.get_collection()
        embedding = self.embedding.embed_query(query)
        result = collection.query(query_embeddings=[embedding], n_results=top_k)

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        output = []
        for idx, content in enumerate(documents):
            distance = distances[idx] if idx < len(distances) else None
            similarity = (1.0 / (1.0 + float(distance))) if distance is not None else None
            if similarity is not None and similarity < min_similarity:
                continue
            output.append(
                {
                    "content": content,
                    "metadata": metadatas[idx] if idx < len(metadatas) else {},
                    "score": similarity,
                }
            )
        return output
