# app/api/v1/sos.py
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.sos import SOSRequest
from app.api.responses import success_response, error_response
import datetime

router = APIRouter()
logger = logging.getLogger("saferoute.api.sos")


@router.post("/sos/trigger")
async def trigger_sos(
    request: SOSRequest,
    db: Session = Depends(get_db)
):
    """
    Trigger an emergency SOS alert.

    NOTE: This is a simulation. No real emergency services are contacted.
    """
    try:
        # SEC-8: Label all dispatch details as simulated
        return success_response(
            data={
                "status": "simulated",
                "message": "SOS alert simulated successfully (demo mode — no real services contacted)",
                "simulated": True,
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "location": {
                    "latitude": request.latitude,
                    "longitude": request.longitude
                },
                "dispatch_details": {
                    "police_patrol": "[SIMULATED] Vehicle #04 would be redirected to location",
                    "guardians_notified": "[SIMULATED] +91 XXXXXXX890",
                    "emergency_contacts": ["100", "1091", "112"]
                },
                "alerts_sent": [
                    "[SIMULATED] SMS to emergency contact",
                    "[SIMULATED] Email to emergency services",
                    "[SIMULATED] Police Control Room",
                    "[SIMULATED] Women's Helpline",
                    "[SIMULATED] Emergency Services",
                    "[SIMULATED] Guardians notified"
                ]
            },
            message="SOS alert simulated successfully (demo mode)"
        )

    except ValueError as e:
        return error_response(
            error=str(e),
            error_code="VALIDATION_ERROR",
            message="Invalid input data for SOS request"
        )
    except Exception as e:
        logger.exception("SOS simulation failed")
        return error_response(
            error="Internal server error",
            error_code="INTERNAL_ERROR",
            message="Failed to process SOS request"
        )
