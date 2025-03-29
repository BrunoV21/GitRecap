from pydantic import BaseModel, model_validator
from typing import Dict, Self, Optional, Any
import ulid

class ChatRequest(BaseModel):
    session_id: str=""
    message: str
    model_params: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def set_session_id(self)->Self:
        if not self.session_id:
            self.session_id = ulid.ulid()
        return self