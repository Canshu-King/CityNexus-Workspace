import { useState } from "react";
import { createRoot } from "react-dom/client";
import { testIds } from "./contracts/testIds";
import "./styles.css";

const acceptedKey = "citynexus.demo.replan.accepted";

const journeyFacts = {
  currentActivity: "Tech Art Center",
  nextActivity: "River Cruise",
  budgetRemaining: "¥5,600",
  nextCommitmentBuffer: "55 min safe buffer",
  opportunityWindow: "13:20–14:35 · 75 min available",
  upcomingCommitments: [
    "River Cruise · 15:30 · C4 Anchored",
    "Dinner reservation · 18:00 · C2 Scheduled",
  ],
};

const candidateFamilies = [
  "F0_SAME_SLOT_REPLACEMENT",
  "F3_OPPORTUNITY_WINDOW",
  "F1_OPTIONAL_REMOVAL",
];

function App() {
  const [simulatorOpen, setSimulatorOpen] = useState(false);
  const [replanVisible, setReplanVisible] = useState(false);
  const [replanRejected, setReplanRejected] = useState(false);
  const [accepted, setAccepted] = useState(() => localStorage.getItem(acceptedKey) === "true");

  const accept = () => {
    localStorage.setItem(acceptedKey, "true");
    setAccepted(true);
  };

  const reject = () => {
    localStorage.removeItem(acceptedKey);
    setReplanRejected(true);
    setReplanVisible(false);
  };

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">CityNexus · deterministic journey mode</p>
        <h1>Commitment-aware recovery</h1>
        <span data-testid={testIds.journeyStatus} className="status">{accepted ? "ACTIVE · recovered" : "ACTIVE"}</span>
        {replanRejected && <span className="status muted-status"> · proposal rejected</span>}
      </header>
      <section className="grid">
        <div data-testid={testIds.journeyMap} className="map-card">
          <div className="map-title">Journey map · MapLibre-ready evidence surface</div>
          <div className="map-canvas" aria-label="Journey map markers and route">
            <span data-testid={testIds.mapCurrentMarker} className="map-marker current-marker">Current</span>
            <span data-testid={testIds.mapEventMarker} className="map-marker event-marker">Closure</span>
            <span data-testid={testIds.mapProtectedMarker} className="map-marker protected-marker">C4</span>
            <div data-testid={testIds.mapOldRoute} className="route-line old-route" />
            {replanVisible && <div data-testid={testIds.mapNewRoute} className="route-line new-route" />}
          </div>
          <p data-testid={testIds.currentActivity}>Current: {journeyFacts.currentActivity}</p>
          <p>Next: {journeyFacts.nextActivity}</p>
        </div>
        <aside className="evidence-card">
          <h2 data-testid={testIds.protectedCommitment}>🔒 River Cruise · 15:30 C4</h2>
          <p data-testid={testIds.nextCommitment}>Next commitment · {journeyFacts.nextActivity}</p>
          <p data-testid={testIds.nextCommitmentBuffer}>{journeyFacts.nextCommitmentBuffer}</p>
          <p data-testid={testIds.budgetRemaining}>Budget remaining · {journeyFacts.budgetRemaining}</p>
          <p data-testid={testIds.opportunityWindow}>Opportunity window · {journeyFacts.opportunityWindow}</p>
          <p data-testid={testIds.feasibilityEnvelope}>Feasibility envelope · robust · hard constraints pass</p>
          <p data-testid={testIds.providerDegradation} className="provider-ready">Provider status · ready (no degradation)</p>
          <div data-testid={testIds.upcomingCommitments} className="upcoming-list">
            <strong>Upcoming protected commitments</strong>
            {journeyFacts.upcomingCommitments.map((item) => <span key={item}>{item}</span>)}
          </div>
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
      <section data-testid={testIds.journeyTimeline} className="timeline-card">
        <strong>Journey timeline</strong>
        <div className="timeline-track">
          <span className="timeline-item complete">09:00 · Breakfast</span>
          <span className="timeline-item active">13:00 · {journeyFacts.currentActivity}</span>
          <span className="timeline-item protected">15:30 · {journeyFacts.nextActivity} · C4</span>
        </div>
      </section>
      {replanVisible && (
        <section data-testid={testIds.replanPanel} className="replan-card">
          <h2>Replan comparison</h2>
          <div data-testid={testIds.replanCandidate} className="candidate">F0 · Design Library replacement · verified feasible</div>
          <div data-testid={testIds.replanCandidateFamilies} className="candidate-families">
            {candidateFamilies.map((family) => <span key={family}>{family}</span>)}
          </div>
          <p data-testid={testIds.replanScore}>Utility score · 0.84 · commitment preservation 1.0 · stability 0.9</p>
          <p data-testid={testIds.replanEvidence}>Evidence · hard constraints pass · C4 preserved · preference fit verified · opportunity neutral until F3 evidence</p>
          <p data-testid={testIds.replanDiff}>Tech Art Center removed · Design Library added · River Cruise preserved at 15:30</p>
          <p data-testid={testIds.replanDeltas}>Cost Δ ¥0 · travel Δ +5 min · risk Δ none · protected commitments unchanged</p>
          <div className="replan-actions">
            <button data-testid={testIds.acceptReplan} onClick={accept}>Accept replan</button>
            <button data-testid={testIds.rejectReplan} className="secondary-button" onClick={reject}>Reject</button>
          </div>
        </section>
      )}
      <p data-testid={testIds.aiExplanation} className="note">Explanations use verified JourneyTwin and ReplanDiff evidence.</p>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
