from pydantic import BaseModel, conint

# schema for creating a prize
class CreatePrize(BaseModel):
    name: str
    level: conint(ge=1,le=3)

# Prize schema for output
# references CreatePrize for fields
class Prize(CreatePrize):
    id: int
    class Config:
        orm_mode=True