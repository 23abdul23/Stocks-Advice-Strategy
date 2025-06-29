from typing import TypedDict, Literal, List, Optional, Dict
from pydantic import BaseModel, Field

class UsageClassfier(BaseModel):
    user_query: str
    usage: Optional[Literal["advice", "strategy", "invalid"]] = "invalid"
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
    stocks: Optional[List[str]] = Field(default_factory=list)

class AppState(TypedDict):
    usage: str
    user_query: str
    stocks: Optional[List[str]]

    #Agent Outputs
    portfolio: str

    news : str
    news_dict: Dict
    market_news : str

    
    macro_economics : str
    macro_economics_dict : Dict

    market_trends : str

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
