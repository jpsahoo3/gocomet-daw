export default function LiveEvents({ events }) {
  return (
    <div className="card">
      <h3>📡 Live Events</h3>
      <div className="events">
        {events.map((e, i) => (
          <div key={i} className="event">{e}</div>
        ))}
      </div>
    </div>
  );
}
