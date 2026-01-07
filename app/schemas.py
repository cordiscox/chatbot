from pydantic import BaseModel, Field
import uuid

class ChatRequest(BaseModel):
    """
    Template for customer chat request.
    """
    user_input: str = Field(..., description="The message sent by the user.")
    session_id: str = Field(..., description="Unique identifier for the chat session.")
    captcha_token: str | None = Field(None, description="The CAPTCHA token from the frontend, required for the first message.")

class SessionResponse(BaseModel):
    """
    Template for the response when creating a new session.
    """
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="The new session ID generated.")