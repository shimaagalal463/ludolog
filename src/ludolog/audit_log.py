"""Append-only audit trail."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from .storage import Library


@dataclass
class AuditEntry:
    at: str
    action: str
    detail: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"at": self.at, "action": self.action, "detail": dict(self.detail)}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AuditEntry":
        return cls(
            at=str(data.get("at", "")),
            action=str(data.get("action", "")),
            detail=dict(data.get("detail") or {}),
        )


def log_action(lib: "Library", action: str, detail: Dict[str, Any] | None = None) -> None:
    entry = AuditEntry(
        at=datetime.now().isoformat(timespec="seconds"),
        action=action,
        detail=detail or {},
    )
    lib.audit_log.append(entry)
    if len(lib.audit_log) > 500:
        lib.audit_log = lib.audit_log[-500:]


def recent_actions(lib: "Library", limit: int = 20) -> list[AuditEntry]:
    return list(reversed(lib.audit_log[-limit:]))


def filter_audit(lib, action_prefix: str) -> list[AuditEntry]:
    return [a for a in lib.audit_log if a.action.startswith(action_prefix)]


def audit_for_entity(lib, entity: str, entity_id: int) -> list[AuditEntry]:
    key = str(entity_id)
    out = []
    for a in lib.audit_log:
        if a.detail.get("id") == entity_id or a.detail.get(entity) == entity_id:
            out.append(a)
        elif key in str(a.detail.values()):
            out.append(a)
    return out
