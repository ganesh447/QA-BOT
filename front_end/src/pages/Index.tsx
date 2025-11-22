import { useState } from "react";
import { YouTubePlayer } from "@/components/YouTubePlayer";
import { QuestionInput } from "@/components/QuestionInput";
import { AnswerDisplay } from "@/components/AnswerDisplay";
import { QuestionPopup } from "@/components/QuestionPopup";
import { VideoSuggestions } from "@/components/VideoSuggestions";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { Github, Play, Link, Loader2 } from "lucide-react";
import aiIcon from "@/assets/ai-icon.png";

const DEFAULT_VIDEO_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ";

// API endpoint for the FastAPI backend
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const PREMADE_QUESTIONS = [
  "Can you summarize the main points of this video?",
  "What are the key takeaways I should remember?",
  "Are there any actionable steps mentioned in the video?",
  "What's the most interesting part of this content?",
];

const Index = () => {
  const [answer, setAnswer] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [videoUrl, setVideoUrl] = useState(DEFAULT_VIDEO_URL);
  const [urlInput, setUrlInput] = useState("");
  const { toast } = useToast();

  // Function to validate YouTube URL
  const isValidYouTubeUrl = (url: string): boolean => {
    const patterns = [
      /^https?:\/\/(www\.)?(youtube\.com|youtu\.be)\/.+/,
      /^https?:\/\/youtube\.com\/embed\/.+/,
    ];
    return patterns.some(pattern => pattern.test(url));
  };

  // Function to handle URL change
  const handleUrlChange = async () => {
    const trimmedUrl = urlInput.trim();
    
    if (!trimmedUrl) {
      toast({
        title: "Error",
        description: "Please enter a YouTube URL",
        variant: "destructive",
      });
      return;
    }

    if (!isValidYouTubeUrl(trimmedUrl)) {
      toast({
        title: "Invalid URL",
        description: "Please enter a valid YouTube URL",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    setAnswer("");
    
    try {
      // Call backend to process the video (extract transcript, index, and update RAG pipeline)
      const response = await fetch(`${API_URL}/process-video`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ video_url: trimmedUrl }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data?.success) {
        // Update video URL in frontend and clear previous answer
        setVideoUrl(trimmedUrl);
        setUrlInput("");
        
        toast({
          title: "Video processed successfully",
          description: data.message || "Video transcript indexed and ready for questions",
        });
      } else {
        throw new Error(data.message || "Failed to process video");
      }
    } catch (error) {
      console.error("Error processing video:", error);
      toast({
        title: "Error processing video",
        description: error instanceof Error ? error.message : "Failed to process video. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key in URL input
  const handleUrlKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleUrlChange();
    }
  };

  const handleQuestionSubmit = async (question: string) => {
    setIsLoading(true);
    setAnswer("");

    try {
      const response = await fetch(`${API_URL}/ask-question`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data?.answer) {
        setAnswer(data.answer);
      } else {
        throw new Error("No answer received");
      }
    } catch (error) {
      console.error("Error submitting question:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to get an answer. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm fixed top-0 left-0 right-0 z-50 shadow-soft">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <img src={aiIcon} alt="Holzland Beckers' AI" className="w-12 h-12 rounded-xl shadow-md" />
              <div>
                <h1 className="text-2xl md:text-3xl font-bold text-gradient">
                  Holzland Beckers' AI
                </h1>
                <p className="text-muted-foreground text-sm mt-1">
                  Watch, ask, and learn interactively
                </p>
              </div>
            </div>
            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-7xl mt-28">
        <div className="space-y-8">
          {/* URL Input Section */}
          <section className="space-y-2">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Link className="w-4 h-4" />
              <span>Enter YouTube Video URL</span>
            </div>
            <div className="flex gap-3">
              <Input
                type="text"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyPress={handleUrlKeyPress}
                placeholder="https://www.youtube.com/watch?v=..."
                className="flex-1 rounded-xl border-2 focus:border-primary transition-all duration-300"
              />
              <Button
                onClick={handleUrlChange}
                disabled={isLoading || !urlInput.trim()}
                className="rounded-xl px-6 bg-gradient-to-r from-primary to-accent hover:shadow-glow transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Load Video
                  </>
                )}
              </Button>
            </div>
          </section>

          {/* Video and Chat Section - Side by Side */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Video Player */}
            <div className="space-y-4">
              <YouTubePlayer videoUrl={videoUrl} />
            </div>

            {/* Chat Section */}
            <div className="space-y-4 flex flex-col">
              {/* Answer Display */}
              {(answer || isLoading) && (
                <div className="flex-1">
                  <AnswerDisplay answer={answer} isLoading={isLoading} />
                </div>
              )}

              {/* Question Input with Popup */}
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <QuestionInput onSubmit={handleQuestionSubmit} isLoading={isLoading} />
                </div>
                <QuestionPopup
                  questions={PREMADE_QUESTIONS}
                  onQuestionClick={handleQuestionSubmit}
                  isLoading={isLoading}
                />
              </div>
            </div>
          </section>

          {/* Video Suggestions */}
          <section>
            <VideoSuggestions onVideoSelect={setVideoUrl} currentVideoUrl={videoUrl} />
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-16 py-8 bg-card/30">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p className="mb-4">Powered by AI • Made with ❤️</p>
          <a 
            href="#" 
            target="_blank" 
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-foreground hover:text-primary transition-colors"
          >
            <Github className="w-5 h-5" />
            <span>View on GitHub</span>
          </a>
        </div>
      </footer>
    </div>
  );
};

export default Index;
