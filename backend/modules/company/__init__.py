from fastapi import APIRouter

# Create router that can be imported directly from the module
router = APIRouter(prefix="/company", tags=["Company"])

# Import the routes to register them with the router
from . import company
