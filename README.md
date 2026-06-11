# loud-log-pipeline

Cloud-native log ingestion pipeline using AWS SQS, Lambda, S3, and DynamoDB. Includes a Python service layer and REST query API for structured log retrieval.

## Architecture Diagram

```text
+---------------------+        +----------------------+        +------------------------+
| auth-service        |        | billing-service      |        | notification-service   |
| producer scripts    |        | producer scripts     |        | producer scripts       |
+----------+----------+        +----------+-----------+        +-----------+------------+
           \                               |                                /
            \                              |                               /
             +-----------------------------+------------------------------+
                                           |
                                           v
                               +--------------------------+
                               | SQS log-ingestion-queue |
                               +------------+-------------+
                                            |
                                            v
                               +--------------------------+
                               | Lambda processor         |
                               | validates + normalizes   |
                               +------+-------------+-----+
                                      |             |
                                      v             v
                          +----------------+   +----------------+
                          | S3 log-archive |   | DynamoDB       |
                          | raw JSON files |   | log-index      |
                          +--------+-------+   +--------+-------+
                                   \                 /
                                    \               /
                                     v             v
                                   +-------------------+
                                   | FastAPI query API |
                                   +-------------------+
```

## Project Structure

```text
cloud-log-pipeline/
├── api/
├── cloud_log_pipeline/
├── docker/
├── infra/
├── processor/
├── producer/
├── tests/
├── .env.example
├── pyproject.toml
└── README.md
```

## How to Run Locally

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Start LocalStack, initialize AWS resources, and run the API:
   ```bash
   docker compose -f docker/docker-compose.yml up --build
   ```
3. Emit sample events from a producer:
   ```bash
   python -m producer.auth_service
   python -m producer.billing_service
   python -m producer.notification_service
   ```
4. Query the API:
   ```bash
   curl "http://localhost:8000/logs?service=auth-service&level=ERROR&from=2024-01-01&to=2024-01-31"
   ```
5. Inspect DLQ messages when debugging malformed events:
   ```bash
   python -m processor.dlq_reader
   ```

## Components

### Mock Producers

- `producer.auth_service`
- `producer.billing_service`
- `producer.notification_service`

Each producer emits 10–50 random structured events to `log-ingestion-queue`.

### Lambda Processor

`processor.handler.lambda_handler` processes SQS batches, validates each event, normalizes timestamps to UTC, stores raw event JSON in S3, and writes query metadata to DynamoDB. Invalid payloads are forwarded to `log-dlq`.

### REST Query API

- `GET /logs` filters metadata by service, level, and time range
- `GET /logs/{event_id}` fetches the full archived event from S3
- `GET /health` checks API, DynamoDB, and S3 connectivity
- `GET /stats` counts events by level for a service

## Example curl Commands

```bash
curl "http://localhost:8000/health"
curl "http://localhost:8000/logs?service=auth-service&level=ERROR&from=2024-01-01&to=2024-01-31"
curl "http://localhost:8000/logs/00000000-0000-0000-0000-000000000000"
curl "http://localhost:8000/stats?service=auth-service"
```

## Design Decisions

- **SQS over Kafka:** SQS is a better fit for this portfolio project because it matches the AWS-native architecture, keeps operations simple, and is more appropriate for moderate throughput than operating Kafka locally.
- **DynamoDB as the index:** DynamoDB provides a simple keyed lookup surface for service-and-time-range queries while S3 remains the durable source of truth for the raw event payloads.
- **Per-event S3 objects:** Writing each event as its own object keeps archival logic straightforward and makes it easy to retrieve a single event by `event_id`. The tradeoff is higher object-count overhead compared with batching.

## AWS Deployment Notes

For a real AWS deployment you would:

- deploy the SAM template in `infra/template.yaml`
- replace LocalStack endpoints with AWS-managed service endpoints
- attach IAM permissions for Lambda, S3, SQS, and DynamoDB access
- package and deploy the Lambda function artifact
- configure CloudWatch logging, alarms, and retry/observability policies

## Development and Testing

Install dependencies and run the tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```
