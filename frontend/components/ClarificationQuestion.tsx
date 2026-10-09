"use client";

import type { ClarificationQuestion as Question } from "@/lib/types";

export function ClarificationQuestion({ question, index, onAnswer }: { question: Question; index: number; onAnswer: (answer: string) => void }) {
  const answered = Boolean(question.answer?.trim());
  return (
    <div className="question-item">
      <span className={`question-number ${answered ? "answered" : ""}`}>{index + 1}</span>
      <div className="question-content">
        <label htmlFor={`answer-${question.id}`}>{question.question}</label>
        <input
          id={`answer-${question.id}`}
          value={question.answer ?? ""}
          onChange={(event) => onAnswer(event.target.value)}
          placeholder="输入你的回答…"
        />
      </div>
      <span className={answered ? "answer-state done" : "answer-state"}>{answered ? "✓" : "○"}</span>
    </div>
  );
}
