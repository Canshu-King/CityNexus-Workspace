import { useEffect, useRef, useState } from "react";
import { BrowserMultiFormatReader } from "@zxing/browser";

type Props = { onDecoded?: (value: string) => void };

/** Deterministic QR/barcode companion; decoded text still requires Inbox confirmation. */
export function BookingArtifactScanner({ onDecoded }: Props) {
  const video = useRef<HTMLVideoElement>(null);
  const [active, setActive] = useState(false);
  const [value, setValue] = useState<string | null>(null);

  useEffect(() => {
    if (!active || !video.current) return;
    const reader = new BrowserMultiFormatReader();
    let controls: { stop: () => void } | undefined;
    void reader.decodeFromVideoDevice(undefined, video.current, (result) => {
      if (!result) return;
      const text = result.getText();
      setValue(text);
      onDecoded?.(text);
      controls?.stop();
      setActive(false);
    }).then((next) => { controls = next; });
    return () => controls?.stop();
  }, [active, onDecoded]);

  return (
    <section className="v10-inbox-scanner" aria-label="Deterministic QR and barcode scanner">
      <div><b>Scan ticket code</b><small>ZXing deterministic decode · confirmation still required</small></div>
      {active && <video ref={video} className="v10-scanner-video" muted playsInline aria-label="Camera preview" />}
      {value && <code>{value}</code>}
      <button type="button" onClick={() => setActive((current) => !current)}>{active ? "Stop scanner" : "Open scanner"}</button>
    </section>
  );
}
