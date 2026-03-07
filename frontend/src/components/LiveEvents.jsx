function classifyEvent(text) {
  const t = text.toLowerCase();
  if (t.includes("fail") || t.includes("error")) return "error";
  if (t.includes("payment") || t.includes("paid") || t.includes("completed")) return "success";
  if (t.includes("start") || t.includes("accept") || t.includes("ongoing")) return "warning";
  if (t.includes("created") || t.includes("offered") || t.includes("assigned")) return "info";
  return "neutral";
}

function formatTime(date) {
  return date.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function LiveEvents({ events, onClear }) {
  return (
    <div className="card" style={{ gridRow: "span 2" }}>
      <div className="card-header" style={{ justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div className="card-icon blue">📡</div>
          <h3 className="card-title">Live Events</h3>
        </div>
        {events.length > 0 && (
          <button className="btn-ghost" onClick={onClear}>Clear</button>
        )}
      </div>

      <div className="events-container">
        {events.length === 0 ? (
          <div className="events-empty">Waiting for events...</div>
        ) : (
          events.map((evt, i) => {
            const text = typeof evt === "string" ? evt : evt.text;
            const time = typeof evt === "string" ? null : evt.time;
            const type = classifyEvent(text);
            return (
              <div key={i} className={`event-item ${type}`}>
                <span className="event-text">{text}</span>
                {time && <span className="event-time">{formatTime(time)}</span>}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
