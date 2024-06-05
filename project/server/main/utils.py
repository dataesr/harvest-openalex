from jsonschema import exceptions, validate

from project.server.main.logger import get_logger

logger = get_logger(__name__)


def validate_json_schema(data: list, _schema: dict) -> bool:
    is_valid = True
    try:
        for datum in data:
            validate(instance=datum, schema=_schema)
    except exceptions.ValidationError as error:
        is_valid = False
        logger.error(error)
    return is_valid
