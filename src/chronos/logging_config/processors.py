import os
from typing import Any

from structlog.types import EventDict


def add_service_name(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["service"] = "chronos-scheduler"
    return event_dict


def add_node_id(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    node_id = os.environ.get("CHRONOS_NODE_ID", "unknown")
    event_dict["node_id"] = node_id
    return event_dict
