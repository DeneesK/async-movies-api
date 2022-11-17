from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from services.genre import GenreService, get_genre_service

# Объект router, в котором регистрируем обработчики
router = APIRouter()


# Модель ответа API
class Genre(BaseModel):
    id: str
    name: str
    description: str

# С помощью декоратора регистрируем обработчик genre_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру
# И адрес запроса будет выглядеть так — /api/v1/genre/some_id
# В сигнатуре функции указываем тип данных, получаемый из адреса запроса (person_id: str)
# И указываем тип возвращаемого объекта — Genre

# Внедряем GenreService с помощью Depends(get_genre_service)
@router.get('/genre/{genre_id}', response_model=Genre)
async def genre_details(genre_id: str, genre_service: GenreService = Depends(get_genre_service)) -> Genre:
    genre_lst = await genre_service.get_by_id(genre_id)
    if not genre_lst:
        # Если жанр не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum
                # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')
    else:
        # We ised id, so there is only one item.
        person = genre_lst[0]
    return Genre(**person.dict())


@router.get('/search/', response_model=list[Genre])
async def genres_list(query: str | None = Query(default=None),
                      sort:list[str]=Query(default=None),
                      filter:list[str]=Query(default=None),
                      from_:int=None, page_size:int=None,
                      person_service: GenreService = Depends(get_genre_service)) -> list:
    """sort must be json-encoded list. An example:
        http://127.0.0.1:8000/api/v1/genres/search/?query=Adventure?sort=["description.raw"]
        http://127.0.0.1:8000/api/v1/genres/search/?query=Adventure?filter=["Some quoted name"]
        """

    genres = await person_service.get_genres_by_query(query, from_, page_size,
                                                      sort, filter)
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='nothing found')
    return [Genre(**f.dict()) for f in genres]