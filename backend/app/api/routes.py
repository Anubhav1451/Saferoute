from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from app.db.session import get_db
from app.services.routing import SafetyRoutingService
from app.schemas.routing import RouteRequest, RouteResponse

router = APIRouter(prefix="/api/v1/route", tags=["routing"])


class SOSRequest(BaseModel):
    latitude: float
    longitude: float
    timestamp: str


@router.post("/calculate", response_model=RouteResponse)
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
        routing_service = SafetyRoutingService(db)
        
        result = routing_service.find_safest_route(
            source=request.source,
            destination=request.destination,
            safety_weight=request.safety_weight
        )
        
        return RouteResponse(
            safest_route=result["safest_route"],
            fastest_route=result["fastest_route"],
            safest_distance=result["safest_distance"],
            fastest_distance=result["fastest_distance"],
            safest_safety_score=result["safest_safety_score"],
            fastest_safety_score=result["fastest_safety_score"],
            route_segments=result["route_segments"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route calculation failed: {str(e)}")


@router.post("/sos/trigger")
async def trigger_sos(
    request: SOSRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger an emergency SOS alert.
    
    This endpoint simulates sending emergency alerts to contacts and authorities
    with the user's live coordinates and safety context.
    """
    try:
        # Simulate emergency alert processing
        print("\n" + "="*60)
        print("🚨 EMERGENCY SOS ALERT TRIGGERED 🚨")
        print("="*60)
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print(f"User Location: {request.latitude}, {request.longitude}")
        print(f"Original Timestamp: {request.timestamp}")
        print("\n📱 SENDING EMERGENCY ALERTS:")
        print("  ✅ SMS sent to emergency contact: +91-9876543210")
        print("  ✅ Email sent to: emergency@saferoute.ai")
        print("  ✅ Alert sent to Police Control Room (100)")
        print("  ✅ Alert sent to Women's Helpline (1091)")
        print("  ✅ Alert sent to Emergency Services (112)")
        print("\n📍 COORDINATES SHARED:")
        print(f"  Latitude: {request.latitude}")
        print(f"  Longitude: {request.longitude}")
        print(f"  Google Maps: https://maps.google.com/?q={request.latitude},{request.longitude}")
        print("\n🛡️ SAFETY CONTEXT:")
        print("  User's current safety route context attached")
        print("  Nearby safety nodes and crime hotspots identified")
        print("  Emergency response team dispatched")
        print("="*60 + "\n")
        
        return {
            "status": "success",
            "message": "Emergency SOS alert sent successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "location": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "alerts_sent": [
                "SMS to emergency contact",
                "Email to emergency services",
                "Police Control Room",
                "Women's Helpline",
                "Emergency Services"
            ]
        }
        
    except Exception as e:
        print(f"❌ ERROR processing SOS alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SOS trigger failed: {str(e)}")
