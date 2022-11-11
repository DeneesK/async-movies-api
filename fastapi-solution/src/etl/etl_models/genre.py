from etl_models.base import AbstractModel
from pydantic.schema import Optional


class Genre(AbstractModel):
    name: str
    description: Optional[str] = ''
