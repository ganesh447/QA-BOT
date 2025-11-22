import { AspectRatio } from "@/components/ui/aspect-ratio";

interface YouTubePlayerProps {
  videoUrl: string;
}

export const YouTubePlayer = ({ videoUrl }: YouTubePlayerProps) => {
  const getVideoId = (url: string) => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return match && match[2].length === 11 ? match[2] : null;
  };

  const videoId = getVideoId(videoUrl);

  if (!videoId) {
    return (
      <div className="w-full rounded-2xl bg-muted p-8 text-center">
        <p className="text-muted-foreground">Please provide a valid YouTube URL</p>
      </div>
    );
  }

  return (
    <div className="w-full rounded-2xl overflow-hidden shadow-large animate-fade-in">
      <AspectRatio ratio={16 / 9}>
        <iframe
          src={`https://www.youtube.com/embed/${videoId}`}
          title="YouTube video player"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
          allowFullScreen
          className="w-full h-full"
        />
      </AspectRatio>
    </div>
  );
};
