# V12 Sourceful Web Runtime

The SearXNG adapter and DeepSeek web-search adapter remain optional, sourceful observation layers. They return provider, URL, title, snippet, captured time, and evidence status. Web observations can inform explanations or candidate discovery, but they do not become authoritative Journey facts until a CityNexus provider contract captures and validates them. When SearXNG is not configured, the runtime reports `NOT_CONFIGURED` and keeps the native DeepSeek path explicit rather than fabricating source coverage.
