# rag_chain.py

from chunk_and_index import ChunkAndIndex
import ollama  # new API import

class RAGChain:
    def __init__(self, index_name: str = "video_index", model_name: str = "mistral", load_existing: bool = True):
        # Initialize the indexer
        self.indexer = ChunkAndIndex()
        self.index_name = index_name
        self.model_name = model_name
        
        # Optionally load existing index if it exists
        if load_existing:
            try:
                self.indexer.load(index_name)
            except FileNotFoundError:
                # Index doesn't exist yet, will be created when video is processed
                pass

    def retrieve_chunks(self, query: str, top_k: int = 5):
        """Retrieve top-k relevant transcript chunks."""
        return self.indexer.query(query, top_k=top_k)

    def generate_answer(self, query: str, top_k: int = 5):
        """
        Use Ollama to generate an answer based on retrieved chunks.
        Returns the full answer as a string.
        """
        chunks = self.retrieve_chunks(query, top_k)
        context = "\n\n".join([c["text"] for c in chunks])

        messages = [
            {"role": "system", "content": "You are an assistant that answers based on context."},
            {"role": "user", "content": f"{context}\n\nQuestion: {query}"}
        ]

        # Call Ollama and return the response text
        response = ollama.chat(model=self.model_name, messages=messages)
        return response["message"]["content"]
    
    def reload_index(self, index_name: str):
        """Reload the index from disk."""
        self.index_name = index_name
        self.indexer.load(index_name)
    
    def get_index_name(self) -> str:
        """Get current index name."""
        return self.index_name

if __name__ == "__main__":
    rag = RAGChain(index_name="video_index", model_name="mistral")
    user_query = input("Enter question: ")
    answer = rag.generate_answer(user_query)
    print("\n Answer:\n", answer)
