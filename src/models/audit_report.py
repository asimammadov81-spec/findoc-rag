"""
AuditReport - FinancialDocument-in konkret alt sinifi
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum

from .financial_document import DocumentType, FinancialDocument


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ACCEPTED = "accepted"


@dataclass
class AuditFinding:
    """Audit tapintisi."""
    finding_id: str
    description: str
    risk_level: RiskLevel
    status: FindingStatus = FindingStatus.OPEN
    recommendation: str = ""

    def __str__(self) -> str:
        return f"[{self.risk_level.value.upper()}] {self.finding_id}: {self.description}"


@dataclass
class AuditReport(FinancialDocument):
    """Audit hesabati senedi."""

    auditor_name: str = ""
    audit_period_start: date = field(default_factory=date.today)
    audit_period_end: date = field(default_factory=date.today)
    findings: list[AuditFinding] = field(default_factory=list)
    overall_risk: RiskLevel = RiskLevel.LOW

    def __post_init__(self):
        self.doc_type = DocumentType.AUDIT_REPORT

    def summary(self) -> str:
        critical = self.findings_by_risk(RiskLevel.CRITICAL)
        high = self.findings_by_risk(RiskLevel.HIGH)
        return (
            f"Audit Hesabati: {self.title}\n"
            f"  Auditor  : {self.auditor_name}\n"
            f"  Dovr     : {self.audit_period_start} -> {self.audit_period_end}\n"
            f"  Umumi risk: {self.overall_risk.value.upper()}\n"
            f"  Tapintilar: {len(self.findings)} "
            f"(kritik: {len(critical)}, yuksek: {len(high)})"
        )

    def validate(self) -> bool:
        errors = []
        if not self.auditor_name:
            errors.append("auditor_name bosdur")
        if self.audit_period_end < self.audit_period_start:
            errors.append("period_end, period_start-dan evvel ola bilmez")
        if errors:
            print(f"[Validate] {self.doc_id} - xetalar: {errors}")
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "doc_type": self.doc_type.value,
            "title": self.title,
            "created_date": self.created_date.isoformat(),
            "auditor_name": self.auditor_name,
            "audit_period_start": self.audit_period_start.isoformat(),
            "audit_period_end": self.audit_period_end.isoformat(),
            "overall_risk": self.overall_risk.value,
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "description": f.description,
                    "risk_level": f.risk_level.value,
                    "status": f.status.value,
                    "recommendation": f.recommendation,
                }
                for f in self.findings
            ],
            "tags": self.tags,
        }

    def add_finding(
        self,
        finding_id: str,
        description: str,
        risk_level: RiskLevel,
        recommendation: str = "",
    ) -> AuditFinding:
        finding = AuditFinding(
            finding_id=finding_id,
            description=description,
            risk_level=risk_level,
            recommendation=recommendation,
        )
        self.findings.append(finding)
        self._update_overall_risk()
        return finding

    def findings_by_risk(self, risk_level: RiskLevel) -> list[AuditFinding]:
        return [f for f in self.findings if f.risk_level == risk_level]

    def _update_overall_risk(self) -> None:
        if not self.findings:
            return
        levels = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        max_idx = max(levels.index(f.risk_level) for f in self.findings)
        self.overall_risk = levels[max_idx]
