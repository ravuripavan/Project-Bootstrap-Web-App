from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def list_templates():
    """List available project templates"""
    return {"templates": []}

@router.get("/{template_id}")
async def get_template(template_id: str):
    """Get template details"""
    return {"template_id": template_id}
