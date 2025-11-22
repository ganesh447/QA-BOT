"""
FastAPI backend server to integrate RAG chain with frontend.
This server exposes an API endpoint that the frontend can call to get answers.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_chain import RAGChain
from extracter1 import fetch_transcript, extract_video_id
from chunk_and_index import ChunkAndIndex
import uvicorn
import os
import httpx
from typing import List, Optional

# Initialize FastAPI app
app = FastAPI(title="Video Q&A API", version="1.0.0")

# Configure CORS to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",  # Vite default port for this project
        "http://localhost:5173",   # Standard Vite port
        "http://localhost:3000",   # Common React port
        "http://127.0.0.1:8080",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG chain (load once at startup)
rag_chain = None
current_video_id = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG chain when server starts."""
    global rag_chain
    try:
        # Try to load existing index, but don't fail if it doesn't exist
        rag_chain = RAGChain(index_name="video_index", model_name="mistral", load_existing=True)
        if rag_chain.indexer.num_vectors() > 0:
            print("✅ RAG chain initialized successfully with existing index")
        else:
            print("⚠️  RAG chain initialized but no index loaded. Process a video first.")
    except FileNotFoundError:
        # Index doesn't exist yet, create empty chain
        rag_chain = RAGChain(index_name="video_index", model_name="mistral", load_existing=False)
        print("⚠️  No existing index found. Process a video to create an index.")
    except Exception as e:
        print(f"❌ Error initializing RAG chain: {e}")
        rag_chain = None

# Request/Response models
class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str

class VideoUrlRequest(BaseModel):
    video_url: str

class VideoProcessResponse(BaseModel):
    success: bool
    message: str
    video_id: str | None = None

class SuggestedVideo(BaseModel):
    id: str
    title: str
    thumbnail: str
    url: str

class SuggestedVideosResponse(BaseModel):
    videos: List[SuggestedVideo]

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Video Q&A API is running",
        "index_loaded": rag_chain is not None
    }

@app.post("/ask-question", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """
    Endpoint to ask questions about the video.
    Accepts a question and returns an answer using the RAG chain.
    """
    if not rag_chain:
        raise HTTPException(
            status_code=503,
            detail="RAG chain not initialized. Please check server logs."
        )
    
    if not request.question or not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    try:
        # Generate answer using RAG chain
        answer = rag_chain.generate_answer(request.question.strip(), top_k=5)
        
        return AnswerResponse(answer=answer)
    
    except Exception as e:
        print(f"Error generating answer: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}"
        )

@app.post("/process-video", response_model=VideoProcessResponse)
async def process_video(request: VideoUrlRequest, background_tasks: BackgroundTasks):
    """
    Process a YouTube video URL: extract transcript, chunk, index, and reload RAG chain.
    This updates the RAG pipeline to use the new video's transcript.
    """
    global rag_chain, current_video_id
    
    if not request.video_url or not request.video_url.strip():
        raise HTTPException(
            status_code=400,
            detail="Video URL cannot be empty"
        )
    
    video_url = request.video_url.strip()
    
    try:
        # Extract video ID
        video_id = extract_video_id(video_url)
        
        # Check if this video is already indexed
        index_name = f"video_{video_id}"
        index_path = os.path.join("indexes", f"{index_name}.index")
        
        if os.path.exists(index_path):
            # Index already exists, just reload it
            print(f"📦 Loading existing index for video: {video_id}")
            if not rag_chain:
                rag_chain = RAGChain(index_name=index_name, model_name="mistral", load_existing=False)
            rag_chain.reload_index(index_name)
            current_video_id = video_id
            
            return VideoProcessResponse(
                success=True,
                message=f"Video {video_id} loaded from existing index",
                video_id=video_id
            )
        
        # Fetch transcript
        print(f"📥 Fetching transcript for video: {video_id}")
        transcript = fetch_transcript(video_url)
        
        if not transcript or len(transcript.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Transcript is empty or could not be fetched"
            )
        
        # Chunk and index
        print(f"🔪 Chunking transcript for video: {video_id}")
        indexer = ChunkAndIndex()
        indexer.reset()  # Start with fresh index
        
        chunks, metas = indexer.chunk_text(transcript, chunk_size=500, overlap=100)
        print(f"✅ Created {len(chunks)} chunks")
        
        # Add video_id to metadata
        for meta in metas:
            meta["video_id"] = video_id
            meta["video_url"] = video_url
        
        # Embed and add to index
        print(f"🔍 Creating embeddings for video: {video_id}")
        indexer.add_texts(chunks, metas)
        
        # Save index
        print(f"💾 Saving index for video: {video_id}")
        indexer.save(index_name)
        
        # Reload RAG chain with new index
        if not rag_chain:
            rag_chain = RAGChain(index_name=index_name, model_name="mistral", load_existing=False)
        rag_chain.reload_index(index_name)
        current_video_id = video_id
        
        print(f"✅ Successfully processed video: {video_id}")
        
        return VideoProcessResponse(
            success=True,
            message=f"Video {video_id} processed successfully. {len(chunks)} chunks indexed.",
            video_id=video_id
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid YouTube URL: {str(e)}"
        )
    except Exception as e:
        print(f"Error processing video: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing video: {str(e)}"
        )

@app.get("/suggested-videos", response_model=SuggestedVideosResponse)
async def get_suggested_videos(video_id: Optional[str] = None):
    """
    Get suggested/recommended videos.
    If video_id is provided, returns videos related to that video.
    Otherwise, returns general suggested videos.
    """
    try:
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        
        if youtube_api_key and video_id:
            # Use YouTube Data API to get related videos
            try:
                async with httpx.AsyncClient() as client:
                    # First, get video details to extract search terms
                    video_response = await client.get(
                        f"https://www.googleapis.com/youtube/v3/videos",
                        params={
                            "key": youtube_api_key,
                            "id": video_id,
                            "part": "snippet"
                        },
                        timeout=10.0
                    )
                    
                    if video_response.status_code == 200:
                        video_data = video_response.json()
                        if video_data.get("items"):
                            snippet = video_data["items"][0]["snippet"]
                            title = snippet.get("title", "")
                            channel_id = snippet.get("channelId", "")
                            
                            # Search for related videos using title keywords
                            search_query = " ".join(title.split()[:5])  # Use first 5 words
                            
                            search_response = await client.get(
                                f"https://www.googleapis.com/youtube/v3/search",
                                params={
                                    "key": youtube_api_key,
                                    "q": search_query,
                                    "type": "video",
                                    "maxResults": 10,
                                    "part": "snippet",
                                    "order": "relevance"
                                },
                                timeout=10.0
                            )
                            
                            if search_response.status_code == 200:
                                search_data = search_response.json()
                                videos = []
                                
                                for item in search_data.get("items", []):
                                    if item["id"]["kind"] == "youtube#video":
                                        video_id_result = item["id"]["videoId"]
                                        # Skip the current video
                                        if video_id_result == video_id:
                                            continue
                                        
                                        snippet = item["snippet"]
                                        videos.append(SuggestedVideo(
                                            id=video_id_result,
                                            title=snippet.get("title", "Untitled"),
                                            thumbnail=snippet.get("thumbnails", {}).get("medium", {}).get("url", 
                                                f"https://img.youtube.com/vi/{video_id_result}/mqdefault.jpg"),
                                            url=f"https://www.youtube.com/watch?v={video_id_result}"
                                        ))
                                        
                                        if len(videos) >= 5:  # Limit to 5 videos
                                            break
                                
                                if videos:
                                    return SuggestedVideosResponse(videos=videos)
            except Exception as e:
                print(f"Error fetching from YouTube API: {e}")
                # Fall through to default suggestions
        
        # Fallback: Return curated suggestions or videos from same channel
        # You can customize this list based on your needs
        default_videos = [
            SuggestedVideo(
                id="dQw4w9WgXcQ",
                title="Introduction to Video Learning",
                thumbnail="https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
                url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            ),
            SuggestedVideo(
                id="jNQXAC9IVRw",
                title="Advanced Learning Techniques",
                thumbnail="https://img.youtube.com/vi/jNQXAC9IVRw/mqdefault.jpg",
                url="https://www.youtube.com/watch?v=jNQXAC9IVRw"
            ),
            SuggestedVideo(
                id="kJQP7kiw5Fk",
                title="Interactive Learning Guide",
                thumbnail="https://img.youtube.com/vi/kJQP7kiw5Fk/mqdefault.jpg",
                url="https://www.youtube.com/watch?v=kJQP7kiw5Fk"
            ),
            SuggestedVideo(
                id="9bZkp7q19f0",
                title="Educational Content Series",
                thumbnail="https://img.youtube.com/vi/9bZkp7q19f0/mqdefault.jpg",
                url="https://www.youtube.com/watch?v=9bZkp7q19f0"
            ),
            SuggestedVideo(
                id="L_jWHffIx5E",
                title="Mastering Video Analysis",
                thumbnail="https://img.youtube.com/vi/L_jWHffIx5E/mqdefault.jpg",
                url="https://www.youtube.com/watch?v=L_jWHffIx5E"
            ),
        ]
        
        return SuggestedVideosResponse(videos=default_videos)
    
    except Exception as e:
        print(f"Error getting suggested videos: {e}")
        # Return empty list on error
        return SuggestedVideosResponse(videos=[])

@app.get("/health")
async def health_check():
    """Health check endpoint with more details."""
    return {
        "status": "healthy" if rag_chain else "unhealthy",
        "rag_chain_loaded": rag_chain is not None,
        "current_video_id": current_video_id,
        "index_name": rag_chain.get_index_name() if rag_chain else None,
        "num_chunks": rag_chain.indexer.num_vectors() if rag_chain else 0
    }

if __name__ == "__main__":
    # Run the server
    # Default: http://localhost:8000
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )

