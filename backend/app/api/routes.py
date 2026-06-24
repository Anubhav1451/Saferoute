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
        # Simulate emergency alert processing with high-visibility terminal logging
        print("\n" + "="*70)
        print("🚨" + " "*20 + "CRITICAL SECURITY ALERT" + " "*20 + "🚨")
        print("="*70)
        print(f"⚠️  DISTRESS SIGNAL RECEIVED AT: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"📍 LOCATION: Lat: {request.latitude:.6f}, Lng: {request.longitude:.6f}")
        print(f"📱 SMS DISPATCHED TO GUARDIANS: \"+91 XXXXXXX890\"")
        print(f"🚔 STATUS: Police Patrol Vehicle #04 REDIRECTED TO LOCATION")
        print("\n" + "-"*70)
        print("� EMERGENCY RESPONSE LOG:")
        print("-"*70)
        print("  ✅ SMS sent to emergency contact: +91-9876543210")
        print("  ✅ Email sent to: emergency@saferoute.ai")
        print("  ✅ Alert sent to Police Control Room (100)")
        print("  ✅ Alert sent to Women's Helpline (1091)")
        print("  ✅ Alert sent to Emergency Services (112)")
        print("\n📍 COORDINATES SHARED:")
        print(f"  Latitude: {request.latitude:.6f}")
        print(f"  Longitude: {request.longitude:.6f}")
        print(f"  Google Maps: https://maps.google.com/?q={request.latitude},{request.longitude}")
        print("\n🛡️ SAFETY CONTEXT:")
        print("  ✓ User's current safety route context attached")
        print("  ✓ Nearby safety nodes and crime hotspots identified")
        print("  ✓ Emergency response team dispatched")
        print("  ✓ Live location tracking activated")
        print("="*70 + "\n")
        
        return {
            "status": "success",
            "message": "Emergency SOS alert sent successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "location": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "dispatch_details": {
                "police_patrol": "Vehicle #04 redirected to location",
                "guardians_notified": "+91 XXXXXXX890",
                "emergency_contacts": ["100", "1091", "112"]
            },
            "alerts_sent": [
                "SMS to emergency contact",
                "Email to emergency services",
                "Police Control Room",
                "Women's Helpline",
                "Emergency Services",
                "Guardians notified"
            ]
        }
        
    except Exception as e:
        print(f"❌ ERROR processing SOS alert: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SOS trigger failed: {str(e)}")
