import numpy as np

# The bge model card recommends this prefix for short retrieval queries.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class Embedder:
    def __init__(self, name: str, device: str | None = None):
        from sentence_transformers import SentenceTransformer

        self.name = name
        self.model = SentenceTransformer(name, device=device)
        get_dim = getattr(self.model, "get_embedding_dimension", None) or \
            self.model.get_sentence_embedding_dimension  # older sentence-transformers
        self.dim = get_dim()
        tok = self.model.tokenizer
        self.count_tokens = lambda s: len(tok.encode(s, add_special_tokens=False))

    def encode(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        # normalised, so cosine == dot product
        return self.model.encode(
            texts, batch_size=batch_size, normalize_embeddings=True, convert_to_numpy=True
        )

    def encode_query(self, query: str, prefix: bool = True) -> np.ndarray:
        return self.encode([(QUERY_PREFIX if prefix else "") + query])[0]
