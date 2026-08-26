"""The two Persona roles in the Data Agent Network demo."""

from __future__ import annotations

import re
from typing import Any

from phemacast_lite import Persona, PersonaProfile, PulseSpec
from prompits_lite import CallContext, Plaza
from prompits_lite.models import JsonObject

from .catalog import CATALOG, DataProduct


NEED_MARKERS: dict[str, tuple[str, ...]] = {
    "prices": ("price", "close", "market", "daily"),
    "returns": ("return", "performance"),
    "volatility": ("volatility", "risk", "dispersion"),
    "fundamentals": ("fundamental", "revenue", "margin", "income", "balance sheet"),
    "valuation": ("valuation", "multiple", "p/e", "ev/", "undervalued", "expensive"),
    "peers": ("peer", "compare company", "relative"),
    "rates": ("rate", "yield", "policy"),
    "inflation": ("inflation", "cpi", "prices index"),
    "macro": ("macro", "gdp", "economy", "economic"),
}

PRIORITY_MARKERS: dict[str, tuple[str, ...]] = {
    "low_cost": ("free", "low-cost", "low cost", "cheap"),
    "fresh": ("latest", "current", "fresh", "real-time", "realtime"),
    "reproducible": ("reproducible", "audit", "trace", "transparent"),
}


def _contains(text: str, markers: tuple[str, ...]) -> bool:
    for marker in markers:
        escaped = re.escape(marker).replace(r"\ ", r"\s+")
        prefix = r"(?<![a-z0-9])" if marker[0].isalnum() else ""
        suffix = r"(?![a-z0-9])" if marker[-1].isalnum() else ""
        if re.search(f"{prefix}{escaped}{suffix}", text):
            return True
    return False


def interpret_prompt(prompt: str) -> JsonObject:
    normalized = re.sub(r"\s+", " ", prompt.strip())
    lowered = normalized.lower()
    needs = [name for name, markers in NEED_MARKERS.items() if _contains(lowered, markers)]
    priorities = [name for name, markers in PRIORITY_MARKERS.items() if _contains(lowered, markers)]

    if not needs:
        needs = ["unclassified"]
    if "reproducible" not in priorities:
        priorities.append("reproducible")

    instruments = sorted(set(re.findall(r"\b[A-Z]{2,6}\b", normalized)))
    return {
        "original_prompt": normalized,
        "needs": needs,
        "priorities": priorities,
        "instruments": instruments,
        "constraints": [
            "Use fictional checked-in fixtures only.",
            "Expose freshness, access, and coverage gaps.",
        ],
    }


def _rank_product(product: DataProduct, request: JsonObject) -> JsonObject:
    needs = set(request.get("needs", []))
    priorities = set(request.get("priorities", []))
    matched = sorted(needs.intersection(product.coverage))
    score = len(matched) * 5
    reasons: list[str] = []

    if matched:
        reasons.append(f"covers {', '.join(matched)}")
    if matched:
        if "low_cost" in priorities and product.cost == "free":
            score += 2
            reasons.append("meets the low-cost constraint")
        if "reproducible" in priorities and product.reproducibility == "fully checked in":
            score += 2
            reasons.append("is fully reproducible")
        if "fresh" in priorities and "real-time" in product.freshness:
            score += 2
            reasons.append("has the lowest stated latency")
        if product.access == "contract required":
            score -= 10
            reasons.append("requires an unavailable contract")

    return {
        **product.to_dict(),
        "score": score,
        "matched_needs": matched,
        "rationale": "; ".join(reasons) if reasons else "context-only candidate",
    }


class DataConsultant(Persona):
    """Specialist Persona that evaluates data products and tradeoffs."""

    def __init__(self) -> None:
        super().__init__(
            name="Data Consultant",
            pit_id="data-consultant",
            description="Selects fit-for-purpose data and makes tradeoffs explicit.",
            profile=PersonaProfile(
                role="data-consultant",
                purpose="Turn a structured data need into an evidence-backed source plan.",
                instructions=(
                    "Rank only products present in the checked-in demo catalog.",
                    "Surface coverage, freshness, cost, access, and limitations.",
                    "Return structured evidence rather than an investment conclusion.",
                ),
            ),
        )
        self.register_pulse(
            PulseSpec(
                name="data_advice",
                description="Rank candidate data products for a structured request.",
                required_inputs=("request",),
                output_fields=("interpretation", "recommendations", "gaps", "decision_rules"),
                input_types={"request": dict},
                output_types={
                    "interpretation": dict,
                    "recommendations": list,
                    "gaps": list,
                    "decision_rules": list,
                },
            ),
            self._advise,
        )

    def _advise(self, payload: JsonObject, context: CallContext) -> JsonObject:
        request = dict(payload["request"])
        ranked = sorted(
            (_rank_product(product, request) for product in CATALOG),
            key=lambda candidate: (-int(candidate["score"]), str(candidate["name"])),
        )
        recommendations = [
            candidate
            for candidate in ranked
            if candidate["matched_needs"] and int(candidate["score"]) > 0
        ][:3]
        covered = {
            need
            for candidate in recommendations
            for need in candidate.get("matched_needs", [])
        }
        gaps = sorted(set(request.get("needs", [])) - covered)
        return {
            "interpretation": {
                "needs": list(request.get("needs", [])),
                "priorities": list(request.get("priorities", [])),
                "instruments": list(request.get("instruments", [])),
            },
            "recommendations": recommendations,
            "gaps": gaps,
            "decision_rules": [
                "Coverage fit contributes five points per requested need.",
                "Low-cost and reproducible fixtures receive explicit preference when requested.",
                "Unavailable contract access is penalized and never hidden.",
            ],
        }


class DataUser(Persona):
    """User-facing Persona that owns intent, delegation, and acceptance."""

    def __init__(self, plaza: Plaza) -> None:
        super().__init__(
            name="Data User",
            pit_id="data-user",
            description="Translates a financial question into a data request and presents the result.",
            profile=PersonaProfile(
                role="data-user",
                purpose="Preserve user intent while delegating source selection to a specialist.",
                instructions=(
                    "Normalize the request before delegation.",
                    "Discover the consultant through Plaza rather than a direct import or fixed address.",
                    "Validate returned evidence and explain any degraded state.",
                ),
            ),
        )
        self.plaza = plaza
        self.register_pulse(
            PulseSpec(
                name="data_request",
                description="Interpret, delegate, validate, and present one data question.",
                required_inputs=("prompt",),
                output_fields=("status", "request", "consultant", "answer", "benefit"),
                input_types={"prompt": str},
                output_types={
                    "status": str,
                    "request": dict,
                    "consultant": dict,
                    "answer": dict,
                    "benefit": dict,
                },
            ),
            self._answer,
        )

    def _answer(self, payload: JsonObject, context: CallContext) -> JsonObject:
        request = interpret_prompt(str(payload["prompt"]))
        context.trace.emit(
            stage="persona.interpret",
            actor=self.name,
            target="Data Consultant role",
            summary="Translate the human question into an explicit data contract.",
            detail={
                "needs": request["needs"],
                "priorities": request["priorities"],
                "instruments": request["instruments"],
            },
        )
        matches = self.plaza.search(
            pit_type="Persona",
            capability="data_advice",
            labels={"role": "data-consultant"},
            caller=self,
            trace=context.trace,
        )

        if not matches:
            context.trace.emit(
                stage="persona.degraded",
                actor=self.name,
                target=None,
                summary="Return a transparent degraded result; no consultant PIT is available.",
                detail={"unresolved_needs": request["needs"]},
            )
            return {
                "status": "degraded",
                "request": request,
                "consultant": {
                    "recommendations": [],
                    "gaps": list(request["needs"]),
                    "decision_rules": [],
                },
                "answer": {
                    "headline": "The request was captured, but specialist data advice is unavailable.",
                    "summary": "No Data Consultant matched the required Persona role and Pulse.",
                    "next_steps": ["Register a Data Consultant PIT in Plaza and rerun the same request."],
                    "caveat": "No source recommendation was fabricated in the degraded path.",
                },
                "benefit": self._benefit(status="degraded"),
            }

        consultant = self.plaza.invoke(
            caller=self,
            target=matches[0],
            capability="data_advice",
            payload={"request": request},
            trace=context.trace,
        )
        recommendations = list(consultant.get("recommendations", []))
        gaps = list(consultant.get("gaps", []))
        status = "complete" if recommendations and not gaps else "needs-review"
        context.trace.emit(
            stage="persona.validate",
            actor=self.name,
            target=None,
            summary="Validate coverage, gaps, and decision evidence before presenting the result.",
            detail={
                "recommendation_count": len(recommendations),
                "gaps": gaps,
            },
        )

        primary = recommendations[0] if recommendations else None
        secondary = recommendations[1] if len(recommendations) > 1 else None
        if primary:
            headline = f"Start with {primary['name']} for the strongest fit."
            summary = f"It {primary['rationale']}."
            if secondary:
                summary += f" Use {secondary['name']} as a complementary source because it {secondary['rationale']}."
        else:
            headline = "No catalog product covers the interpreted request."
            summary = "The evidence gap is explicit so the catalog can be extended without hiding uncertainty."

        context.trace.emit(
            stage="persona.present",
            actor=self.name,
            target="Demo UI",
            summary="Present the recommendation with provenance and limitations intact.",
            detail={"status": status, "primary": primary["product_id"] if primary else None},
        )
        return {
            "status": status,
            "request": request,
            "consultant": consultant,
            "answer": {
                "headline": headline,
                "summary": summary,
                "next_steps": [
                    "Confirm the required date range, units, and field definitions.",
                    "Replace fictional fixtures with an approved connector only outside this demo.",
                ],
                "caveat": "Educational demo only; synthetic metadata, no live market data, and no investment advice.",
            },
            "benefit": self._benefit(status=status),
        }

    @staticmethod
    def _benefit(*, status: str) -> JsonObject:
        return {
            "status": status,
            "separation": "Data User owns intent and acceptance; Data Consultant owns source-selection evidence.",
            "discoverability": "The specialist is found by PIT type, Persona role, and Pulse capability.",
            "inspectability": "One correlation id follows the request across discovery, routing, execution, and return.",
            "replaceability": "A different consultant can implement the same data_advice Pulse without changing Data User.",
        }
