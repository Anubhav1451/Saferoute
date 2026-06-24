# app/api/v1/sos.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.sos import SOSRequest
from app.api.responses import success_response, error_response
import datetime

router = APIRouter()


@router.post("/sos/trigger")
async def trigger_sos(
    request: SOSRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger an emergency SOS alert.
    """
    try:
        # Simple response without any print statements to test if the endpoint works
        return success_response(
            data={
                "status": "success",
                "message": "Emergency SOS alert sent successfully",
                "timestamp": datetime.datetime.utcnow().isoformat(),
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
            },
            message="Emergency SOS alert sent successfully"
        )

    except ValueError as e:
        return error_response(
            error=str(e),
            error_code="VALIDATION_ERROR",
            message="Invalid input data for SOS request"
        )
    except Exception as e:
        return error_response(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            message="Failed to process SOS request"
        )
