from typing import Any, Iterable

from common import indent


def indent_entity(entity: Any) -> str:
    """indent an entity and add trailing newline

    >>> indent_entity('(foo "1")')
    ' (foo "1")\\n'
    >>> indent_entity('(bar "2"\\n (baz "3")\\n)')
    ' (bar "2"\\n  (baz "3")\\n )\\n'
    """
    result = '\n'.join(indent(1, str(entity).splitlines()))
    result += '\n'
    return result


def indent_entities(entities: Iterable[Any]) -> str:
    """indent a list of entities and add a trailing newline

    >>> indent_entities(['(bar "2")', '(bar "3")'])
    ' (bar "2")\\n (bar "3")\\n'
    """
    return ''.join(map(indent_entity, entities))
