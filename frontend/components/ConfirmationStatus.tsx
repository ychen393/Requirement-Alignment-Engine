import type { ConfirmationStatus as Status } from "@/lib/types";

export function ConfirmationStatus({ status }: { status: Status }) {
  const confirmed = status === "USER_CONFIRMED";
  return (
    <span className={`confirmation ${confirmed ? "confirmed" : "suggested"}`}>
      <span>{confirmed ? "✓" : "AI"}</span>
      {confirmed ? "用户已确认" : "AI 建议"}
    </span>
  );
}
