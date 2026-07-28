# app/api/v1/routing.py
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.routing import SafetyRoutingService
from app.schemas.routing import RouteRequest, RouteResponse
from app.api.responses import success_response, error_response

router = APIRouter()
logger = logging.getLogger("saferoute.api.routing")


@router.post("/calculate")
async def calculate_route(
    request: RouteRequest,
    db: Session = Depends(get_db)
):
    """
    Calculate the safest and fastest routes between source and destination.

    The routing algorithm considers:
    - Distance (base cost)
    - Crime hotspots (high severity = heavy penalty)
    - Safety nodes with low lighting or sparse crowd (medium penalty)
    - Recent active user reports (dynamic penalty based on recency)

    Returns both the safest route (weighted for safety) and fastest route (shortest distance).
    """
    try:
        # RT-2: Guard same source/destination
        if (abs(request.source.latitude - request.destination.latitude) < 1e-6 and
                abs(request.source.longitude - request.destination.longitude) < 1e-6):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=error_response(
                    error="Source and destination are identical",
                    error_code="IDENTICAL_POINTS",
                    message="Source and destination must be different locations"
                )
            )

        routing_service = SafetyRoutingService(db)

        # ARC-1: Run blocking routing computation in a thread to avoid blocking the event loop
        result = await asyncio.to_thread(
            routing_service.find_safest_route,
            source=request.source,
            destination=request.destination,
            safety_weight=request.safety_weight,
        )
        logger.info("Route calculated: %d safest pts, %d fastest pts",
                     len(result.get('safest_route', [])),
                     len(result.get('fastest_route', [])))

        response = success_response(
            data={
                "safest_route": result["safest_route"],
                "fastest_route": result["fastest_route"],
                "safest_distance": result["safest_distance"],
                "fastest_distance": result["fastest_distance"],
                "safest_safety_score": result["safest_safety_score"],
                "fastest_safety_score": result["fastest_safety_score"],
                "route_segments": result["route_segments"]
            },
            message="Route calculation completed successfully"
        )
        return response

    except ValueError as e:
        logger.warning("Route validation error: %s", e)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_response(
                error=str(e),
                error_code="VALIDATION_ERROR",
                message="Invalid input data"
            )
        )
    except Exception as e:
        logger.exception("Route calculation failed")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response(
                error="Internal server error",
                error_code="INTERNAL_ERROR",
                message="Route calculation failed"
            )
        )


# Optional: Add a health check endpoint for the routing service
@router.get("/health")
async def routing_health():
    """Health check for routing service"""
    return success_response(
        data={"status": "healthy"},
        message="Routing service is operational"
    )