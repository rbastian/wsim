// Skip links component for keyboard navigation
// Provides quick navigation to main content areas

export function SkipLinks() {
  return (
    <div
      className="skip-links"
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        zIndex: 10000,
      }}
    >
      <a
        href="#main-content"
        className="skip-link"
        style={{
          position: "absolute",
          left: "-10000px",
          top: "auto",
          width: "1px",
          height: "1px",
          overflow: "hidden",
          padding: "12px 24px",
          background: "#2c1810",
          color: "#f2ebdc",
          fontFamily: "'Cinzel', serif",
          fontSize: "16px",
          fontWeight: 600,
          textDecoration: "none",
          borderRadius: "4px",
          zIndex: 10000,
        }}
        onFocus={(e) => {
          e.currentTarget.style.left = "10px";
          e.currentTarget.style.top = "10px";
          e.currentTarget.style.width = "auto";
          e.currentTarget.style.height = "auto";
          e.currentTarget.style.overflow = "visible";
        }}
        onBlur={(e) => {
          e.currentTarget.style.left = "-10000px";
          e.currentTarget.style.top = "auto";
          e.currentTarget.style.width = "1px";
          e.currentTarget.style.height = "1px";
          e.currentTarget.style.overflow = "hidden";
        }}
      >
        Skip to main content
      </a>
      <a
        href="#ship-actions"
        className="skip-link"
        style={{
          position: "absolute",
          left: "-10000px",
          top: "auto",
          width: "1px",
          height: "1px",
          overflow: "hidden",
          padding: "12px 24px",
          background: "#2c1810",
          color: "#f2ebdc",
          fontFamily: "'Cinzel', serif",
          fontSize: "16px",
          fontWeight: 600,
          textDecoration: "none",
          borderRadius: "4px",
          zIndex: 10000,
        }}
        onFocus={(e) => {
          e.currentTarget.style.left = "10px";
          e.currentTarget.style.top = "60px";
          e.currentTarget.style.width = "auto";
          e.currentTarget.style.height = "auto";
          e.currentTarget.style.overflow = "visible";
        }}
        onBlur={(e) => {
          e.currentTarget.style.left = "-10000px";
          e.currentTarget.style.top = "auto";
          e.currentTarget.style.width = "1px";
          e.currentTarget.style.height = "1px";
          e.currentTarget.style.overflow = "hidden";
        }}
      >
        Skip to ship actions
      </a>
    </div>
  );
}
