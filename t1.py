from chunk_and_index import ChunkAndIndex

indexer = ChunkAndIndex()
indexer.load("video_index")  # load FAISS + metadata

query = "Peformance of LEgion go 2?"  # example question
results = indexer.query(query, top_k=3)

for i, r in enumerate(results):
    print(f"Chunk {i}:\n{r['text'][:300]}...\n")
