from fastapi import APIRouter, HTTPException, Request, status

from app.trips.engine import EngineUnavailableError
from app.trips.options import plan_trip
from app.trips.schemas import PlanRequest, PlanResponse

router = APIRouter(prefix="/api/v1", tags=["trips"])


@router.post("/trips/plan")
async def plan(request: Request, body: PlanRequest) -> PlanResponse:
    """Route options between two places: public transport, auto, cab and walking."""
    try:
        return await plan_trip(
            request.app.state.planner, body.origin, body.destination, body.depart_at
        )
    except EngineUnavailableError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "The route planner isn't available right now. Please try again shortly.",
        ) from error
