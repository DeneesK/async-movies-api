from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from services.person import PersonService, get_person_service

# Объект router, в котором регистрируем обработчики
router = APIRouter()


# Модель ответа API
class Person(BaseModel):
    id: str
    name: str

# С помощью декоратора регистрируем обработчик person_details
# На обработку запросов по адресу <some_prefix>/some_id
# Позже подключим роутер к корневому роутеру
# И адрес запроса будет выглядеть так — /api/v1/person/some_id
# В сигнатуре функции указываем тип данных, получаемый из адреса запроса (person_id: str)
# И указываем тип возвращаемого объекта — Person

# Внедряем FilmService с помощью Depends(get_film_service)
@router.get('/person/{person_id}', response_model=Person)
async def person_details(person_id: str, person_service: PersonService = Depends(get_person_service)) -> Person:
    person_lst = await person_service.get_by_id(person_id)
    if not person_lst:
        # Если фильм не найден, отдаём 404 статус
        # Желательно пользоваться уже определёнными HTTP-статусами, которые содержат enum
                # Такой код будет более поддерживаемым
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')
    else:
        # We ised id, so there is only one item.
        person = person_lst[0]
    return Person(**person.dict())


@router.get('/search/', response_model=list[Person])
async def persons_list(query: str | None = Query(default=None),
                       sort:list[str]=Query(default=None),
                       filter:list[str]=Query(default=None),
                       from_:int=None, page_size=None,
                       person_service: PersonService = Depends(get_person_service)) -> list:
    """sort must be json-encoded list. An example:
    http://127.0.0.1:8000/api/v1/persons/search/?query=William%20Po?sort=name.raw&sort=...
    http://127.0.0.1:8000/api/v1/persons/search/?query=William%20Po?filter=Po Chien Chin&filter=...
    """
    persons = await person_service.get_persons_by_query(query,
                                                        from_, page_size,
                                                        sort, filter)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='nothing found')
    return [Person(**f.dict()) for f in persons]