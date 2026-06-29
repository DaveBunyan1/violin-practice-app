"use client";

interface Props {
  disabled: boolean;
  loading: boolean;
  onClick: () => void;
}

export default function StartPracticeButton({
  disabled,
  loading,
  onClick,
}: Props) {
  return (
    <button
      disabled={disabled || loading}
      onClick={onClick}
      style={{
        width: "100%",
        padding: "12px",
        backgroundColor: disabled ? "#ccc" : "#0070f3",
        color: "#fff",
        border: "none",
        borderRadius: "4px",
        fontWeight: "bold",
        cursor: disabled ? "not-allowed" : "pointer",
      }}
    >
      {loading ? "Starting..." : "Start Practice"}
    </button>
  );
}
