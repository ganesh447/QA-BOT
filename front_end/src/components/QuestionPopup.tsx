import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Sparkles } from "lucide-react";

interface QuestionPopupProps {
  questions: string[];
  onQuestionClick: (question: string) => void;
  isLoading: boolean;
}

export const QuestionPopup = ({
  questions,
  onQuestionClick,
  isLoading,
}: QuestionPopupProps) => {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          className="rounded-2xl h-[80px] w-[80px] shadow-medium hover:shadow-glow transition-all duration-300 hover:scale-105 bg-card"
        >
          <Sparkles className="h-6 w-6 text-accent" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] bg-card">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-accent" />
            Quick Questions
          </DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-1 gap-3 mt-4">
          {questions.map((question, index) => (
            <Button
              key={index}
              onClick={() => onQuestionClick(question)}
              disabled={isLoading}
              variant="outline"
              className="h-auto p-4 text-left justify-start rounded-2xl border-2 hover:border-primary hover:bg-primary/5 transition-all duration-300 hover:scale-[1.02]"
            >
              <span className="text-sm leading-relaxed">{question}</span>
            </Button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
};
