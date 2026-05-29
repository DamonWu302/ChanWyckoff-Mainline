from dataclasses import dataclass
from typing import Protocol

from app.models.review import SignalLlmReview
from app.review.signal_review import LlmReviewPayload, RuleSignalContext, SignalReviewService


@dataclass(frozen=True, slots=True)
class LlmExplanationDraft:
    background_summary: str
    feature_summary: str
    forecast_summary: str
    failure_type: str | None
    attempted_rule_state: str | None = None
    attempted_action: str | None = None


class LlmExplanationProvider(Protocol):
    provider: str
    model: str

    async def explain(self, context: RuleSignalContext) -> LlmExplanationDraft:
        """Generate explanatory text from immutable rule output."""


class LlmSignalExplainer:
    def __init__(
        self,
        review_service: SignalReviewService,
        provider: LlmExplanationProvider,
    ) -> None:
        self.review_service = review_service
        self.provider = provider

    async def generate_for_record(self, signal_uid: str) -> SignalLlmReview:
        context = self.review_service.context_for_llm(signal_uid)
        draft = await self.provider.explain(context)
        return self.review_service.attach_llm_review(
            LlmReviewPayload(
                signal_uid=signal_uid,
                provider=self.provider.provider,
                model=self.provider.model,
                background_summary=draft.background_summary,
                feature_summary=draft.feature_summary,
                forecast_summary=draft.forecast_summary,
                failure_type=draft.failure_type,
                attempted_rule_state=draft.attempted_rule_state,
                attempted_action=draft.attempted_action,
            )
        )
