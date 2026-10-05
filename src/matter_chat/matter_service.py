from __future__ import annotations

import os

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status

from .infrai_client import InfraiError, InfraiRealtime
from .workflow import (
    DeadlineCheck,
    FollowUpResult,
    IntakeResult,
    MatterIntake,
    MatterWorkflow,
    SignedDocumentDelivery,
)

app = FastAPI(title="Private matter chat")


def workflow() -> MatterWorkflow:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")
    return MatterWorkflow(InfraiRealtime(api_key))


def client_status(error: InfraiError) -> int:
    return error.status_code if 400 <= error.status_code < 500 else status.HTTP_502_BAD_GATEWAY


@app.post("/matters/intake", response_model=IntakeResult)
def intake(request: MatterIntake, service: MatterWorkflow = Depends(workflow)) -> IntakeResult:
    try:
        return service.intake(request)
    except InfraiError as error:
        raise HTTPException(status_code=client_status(error), detail=error.detail) from error


@app.post("/matters/signed-document", status_code=status.HTTP_204_NO_CONTENT)
def signed_document(
    request: SignedDocumentDelivery, service: MatterWorkflow = Depends(workflow)
) -> None:
    try:
        service.deliver_signed_document(request)
    except InfraiError as error:
        raise HTTPException(status_code=client_status(error), detail=error.detail) from error


@app.post("/matters/deadline-check", response_model=FollowUpResult)
def deadline_check(
    request: DeadlineCheck, service: MatterWorkflow = Depends(workflow)
) -> FollowUpResult:
    try:
        return service.check_deadline(request)
    except InfraiError as error:
        raise HTTPException(status_code=client_status(error), detail=error.detail) from error


def run() -> None:
    uvicorn.run("matter_chat.matter_service:app", host="127.0.0.1", port=8000)
