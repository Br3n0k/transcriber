from fastapi.templating import Jinja2Templates
from datetime import datetime
from .config import settings
from .theme import default_theme

# Create a single Jinja2Templates instance
templates = Jinja2Templates(directory=str(settings.templates_dir))

# Register Filters
def timestamp_to_date(timestamp: float) -> str:
    try:
        return datetime.fromtimestamp(timestamp).strftime('%d/%m/%Y %H:%M')
    except Exception:
        return ""

templates.env.filters["timestamp_to_date"] = timestamp_to_date

# Register Globals
templates.env.globals["theme"] = default_theme()
