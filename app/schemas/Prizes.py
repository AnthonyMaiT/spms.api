from pydantic import BaseModel, conint

# schema for creating/updating a prize
class CreateUpdatePrize(BaseModel):
    name: str
    level: conint(ge=1,le=3)

# Prize schema for output
# references CreatePrize for fields
class Prize(CreateUpdatePrize):
    id: int
    class Config:
        orm_mode=True