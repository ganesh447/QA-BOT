import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";

interface PreMadeQuestionsProps {
  questions: string[];
  onQuestionClick: (question: string) => void;
  isLoading: boolean;
}

export const PreMadeQuestions = ({
  questions,
  onQuestionClick,
  isLoading,
}: PreMadeQuestionsProps) => {
  return (
    <div className="space-y-4 animate-fade-in" style={{ animationDelay: "0.3s" }}>
      <div className="flex items-center gap-2 text-foreground">
        <Sparkles className="h-5 w-5 text-accent" />
        <h3 className="text-lg font-semibold">Quick Questions</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {questions.map((question, index) => (
          <Button
            key={index}
            onClick={() => onQuestionClick(question)}
            disabled={isLoading}
            variant="outline"
            className="h-auto p-4 text-left justify-start rounded-2xl border-2 hover:border-primary hover:bg-primary/5 transition-all duration-300 hover:scale-[1.02] hover:shadow-soft bg-card"
            style={{ animationDelay: `${0.4 + index * 0.1}s` }}
          >
            <span className="text-sm leading-relaxed">{question}</span>
          </Button>
        ))}
      </div>
    </div>
  );
};
