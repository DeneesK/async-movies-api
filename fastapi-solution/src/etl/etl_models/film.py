from etl_models.base import AbstractModel
from pydantic.schema import Optional
from etl_models.person import Persons


class Filmwork(AbstractModel):
    imdb_rating: Optional[float] = 0.0
    genre: Optional[list] = []
    title: str
    description: Optional[str] = ''
    director: Optional[list] = []
    actors_names: Optional[list] = []
    writers_names: Optional[list] = []
    actors: Optional[list[Persons]] = []
    writers: Optional[list[Persons]] = []