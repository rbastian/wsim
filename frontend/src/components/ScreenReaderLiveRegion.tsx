// Screen reader live region component
// Provides an off-screen element for announcing game state changes to screen readers

export function ScreenReaderLiveRegion() {
  return (
    <>
      {/* Live region for polite announcements */}
      <div
        id="sr-live-region"
        role="status"
        aria-live="polite"
        aria-atomic="true"
        style={{
          position: "absolute",
          left: "-10000px",
          width: "1px",
          height: "1px",
          overflow: "hidden",
        }}
      />

      {/* Live region for assertive announcements */}
      <div
        id="sr-alert-region"
        role="alert"
        aria-live="assertive"
        aria-atomic="true"
        style={{
          position: "absolute",
          left: "-10000px",
          width: "1px",
          height: "1px",
          overflow: "hidden",
        }}
      />
    </>
  );
}
