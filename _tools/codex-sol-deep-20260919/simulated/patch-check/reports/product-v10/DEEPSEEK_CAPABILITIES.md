# DeepSeek V4.1 capability evidence

## Official probe

The supplied V10 probe was run with the temporary DeepSeek key loaded into a child process only. No key or raw response was written to the repository.

| Capability | Live result | Honest interpretation |
|---|---|---|
| TEXT | HTTP 200; output types `reasoning`, `message` | Endpoint accepted a text response |
| FUNCTION | HTTP 400; `Thinking mode does not support this tool_choice` | Failed under the probe’s forced-thinking/tool-choice combination |
| WEB_SEARCH | HTTP 200; output types `reasoning`, `message` | Request accepted, but no normalized source observation was exposed |
| VISION | HTTP 200; output types `reasoning`, `message` | Request accepted, but live structured JSON was not asserted |

## CityNexus compatibility behavior

The Responses client defaults to `deepseek-flash` and `https://api.deepseek.com/responses`. It converts Chat-like messages/tools into Responses input, normalizes text/function/web metadata, keeps token/latency metadata, and retains reasoning/function continuation items in process memory for stateless tool turns. Forced tool turns send `reasoning: {"effort":"none"}`; a direct mocked transport test proves the function-call continuation path.

The image and pasted-text extractors demand strict JSON and allow `UNKNOWN`/null. They store only redacted artifact metadata and keep critical facts in a confirmation draft until validated.

