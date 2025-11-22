import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";

interface Video {
  id: string;
  title: string;
  thumbnail: string;
  url: string;
}

interface VideoSuggestionsProps {
  onVideoSelect: (url: string) => void;
  currentVideoUrl?: string;
}

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Helper function to extract video ID from URL
const extractVideoId = (url: string): string | null => {
  const patterns = [
    /[?&]v=([a-zA-Z0-9_-]{11})/,
    /youtu\.be\/([a-zA-Z0-9_-]{11})/,
    /youtube\.com\/embed\/([a-zA-Z0-9_-]{11})/,
  ];
  for (const pattern of patterns) {
    const match = url.match(pattern);
    if (match) return match[1];
  }
  return null;
};

export const VideoSuggestions = ({ onVideoSelect, currentVideoUrl }: VideoSuggestionsProps) => {
  const [startIndex, setStartIndex] = useState(0);
  const [suggestedVideos, setSuggestedVideos] = useState<Video[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const VIDEOS_TO_SHOW = 3;

  // Fetch suggested videos when current video changes
  useEffect(() => {
    const fetchSuggestedVideos = async () => {
      setIsLoading(true);
      try {
        const videoId = currentVideoUrl ? extractVideoId(currentVideoUrl) : null;
        const url = videoId 
          ? `${API_URL}/suggested-videos?video_id=${videoId}`
          : `${API_URL}/suggested-videos`;
        
        const response = await fetch(url);
        
        if (response.ok) {
          const data = await response.json();
          if (data?.videos && Array.isArray(data.videos)) {
            setSuggestedVideos(data.videos);
            setStartIndex(0); // Reset to start when new videos load
          }
        }
      } catch (error) {
        console.error("Error fetching suggested videos:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSuggestedVideos();
  }, [currentVideoUrl]);

  const handlePrevious = () => {
    setStartIndex((prev) => (prev === 0 ? suggestedVideos.length - VIDEOS_TO_SHOW : prev - 1));
  };

  const handleNext = () => {
    setStartIndex((prev) => (prev >= suggestedVideos.length - VIDEOS_TO_SHOW ? 0 : prev + 1));
  };

  const visibleVideos = suggestedVideos.slice(startIndex, startIndex + VIDEOS_TO_SHOW);

  if (isLoading) {
    return (
      <div className="w-full animate-fade-in" style={{ animationDelay: "0.4s" }}>
        <h3 className="text-lg font-semibold mb-4 text-foreground text-center">Suggested Videos</h3>
        <div className="flex items-center justify-center gap-4">
          <div className="flex gap-4 flex-1 justify-center max-w-4xl">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="w-[280px] overflow-hidden rounded-xl shadow-soft bg-card">
                <div className="w-full h-[157px] bg-muted animate-pulse" />
                <div className="p-3">
                  <div className="h-4 bg-muted rounded animate-pulse mb-2" />
                  <div className="h-4 bg-muted rounded animate-pulse w-3/4" />
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (suggestedVideos.length === 0) {
    return (
      <div className="w-full animate-fade-in" style={{ animationDelay: "0.4s" }}>
        <h3 className="text-lg font-semibold mb-4 text-foreground text-center">Suggested Videos</h3>
        <p className="text-center text-muted-foreground">No suggested videos available</p>
      </div>
    );
  }

  return (
    <div className="w-full animate-fade-in" style={{ animationDelay: "0.4s" }}>
      <h3 className="text-lg font-semibold mb-4 text-foreground text-center">Suggested Videos</h3>
      <div className="flex items-center justify-center gap-4">
        {suggestedVideos.length > VIDEOS_TO_SHOW && (
          <Button
            variant="outline"
            size="icon"
            onClick={handlePrevious}
            className="rounded-full h-12 w-12 shadow-soft hover:shadow-medium transition-all"
          >
            <ChevronLeft className="h-6 w-6" />
          </Button>
        )}
        
        <div className="flex gap-4 flex-1 justify-center max-w-4xl">
          {visibleVideos.map((video) => (
            <Card
              key={video.id}
              className="w-[280px] cursor-pointer overflow-hidden rounded-xl shadow-soft hover:shadow-medium transition-all duration-300 hover:scale-105 bg-card"
              onClick={() => onVideoSelect(video.url)}
            >
              <img
                src={video.thumbnail}
                alt={video.title}
                className="w-full h-[157px] object-cover"
                onError={(e) => {
                  // Fallback thumbnail if image fails to load
                  (e.target as HTMLImageElement).src = `https://img.youtube.com/vi/${video.id}/mqdefault.jpg`;
                }}
              />
              <div className="p-3">
                <p className="text-sm font-medium line-clamp-2 text-foreground">
                  {video.title}
                </p>
              </div>
            </Card>
          ))}
        </div>

        {suggestedVideos.length > VIDEOS_TO_SHOW && (
          <Button
            variant="outline"
            size="icon"
            onClick={handleNext}
            className="rounded-full h-12 w-12 shadow-soft hover:shadow-medium transition-all"
          >
            <ChevronRight className="h-6 w-6" />
          </Button>
        )}
      </div>
    </div>
  );
};
