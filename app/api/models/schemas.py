from pydantic import BaseModel, model_validator
from typing import Dict, Self, Optional, Any, List
import ulid

class ChatRequest(BaseModel):
    session_id: str = ""
    message: str
    model_params: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def set_session_id(self) -> Self:
        if not self.session_id:
            self.session_id = ulid.ulid()
        return self

# --- Release Notes Request/Response Schemas ---

class ReleaseNotesRequest(BaseModel):
    session_id: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    repo_filter: Optional[List[str]] = None
    authors: Optional[List[str]] = None

class ReleaseNotesResponse(BaseModel):
    release_notes: str