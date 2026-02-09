from typing import Literal, Optional
from pydantic import BaseModel

class ActionResponse(BaseModel):
    status: Literal["ok"] = "ok"
    message: Optional[str] = None