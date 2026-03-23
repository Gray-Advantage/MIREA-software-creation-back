from pydantic import BaseModel


class ErrorDetail(BaseModel):
    detail: str

    model_config = {
        "json_schema_extra": {
            "examples": [{"detail": "Описание ошибки"}],
        },
    }


R_401: dict = {401: {"model": ErrorDetail, "description": "Не авторизован"}}
R_403: dict = {403: {"model": ErrorDetail, "description": "Доступ запрещён"}}
R_404: dict = {404: {"model": ErrorDetail, "description": "Ресурс не найден"}}
R_409: dict = {409: {"model": ErrorDetail, "description": "Конфликт данных"}}
R_400: dict = {400: {"model": ErrorDetail, "description": "Некорректный запрос"}}

ADMIN = {**R_401, **R_403}
ADMIN_NOT_FOUND = {**ADMIN, **R_404}
EMPLOYEE = {**R_401, **R_403}
