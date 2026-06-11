from __future__ import annotations

from producer.base import emit_events


if __name__ == "__main__":
    events = emit_events("billing-service")
    print(f"Emitted {len(events)} billing events")
