# chunk_and_index.py
"""
Chunk the transcript, generate embeddings, and store them in a FAISS index.
Works with:
 - extractor.py (your version)
 - local ollama models for LLM later (not needed for this file)
 - LangChain 1.x (not used here because we embed locally)
 - sentence-transformers + faiss-cpu
"""

import os
import re
import pickle
from typing import List, Dict, Tuple

import faiss
from sentence_transformers import SentenceTransformer

INDEX_DIR = "indexes"


class ChunkAndIndex:
    """
    A simple, local FAISS-based embedding indexer.
    Uses sentence-transformers (MiniLM by default).
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.dim = self.model.get_sentence_embedding_dimension()

        # Cosine similarity → normalize + IndexFlatIP
        self.index = faiss.IndexFlatIP(self.dim)
        self.metadatas: List[Dict] = []
    
    def reset(self):
        """Reset the index and metadata (useful for creating a new index)."""
        self.index = faiss.IndexFlatIP(self.dim)
        self.metadatas: List[Dict] = []

    # ---------------------------------------------------------
    # -------------------- TEXT CLEANING -----------------------
    # ---------------------------------------------------------
    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # ---------------------------------------------------------
    # ---------------------  CHUNKING  -------------------------
    # ---------------------------------------------------------
    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 100
    ) -> Tuple[List[str], List[Dict]]:
        """
        Chunk text by word count.
        Returns:
            chunks: list of chunk strings
            metadatas: metadata list for FAISS indexing
        """
        cleaned = self._clean_text(text)
        words = cleaned.split()

        if len(words) == 0:
            return [], []

        chunks = []
        metas = []
        i = 0
        chunk_id = 0

        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)

            chunks.append(chunk_text)
            metas.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "word_start": i,
                "word_end": i + len(chunk_words),
            })

            chunk_id += 1
            i += chunk_size - overlap

        return chunks, metas

    # ---------------------------------------------------------
    # --------------------  EMBEDDING  -------------------------
    # ---------------------------------------------------------
    def add_texts(self, texts: List[str], metadatas: List[Dict]):
        """
        Embed and add text chunks to the FAISS index.
        """
        if len(texts) == 0:
            return

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        # normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        self.index.add(embeddings)
        self.metadatas.extend(metadatas)

    # ---------------------------------------------------------
    # ----------------------  SAVE  ----------------------------
    # ---------------------------------------------------------
    def save(self, prefix: str = "default"):
        """
        Save FAISS index + metadata to ./indexes/
        """
        os.makedirs(INDEX_DIR, exist_ok=True)

        index_path = os.path.join(INDEX_DIR, f"{prefix}.index")
        meta_path = os.path.join(INDEX_DIR, f"{prefix}.meta.pkl")

        faiss.write_index(self.index, index_path)

        with open(meta_path, "wb") as f:
            pickle.dump(self.metadatas, f)

    # ---------------------------------------------------------
    # ----------------------  LOAD  ----------------------------
    # ---------------------------------------------------------
    def load(self, prefix: str = "default"):
        index_path = os.path.join(INDEX_DIR, f"{prefix}.index")
        meta_path = os.path.join(INDEX_DIR, f"{prefix}.meta.pkl")

        if not os.path.exists(index_path):
            raise FileNotFoundError("FAISS index file missing.")
        if not os.path.exists(meta_path):
            raise FileNotFoundError("Metadata file missing.")

        self.index = faiss.read_index(index_path)

        with open(meta_path, "rb") as f:
            self.metadatas = pickle.load(f)

    # ---------------------------------------------------------
    # --------------------  RETRIEVAL  -------------------------
    # ---------------------------------------------------------
    def query(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Return metadata for FAISS top_k results.
        """
        q_emb = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q_emb)

        D, I = self.index.search(q_emb, top_k)

        out = []
        for idx in I[0]:
            if 0 <= idx < len(self.metadatas):
                out.append(self.metadatas[idx])

        return out

    def num_vectors(self) -> int:
        return self.index.ntotal
