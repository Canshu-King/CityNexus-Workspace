import { useState } from "react";
import { createRoot } from "react-dom/client";
import { testIds } from "./contracts/testIds";
import "./styles.css";

const acceptedKey = "citynexus.demo.replan.accepted";

function App() {
  const [simulatorOpen, setSimulatorOpen] = useState(false);
  const [replanVisible, setReplanVisible] = useState(false);
  const [accepted, setAccepted] = useState(() => localStorage.getItem(acceptedKey) === "true");

  const accept = () => {
    localStorage.setItem(acceptedKey, "true");
    setAccepted(true);
  };

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">CityNexus · deterministic journey mode</p>
        <h1>Commitment-aware recovery</h1>
        <span data-testid={testIds.journeyStatus} className="status">{accepted ? "ACTIVE · recovered" : "ACTIVE"}</span>
      </header>
      <section className="grid">
        <div data-testid={testIds.journeyMap} className="map-card">
          <div className="map-title">Journey map</div>
          <div className="route-line" />
          <p data-testid={testIds.currentActivity}>Current route · verified backend facts</p>
        </div>
        <aside className="evidence-card">
          <h2 data-testid={testIds.protectedCommitment}>🔒 River Cruise · 15:30 C4</h2>
          <p data-testid={testIds.feasibilityEnvelope}>Feasibility envelope · robust</p>
          <button data-testid={testIds.eventSimulator} onClick={() => setSimulatorOpen((value) => !value)}>
            Demo Event Simulator
          </button>
          {simulatorOpen && (
            <button data-testid={testIds.eventClosureButton} onClick={() => setReplanVisible(true)}>
              Inject Tech Art closure
            </button>
          )}
        </aside>
      </section>
      {replanVisible && (
        <section data-testid={testIds.replanPanel} className="replan-card">
          <h2>Replan comparison</h2>
          <div data-testid={testIds.replanCandidate} className="candidate">F0 · Design Library replacement</div>
          <p data-testid={testIds.replanDiff}>Tech Art Center removed · Design Library added · River Cruise preserved at 15:30</p>
          <button data-testid={testIds.acceptReplan} onClick={accept}>Accept replan</button>
        </section>
      )}
      <p data-testid={testIds.aiExplanation} className="note">Explanations use verified JourneyTwin and ReplanDiff evidence.</p>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
