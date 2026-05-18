export default function App() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        flexDirection: "column",
        gap: "12px",
      }}
    >
      <h1
        style={{
          fontFamily: "var(--font-display)",
          fontSize: "4rem",
          letterSpacing: "0.05em",
          color: "var(--orange)",
        }}
      >
        MANIFEST
      </h1>
      <p style={{ color: "var(--text-secondary)", fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
        ELD Trip Planner — scaffold ready
      </p>
    </div>
  );
}
