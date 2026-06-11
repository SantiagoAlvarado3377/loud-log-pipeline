from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query

from cloud_log_pipeline.models import ALLOWED_LEVELS, coerce_query_timestamp
from cloud_log_pipeline.storage import LogStorage

app = FastAPI(title="Cloud Log Pipeline API")


@lru_cache(maxsize=1)
def get_storage() -> LogStorage:
    return LogStorage()


@app.get("/health")
def health() -> dict:
    checks = get_storage().health_check()
    status = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return {"status": status, "dependencies": checks}


@app.get("/logs")
def list_logs(
    service: str = Query(..., description="Service name to query"),
    level: str | None = Query(default=None),
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = Query(default=None),
) -> dict:
    if level and level not in ALLOWED_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid log level")

    items = get_storage().query_logs(
        service=service,
        level=level,
        from_timestamp=coerce_query_timestamp(from_) if from_ else None,
        to_timestamp=coerce_query_timestamp(to, end_of_day=True) if to else None,
    )
    return {"items": items, "count": len(items)}


@app.get("/logs/{event_id}")
def get_log(event_id: str) -> dict:
    event = get_storage().get_log_by_event_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Log event not found")
    return event


@app.get("/stats")
def stats(service: str = Query(..., description="Service name to summarize")) -> dict:
    return {"service": service, "counts": get_storage().get_stats(service)}
