"""Seed script — inserts realistic fake incidents for UI development."""
import asyncio
from datetime import datetime, timedelta, timezone

from app.database import AsyncSessionLocal, init_db
from app.models.incident import AgentStep, Incident, IncidentStatus


INCIDENTS = [
    {
        "title": "High error rate on payment-service /checkout endpoint",
        "service_name": "payment-service",
        "severity": "critical",
        "status": IncidentStatus.analyzed,
        "source": "grafana",
        "log_snippets": [
            "ERROR 2024-01-15 14:23:01 PaymentGateway timeout after 30000ms",
            "ERROR 2024-01-15 14:23:05 Stripe API connect timeout: ETIMEDOUT",
            "WARN  2024-01-15 14:23:10 Circuit breaker OPEN for stripe-gateway",
            "ERROR 2024-01-15 14:23:15 500 POST /checkout - PaymentGatewayException",
        ],
        "metrics_data": {
            "error_rate_5xx": 0.34,
            "p99_latency_ms": 31200,
            "request_rate_rps": 245,
            "stripe_timeout_count": 892,
        },
        "log_analysis": "The logs show a cascade of Stripe API timeouts starting at 14:23:01. The circuit breaker opened after repeated failures, causing all checkout requests to fail fast. Error frequency increased from 0 to 892 events in under 15 minutes. Primary error: ETIMEDOUT on stripe-gateway DNS resolution.",
        "metrics_analysis": "Error rate spiked to 34% on the /checkout endpoint. P99 latency reached 31.2s (30x normal). Request rate remained stable at 245 RPS indicating this is not a traffic spike. The stripe_timeout_count metric confirms external dependency failure is the root cause, not internal processing.",
        "root_cause": "Stripe payment gateway experiencing network connectivity issues causing TCP connection timeouts, which cascaded to circuit breaker activation and complete checkout service degradation.",
        "confidence": 0.91,
        "runbook": "## Immediate Actions (first 15 minutes)\n1. Check Stripe status page at https://status.stripe.com\n2. Verify internal DNS resolution: `dig stripe.com`\n3. Test connectivity: `curl -I https://api.stripe.com/v1`\n4. Enable fallback payment processor if configured\n5. Alert on-call for payments team\n\n## Investigation Steps\n1. Check AWS NAT Gateway logs for packet drops\n2. Review network ACL changes in last 24h\n3. Verify Stripe API key expiry\n\n## Remediation\n1. If DNS issue: flush DNS cache on pods, restart CoreDNS\n2. If network: update security group rules or NAT Gateway\n3. Reset circuit breaker after connectivity restored\n\n## Verification\n- Error rate returns below 1%\n- P99 latency below 500ms\n- Stripe connectivity test passes\n\n## Prevention\n1. Add Stripe connectivity health check to readiness probe\n2. Configure secondary payment processor as fallback\n3. Alert on stripe_timeout_count > 10 per minute",
        "summary": "The payment-service experienced a critical outage starting at 14:23 UTC due to Stripe API connectivity failures. Network timeouts caused the circuit breaker to open, resulting in 34% checkout error rate. Engineering is investigating DNS and network connectivity to the Stripe API. Immediate mitigation involves resetting circuit breakers once connectivity is restored.",
        "minutes_ago": 45,
    },
    {
        "title": "Memory leak detected in recommendation-engine pods",
        "service_name": "recommendation-engine",
        "severity": "high",
        "status": IncidentStatus.analyzed,
        "source": "prometheus",
        "log_snippets": [
            "WARN  2024-01-15 11:05:22 JVM heap usage at 87% — GC pressure increasing",
            "WARN  2024-01-15 11:12:45 GC pause duration 3.2s — approaching SLA threshold",
            "ERROR 2024-01-15 11:34:01 java.lang.OutOfMemoryError: Java heap space",
            "ERROR 2024-01-15 11:34:02 Pod recommendation-engine-7d9f8b-xkp2m OOMKilled",
        ],
        "metrics_data": {
            "heap_usage_percent": 94.2,
            "gc_pause_p99_ms": 3200,
            "pod_restarts_1h": 4,
            "memory_mb": 3840,
            "memory_limit_mb": 4096,
        },
        "log_analysis": "JVM heap saturation progressing over 90 minutes before OOM. GC pause times increasing from baseline 50ms to 3.2s indicating heap pressure. OOMKilled on 4 pods in 1 hour confirms systemic memory leak, not a one-off event.",
        "metrics_analysis": "Heap usage at 94.2% with GC pressure causing 3.2s pauses. 4 pod restarts in 1 hour confirms persistent leak, not a traffic spike. Memory usage 3840MB against 4096MB limit with upward trend. Pattern consistent with object reference not being released (cache unbounded growth or listener leak).",
        "root_cause": "Unbounded in-memory cache growth in the recommendation-engine service — likely the user activity cache missing TTL or eviction policy, causing heap exhaustion over time.",
        "confidence": 0.84,
        "runbook": "## Immediate Actions\n1. Scale up recommendation-engine to distribute load: `kubectl scale deployment recommendation-engine --replicas=6`\n2. Trigger rolling restart to clear heap: `kubectl rollout restart deployment/recommendation-engine`\n\n## Investigation Steps\n1. Capture heap dump before restart: `kubectl exec <pod> -- jmap -dump:format=b,file=/tmp/heap.hprof 1`\n2. Analyze with Eclipse MAT or JVisualVM\n3. Review recent code changes to caching layer\n\n## Remediation\n1. Add eviction policy to UserActivityCache: `maximumSize(10000).expireAfterWrite(30, MINUTES)`\n2. Set JVM flags: `-XX:+HeapDumpOnOutOfMemoryError -XX:MaxHeapSize=3g`\n\n## Prevention\n1. Add heap usage alert at 75% threshold\n2. Add cache size metrics to dashboards\n3. Code review required for all cache additions",
        "summary": "Four pods of the recommendation-engine service were OOMKilled over a 90-minute window due to an unbounded in-memory cache growing without eviction. Engineering identified the UserActivityCache as the likely culprit and is deploying a fix with TTL-based eviction. Service is degraded but not fully down due to pod restart recovery.",
        "minutes_ago": 180,
    },
    {
        "title": "Database connection pool exhausted — user-service",
        "service_name": "user-service",
        "severity": "high",
        "status": IncidentStatus.analyzed,
        "source": "generic",
        "log_snippets": [
            "ERROR HikariPool-1 - Connection is not available, request timed out after 30000ms",
            "ERROR Unable to acquire JDBC Connection after 30s",
            "WARN  Active connections: 50/50 — pool exhausted",
            "ERROR select * from users where id=? — Acquisition timeout",
        ],
        "metrics_data": {
            "db_active_connections": 50,
            "db_pool_size": 50,
            "db_pending_requests": 234,
            "db_query_p99_ms": 12400,
            "api_error_rate": 0.18,
        },
        "log_analysis": "HikariCP connection pool fully exhausted at 50/50 connections. 234 requests queued waiting for connections. Slow query at P99 12.4s indicates queries are holding connections longer than expected — likely a missing index or a query returning large result sets.",
        "metrics_analysis": "Pool 100% utilised with 234 pending requests. P99 query time 12.4s (40x normal 300ms baseline). 18% API error rate on user-service endpoints. The combination of full pool + slow queries indicates connection starvation due to long-running transactions.",
        "root_cause": "A recently deployed query in the user profile update path is performing a full table scan due to a missing index on users.email, causing connection hold times to spike from 300ms to 12s and exhausting the connection pool.",
        "confidence": 0.88,
        "runbook": "## Immediate Actions\n1. Increase pool size temporarily: Update `spring.datasource.hikari.maximum-pool-size=100`\n2. Kill long-running queries: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='active' AND query_start < NOW() - INTERVAL '60 seconds';`\n\n## Investigation\n1. Find slow queries: `SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;`\n2. Check missing indexes: `EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@test.com';`\n\n## Remediation\n1. Add index: `CREATE INDEX CONCURRENTLY idx_users_email ON users(email);`\n2. Revert problematic deploy if index doesn't resolve\n\n## Prevention\n1. Add EXPLAIN ANALYZE to CI query review\n2. Alert on db_query_p99_ms > 1000ms",
        "summary": "The user-service database connection pool became fully exhausted due to slow queries caused by a full table scan on the users table. A recent deployment introduced a query filtering on users.email without an index, causing queries to take 40x longer than normal. Engineering is adding the missing index and temporarily increasing pool size to restore service.",
        "minutes_ago": 360,
    },
    {
        "title": "Elevated 5xx errors on api-gateway — TLS certificate warning",
        "service_name": "api-gateway",
        "severity": "medium",
        "status": IncidentStatus.analyzing,
        "source": "grafana",
        "log_snippets": [
            "WARN  TLS certificate for api.example.com expires in 7 days",
            "ERROR SSL handshake failed for upstream auth-service",
            "WARN  Certificate chain validation failed — intermediate cert missing",
        ],
        "metrics_data": {"5xx_rate": 0.03, "tls_handshake_failures": 12},
        "log_analysis": None,
        "metrics_analysis": None,
        "root_cause": None,
        "confidence": None,
        "runbook": None,
        "summary": None,
        "minutes_ago": 15,
    },
    {
        "title": "redis-cache latency spike affecting session service",
        "service_name": "session-service",
        "severity": "medium",
        "status": IncidentStatus.failed,
        "source": "prometheus",
        "log_snippets": [
            "WARN  Redis command latency p99=2340ms (threshold: 100ms)",
            "ERROR CLUSTERDOWN: The cluster is down",
        ],
        "metrics_data": {"redis_latency_p99_ms": 2340, "cache_hit_rate": 0.12},
        "log_analysis": None,
        "metrics_analysis": None,
        "root_cause": None,
        "confidence": None,
        "runbook": None,
        "summary": None,
        "error_message": "Ollama connection refused — ensure Ollama is running with `ollama serve`",
        "minutes_ago": 90,
    },
]


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        for data in INCIDENTS:
            minutes_ago = data.pop("minutes_ago")
            error_message = data.pop("error_message", None)
            created_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
            analyzed_at = None
            if data["status"] == IncidentStatus.analyzed:
                analyzed_at = created_at + timedelta(minutes=2, seconds=30)

            incident = Incident(
                **{k: v for k, v in data.items() if k not in ("log_analysis", "metrics_analysis", "root_cause", "confidence", "runbook", "summary")},
                log_analysis=data.get("log_analysis"),
                metrics_analysis=data.get("metrics_analysis"),
                root_cause=data.get("root_cause"),
                confidence=data.get("confidence"),
                runbook=data.get("runbook"),
                summary=data.get("summary"),
                error_message=error_message,
                created_at=created_at,
                analyzed_at=analyzed_at,
            )
            db.add(incident)
            await db.flush()

            if data["status"] == IncidentStatus.analyzed:
                steps = [
                    ("Log Analyst", "Log snippets from service", data.get("log_analysis", ""), 4200),
                    ("Metrics Correlator", "Metrics data dict", data.get("metrics_analysis", ""), 3800),
                    ("Root Cause Investigator", "Log + metrics synthesis", f"Root cause: {data.get('root_cause', '')} (confidence: {int((data.get('confidence') or 0)*100)}%)", 5100),
                    ("Runbook Writer", f"Root cause: {data.get('root_cause', '')[:60]}", f"Runbook generated ({len(data.get('runbook') or '')} chars)", 8300),
                ]
                for i, (agent, inp, out, lat) in enumerate(steps):
                    db.add(AgentStep(
                        incident_id=incident.id,
                        step_order=i,
                        agent_name=agent,
                        input_summary=inp,
                        output=out[:500] if out else "",
                        latency_ms=lat,
                        status="completed",
                    ))

        await db.commit()
    print(f"Seeded {len(INCIDENTS)} incidents.")


if __name__ == "__main__":
    asyncio.run(seed())
