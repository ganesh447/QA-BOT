from extracter1 import fetch_transcript
from chunk_and_index import ChunkAndIndex


def main():
    url = input("Enter YouTube URL: ")

    print("\n Fetching transcript...")
    transcript = fetch_transcript(url)

    print("\n Chunking transcript...")
    indexer = ChunkAndIndex()
    chunks,metas = indexer.chunk_text(transcript, chunk_size=500, overlap=100)
    print(f"Total chunks created: {len(chunks)}")

    # Show preview
    print("\n--- First Chunk Preview ---")
    print(chunks[0][:300] + "...")
    print("\n--- Last Chunk Preview ---")
    print(chunks[-1][:300] + "...")

    print("\n Building vector DB...")
    
    indexer.add_texts(chunks, metas)
    indexer.save("video_index")
    

    print("\n✅ Vector store created successfully!")
    print("Saved in ./db directory")

if __name__ == "__main__":
    main()
