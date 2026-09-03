function Navigation({ currentView, onChange }) {
  return (
    <nav>
      <button onClick={() => onChange("worker")}>
        Worker Dashboard
      </button>

      <button onClick={() => onChange("partner")}>
        Partner Dashboard
      </button>

      <button onClick={() => onChange("widget")}>
        FlowShield Widget
      </button>
    </nav>
  );
}

export default Navigation;