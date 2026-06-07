"""
Movie Game related Pydantic models.
"""
from pydantic import BaseModel


class GameChoiceV2(BaseModel):
    session_id: str
    round_number: int
    chosen_movie_id: int
    rejected_movie_id: int
    reaction_time_ms: int  # Milliseconds taken to make choice
    is_super_like: bool = False
    is_cant_decide: bool = False  # Both movies get equal points
