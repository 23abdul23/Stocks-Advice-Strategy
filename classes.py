from typing import TypedDict, Literal, List, Optional
from langchain_core.pydantic_v1 import BaseModel, Field

class UsageClassfier(BaseModel):
    user_query: str
    usage: Optional[Literal["advice", "strategy", "invalid"]] = None
    age: Optional[int] = None
    job_type: Optional[str] = ""
    job: Optional[str] = ""
    monthly_income: Optional[float] = None
    side_income: Optional[float] = None
    investment_goal: Optional[str] = ""
    investment_duration: Optional[str] = ""
    risk_preference: Optional[float] = None
    investing_years: Optional[int] = None
    retirement_age: Optional[int] = None
    martial_status: Optional[str] = ""
    children: Optional[int] = None
    stocks : Optional[List[str]] = []

class AppState(TypedDict):
    usage : str
    stocks : Optional[List[str]] = []

    #Agent Outputs
    portfolio : str
    market_news : str
    market_trends : str
    macro_economics : str
    advice : str
    strategy : str
    final_proposal : str

    #Optionals
    """
    exsisting_loans : float
    monthly_saving : float
    preferred_industry : List
    tax_bracket : str
    preferred_instruments : List
    past_losses : float
    """
