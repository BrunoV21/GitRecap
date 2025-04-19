
# Observability in GitRecap

GitRecap provides comprehensive observability features to monitor and analyze the application's performance and behavior.

## Key Components

### Logging
- [Logger Configuration](${AiCore_GitHub:-.}/app/api/services/logger.py)
  - Structured JSON logging
  - Log levels (DEBUG, INFO, WARNING, ERROR)
  - Correlation IDs for request tracing

### Metrics
- [Observability Dashboard](${AiCore_GitHub:-.}/app/api/services/observability_dashboard.py)
  - Request/response metrics
  - Error rates
  - Performance timings
  - Integration with Prometheus

### Tracing
- Distributed tracing support
- Request flow visualization
- Performance bottleneck identification

## Setup

1. Ensure observability is enabled in your `.env` file:
```bash
OBSERVABILITY_ENABLED=true
```

2. Configure the desired log level:
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

3. For metrics collection, set up Prometheus:
```bash
METRICS_ENABLED=true
PROMETHEUS_PORT=9090
```

## Usage Examples

### Viewing Logs
```bash
docker-compose logs -f api
```

### Accessing Metrics
```bash
curl http://localhost:9090/metrics
```

### Using the Dashboard
1. Start the observability service:
```bash
docker-compose up -d observability
```

2. Access the dashboard at:
```
http://localhost:3000/dashboard
```

## Troubleshooting

If observability features aren't working:
1. Verify all environment variables are set correctly
2. Check service logs for errors
3. Ensure required ports aren't blocked
4. Review the [troubleshooting guide](${AiCore_GitHub:-.}/docs/faq.md#observability)

## Related Documentation
- [Backend API Observability](${AiCore_GitHub:-.}/docs/backend.md#observability)
- [Performance Monitoring](${AiCore_GitHub:-.}/docs/backend.md#performance)
- [Logging Standards](${AiCore_GitHub:-.}/docs/contributing.md#logging)