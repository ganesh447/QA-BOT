import { Card } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

interface AnswerDisplayProps {
  answer: string;
  isLoading: boolean;
}

export const AnswerDisplay = ({ answer, isLoading }: AnswerDisplayProps) => {
  if (!answer && !isLoading) {
    return null;
  }

  return (
    <Card className="p-8 rounded-2xl bg-gradient-to-br from-card to-muted/30 border-2 shadow-medium animate-scale-in">
      {isLoading ? (
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
          <p className="text-muted-foreground animate-pulse-glow">Thinking...</p>
        </div>
      ) : (
        <div className="prose prose-lg max-w-none">
          <p className="text-foreground whitespace-pre-wrap leading-relaxed">{answer}</p>
        </div>
      )}
    </Card>
  );
};
