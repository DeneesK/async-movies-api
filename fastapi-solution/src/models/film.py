from models.base import AbstractModel


class Film(AbstractModel):
    title: str
    description: str | None
    imdb_rating: float
    genre: list | None
    director: list
    actors: list | None
    writers: list | None
