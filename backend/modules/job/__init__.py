from fastapi import APIRouter

# Create router that can be imported directly from the module
router = APIRouter(prefix="/job", tags=["Job"])

# Import the routes to register them with the router
from . import job
