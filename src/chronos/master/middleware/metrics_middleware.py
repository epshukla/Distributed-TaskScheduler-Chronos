from prometheus_fastapi_instrumentator import Instrumentator


def setup_metrics(app):  # type: ignore[no-untyped-def]
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_respect_env_var=False,
        excluded_handlers=["/health", "/ready", "/metrics"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="chronos_http_requests_inprogress",
        inprogress_labels=True,
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
