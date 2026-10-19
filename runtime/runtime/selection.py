from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StringConstraints, model_validator

from .mmr import explain_mmr


class Candidate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    relevance: Annotated[StrictFloat, Field(ge=0, le=1, allow_inf_nan=False)]
    title: Annotated[str, StringConstraints(max_length=300)] | None = None


class SelectionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    candidates: Annotated[list[Candidate], Field(min_length=1, max_length=100)]
    similarities: dict[str, dict[str, Annotated[StrictFloat, Field(ge=0, le=1, allow_inf_nan=False)]]]
    count: Annotated[StrictInt, Field(ge=1, le=100)]
    diversity_weight: Annotated[StrictFloat, Field(ge=0, le=1)]

    @model_validator(mode='after')
    def count_fits(self):
        if self.count > len(self.candidates):
            raise ValueError('选择数量不能超过候选数量')
        return self


def select_candidates(values):
    request = SelectionRequest.model_validate(values)
    return explain_mmr(request.model_dump(exclude_none=True))


def selection_router():
    router = APIRouter(prefix='/api/v1/runtime')

    @router.post('/mmr')
    def select(body: SelectionRequest):
        return select_candidates(body.model_dump())

    return router
