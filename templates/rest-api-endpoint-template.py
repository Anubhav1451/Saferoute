"""
REST API Endpoint Template

This template follows RESTful principles and FastAPI conventions.
Can be adapted for other frameworks like Flask, Django REST Framework, etc.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import logging

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Router
router = APIRouter(
    prefix="/api/v1/[resource]",
    tags=["[resource]"],
    responses={404: {"description": "Not found"}},
)


# Pydantic Models
class [Resource]Base(BaseModel):
    """Base model for [Resource]."""
    name: str = Field(..., min_length=1, max_length=100, description="Name of the resource")
    description: Optional[str] = Field(None, max_length=500, description="Description of the resource")

    class Config:
        schema_extra = {
            "example": {
                "name": "example-name",
                "description": "An example resource"
            }
        }


class [Resource]Create([Resource]Base):
    """Model for creating a new [Resource]."""
    pass


```

Please continue writing the code from where it was cut off. I'll complete the partial thought from the previous rewritten thinking and then finish the rest by copying over the next part directly, making sure to follow the instructions. There is a special consideration to drop markdown formatting when instructed.

[Resource]Create([Resource]Base):
    """Model for creating a new [Resource]."""
    pass


class [Resource]Update(BaseModel):
    """Model for updating an existing [Resource]."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class [Resource]Response([Resource]Base):
    """Model for [Resource] response."""
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        orm_mode = True


# Dependency functions
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """Validate and return current user.

    Args:
        credentials: HTTP Bearer token

    Returns:
        User information dictionary

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    # TODO: Implement actual token validation
    # For now, return mock user
    return {
        "id": "user-123",
        "username": "example_user",
        "roles": ["user"]
    }


async def validate_permissions(
    user: Dict[str, Any] = Depends(get_current_user),
    required_role: str = "user"
) -> Dict[str, Any]:
    """Validate user has required permissions.

    Args:
        user: Current user information
        required_role: Minimum role required

    Returns:
        User information if authorized

    Raises:
        HTTPException: If user lacks required permissions
    """
    role_hierarchy = {"admin": 3, "editor": 2, "user": 1}
    user_role = user.get("roles", ["user"])[0] if user.get("roles") else "user"
    user_level = role_hierarchy.get(user_role, 0)
    required_level = role_hierarchy.get(required_role, 1)

    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {required_role}"
        )

    return user


# API Endpoints
@router.post(
    "/",
    response_model=[Resource]Response,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new [Resource]",
    description="Create a new [Resource] with the provided data"
)
async def create_resource(
    resource: [Resource]Create,
    user: Dict[str, Any] = Depends(lambda: validate_permissions(required_role="editor"))
) -> [Resource]Response:
    """Create a new [Resource].

    Args:
        resource: Resource data to create
        user: Current authenticated user (injected by dependency)

    Returns:
        Created resource with metadata

    Raises:
        HTTPException: If resource creation fails
    """
    try:
        # TODO: Implement actual resource creation logic
        # This is where you would save to database, etc.

        # Mock response for demonstration
        resource_id = f"resource-{datetime.utcnow().timestamp()}"
        now = datetime.utcnow()

        response = [Resource]Response(
            id=resource_id,
            name=resource.name,
            description=resource.description,
            created_at=now,
            updated_at=now
        )

        logger.info(f"Created resource {resource_id} by user {user['id']}")
        return response

    except Exception as e:
        logger.error(f"Failed to create resource: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create resource"
        )


@router.get(
    "/",
    response_model=List[Response],
    summary="List [Resources]",
    description="Retrieve a list of [Resources] with optional filtering and pagination"
)
async def list_resources(
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of items to return"),
    name: Optional[str] = Query(None, description="Filter by name"),
    user: Dict[str, Any] = Depends(lambda: validate_permissions(required_role="viewer"))
) -> List[Response]:
    """List [Resources].

    Args:
        skip: Number of items to skip for pagination
        limit: Maximum number of items to return
        name: Optional name filter
        user: Current authenticated user (injected by dependency)

    Returns:
        List of resources matching the criteria
    """
    try:
        # TODO: Implement actual resource retrieval logic
        # This is where you would query database with filters

        # Mock response for demonstration
        resources = []
        for i in range(min(limit, 3)):  # Return up to 3 mock items
            resource_id = f"resource-{i + skip}"
            resources.append(
                Response(
                    id=resource_id,
                    name=f"{resource.name or 'sample'}-{i}",
                    description=f"Sample resource {i}",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )

        logger.info(f"Listed {len(resources)} resources for user {user['id']}")
        return resources

    except Exception as e:
        logger.error(f"Failed to list resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resources"
        )


@router.get(
    "/{resource_id}",
    response_model=Response,
    summary="Get [Resource] by ID",
    description="Retrieve a specific [Resource] by its unique identifier"
)
async def get_resource(
    resource_id: str = Path(..., description="The ID of the resource to retrieve"),
    user: Dict[str, Any] = Depends(lambda: validate_permissions(required_role="viewer"))
) -> Response:
    """Get a specific [Resource] by ID.

    Args:
        resource_id: Unique identifier of the resource
        user: Current authenticated user (injected by dependency)

    Returns:
        Resource with the specified ID

    Raises:
        HTTPException: If resource is not found
    """
    try:
        # TODO: Implement actual resource retrieval logic
        # This is where you would fetch from database by ID

        # Mock response for demonstration
        if not resource_id.startswith("resource-"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        resource = Response(
            id=resource_id,
            name="sample-resource",
            description="A sample resource",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        logger.info(f"Retrieved resource {resource_id} for user {user['id']}")
        return resource

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve resource {resource_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve resource"
        )


@router.put(
    "/{resource_id}",
    response_model=Response,
    summary="Update [Resource]",
    description="Update an existing [Resource] with the provided data"
)
async def update_resource(
    resource_id: str = Path(..., description="The ID of the resource to update"),
    resource_update: ResourceUpdate = ...,
    user: Dict[str, Any] = Depends(lambda: validate_permissions(required_role="editor"))
) -> Response:
    """Update an existing [Resource].

    Args:
        resource_id: Unique identifier of the resource to update
        resource_update: Data to update the resource with
        user: Current authenticated user (injected by dependency)

    Returns:
        Updated resource

    Raises:
        HTTPException: If resource is not found or update fails
    """
    try:
        # TODO: Implement actual resource update logic
        # This is where you would update in database

        # Mock response for demonstration
        if not resource_id.startswith("resource-"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        # Get existing resource (mock)
        existing_resource = Response(
            id=resource_id,
            name="existing-resource",
            description="An existing resource",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Apply updates
        updated_data = existing_resource.dict()
        update_data = resource_update.dict(exclude_unset=True)

        for field, value in update_data.items():
            if value is not None:
                updated_data[field] = value

        updated_data["updated_at"] = datetime.utcnow()
        updated_resource = Response(**updated_data)

        logger.info(f"Updated resource {resource_id} by user {user['id']}")
        return updated_resource

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update resource {resource_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update resource"
        )


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete [Resource]",
    description="Delete a [Resource] by its unique identifier"
)
async def delete_resource(
    resource_id: str = Path(..., description="The ID of the resource to delete"),
    user: Dict[str, Any] = Depends(lambda: validate_permissions(required_role="admin"))
) -> None:
    """Delete a [Resource] by ID.

    Args:
        resource_id: Unique identifier of the resource to delete
        user: Current authenticated user (injected by dependency)

    Raises:
        HTTPException: If resource is not found or deletion fails
    """
    try:
        # TODO: Implement actual resource deletion logic
        # This is where you would remove from database

        # Mock validation for demonstration
        if not resource_id.startswith("resource-"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )

        logger.info(f"Deleted resource {resource_id} by user {user['id']}")
        # Return None for 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete resource {resource_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete resource"
        )


# Health check endpoint
@router.get(
    "/health",
    summary="Health check",
    description="Check the health status of the [Resource] service"
)
async def health_check() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "service": "[resource]",
        "timestamp": datetime.utcnow().isoformat()
    }


# Export router
__all__ = ["router"]