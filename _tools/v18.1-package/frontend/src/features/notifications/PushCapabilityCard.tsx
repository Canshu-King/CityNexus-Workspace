import { useEffect, useState } from "react";
import { useT } from "../../i18n/LocaleContext";

type Props = { travelerId: string };
type PushConfig = { capability: string; public_key: string | null; record_fallback: boolean };

function decodeKey(value: string): Uint8Array {
  const padded = `${value}${"=".repeat((4 - (value.length % 4)) % 4)}`;
  const binary = window.atob(padded.replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

export function PushCapabilityCard({ travelerId }: Props) {
  const t = useT();
  const [config, setConfig] = useState<PushConfig | null>(null);
  const [message, setMessage] = useState(t("push.checking"));

  useEffect(() => {
    void fetch(`/api/v1/travelers/${travelerId}/push-config`)
      .then((response) => response.json() as Promise<PushConfig>)
      .then(setConfig)
      .catch(() => setMessage(t("push.unavailable")));
  }, [travelerId]);

  const enable = async () => {
    if (!config?.public_key || !("serviceWorker" in navigator) || !("PushManager" in window)) {
      setMessage(t("push.noKey"));
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
      setMessage(t("push.saved"));
    } catch {
      setMessage(t("push.notEnabled"));
    }
  };

  return (
    <article className="v8-me-card" data-testid="push-capability">
      <span className="v8-kicker">{t("push.kicker")}</span>
      <strong>{config?.capability ?? t("push.checkingState")}</strong>
      <p>{message}</p>
      <button className="v8-secondary" type="button" onClick={() => void enable()}>
        {t("push.enable")}
      </button>
    </article>
  );
}
