from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.film import FilmService, get_film_service

# Объект router, в котором регистрируем обработчики
router = APIRouter()


class Film(BaseModel):
    id: str
    title: str
    description: str | None
    imdb_rating: float
    genre: list | None
    director: list | None
    actors: list | None
    writers: list | None


@router.get('/film/{film_id}',
            response_model=Film,
            description='Getting a movie by its id',
            summary="Film Search by id",
            response_description="Title, film rating, genre, description and staff working on the film"
            )
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum
        # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    # Перекладываем данные из models.Film в Film
    # Обратите внимание, что у модели бизнес-логики есть поле description
    # Которое отсутствует в модели ответа API.
    # Если бы использовалась общая модель для бизнес-логики и формирования ответов API
    # вы бы предоставляли клиентам данные, которые им не нужны
    # и, возможно, данные, которые опасно возвращать
    return Film(**film.dict())


@router.get('/search/',
            response_model=list[Film],
            description='Get a list movies that match query',
            summary="Films Search by query",
            response_description="Title, film rating, genre, description and staff working on the film"
            )
async def films_list(query: str | None = Query(default=None),
                     sort: list[str] = Query(default=['imdb_rating']),
                     from_: int | None = None,
                     page_size: int | None = None,
                     film_service: FilmService = Depends(get_film_service)) -> list:
    films = await film_service.get_films_by_query(query, from_, page_size, sort)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='nothing found')
    return [Film(**f.dict()) for f in films]
