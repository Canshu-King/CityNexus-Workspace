import { useEffect, useState } from "react";

type Props = { travelerId: string };
type PushConfig = { capability: string; public_key: string | null; record_fallback: boolean };

function decodeKey(value: string): Uint8Array {
  const padded = `${value}${"=".repeat((4 - (value.length % 4)) % 4)}`;
  const binary = window.atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

export function PushCapabilityCard({ travelerId }: Props) {
  const [config, setConfig] = useState<PushConfig | null>(null);
  const [message, setMessage] = useState("Checking delivery path…");

  useEffect(() => {
    void fetch(`/api/v1/travelers/${travelerId}/push-config`)
      .then((response) => response.json() as Promise<PushConfig>)
      .then(setConfig)
      .catch(() => setMessage("Push capability unavailable · in-app records remain active."));
  }, [travelerId]);

  const enable = async () => {
    if (!config?.public_key || !("serviceWorker" in navigator) || !("PushManager" in window)) {
      setMessage("No VAPID key is configured · notifications are recorded in the Journey.");
      return;
    }
    try {
      const registration = await navigator.serviceWorker.ready;
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: decodeKey(config.public_key),
      });
      const response = await fetch(`/api/v1/travelers/${travelerId}/push-subscriptions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(subscription.toJSON()),
      });
      if (!response.ok) throw new Error("subscription rejected");
      setMessage("Web Push subscription saved; policy-bound delivery remains auditable.");
    } catch {
      setMessage("Web Push was not enabled · the server will keep a notification record.");
    }
  };

  return (
    <article className="v8-me-card" data-testid="push-capability">
      <span className="v8-kicker">NOTIFICATIONS</span>
      <strong>{config?.capability ?? "CHECKING"}</strong>
      <p>{message}</p>
      <button className="v8-secondary" type="button" onClick={() => void enable()}>
        Enable Web Push
      </button>
    </article>
  );
}
