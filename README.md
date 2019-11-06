# LibrePCB Library Parts Generator Scripts

[![Travis Build Status](https://travis-ci.org/LibrePCB/librepcb-parts-generator.svg?branch=master)](https://travis-ci.org/LibrePCB/librepcb-parts-generator)

This is a collection of Python 3 based scripts to generate parts for the
[LibrePCB](https://librepcb.org) default library.


## Requirements

- Python 3.5+
- For testing and type checking: See `requirements.txt`


## Introduction / Concepts

While it's easy to create a one-off script to generate LibrePCB library
elements, you quickly run into some issues: 

- If your output format does not match the canonical format used in LibrePCB,
  your elements will be reformatted when opening them in the LibrePCB library
  editor
- When using random UUIDs, regenerating the library element with adjusted
  parameters will result in a completely new library element (since it gets a
  new UUID)
- String concatenation results in messy and hard-to-modify generator scripts

This project uses a set of **entity wrapper types** that can be used to
generate the corresponding library element. It also includes **helpers for
things like number formatting** as well as **a caching system for stable
UUIDs**.

### Entity Types

The entity types can be imported from the `entities` module. Unfortunately
there's no API documentation so far, so you'll have to take a look at the
[source code](https://github.com/LibrePCB/librepcb-parts-generator/tree/master/entities)
or rely on IDE autocompletion for now.

For example, instead of writing a symbol generator like this:

```python
lines = []

lines.append('(librepcb_symbol {}'.format(uuid4()))
lines.append(' (name "{}")'.format("Demo Symbol"))
lines.append(' (description "{}")'.format("A simple symbol with two pins."))
lines.append(' (keywords "{}")'.format(','.join(["simple", "demo"]))
# ...
lines.append(' (pin {} (name "1")'.format(uuid4()))
lines.append('  (position -10.16 0.0) (rotation 0.0) (length 2.54)')
lines.append(' )')
lines.append(' (pin {} (name "2")'.format(uuid4()))
lines.append('  (position 10.16 0.0) (rotation 180.0) (length 2.54)')
lines.append(' )')
# ...
print('\n'.join(lines))
```

...you can do something like this:

```python
from entities.common import Name, Description, Keywords, Position, Rotation, Length
from entities.symbol import Symbol, Pin

# Create symbol
symbol = Symbol(
    str(uuid4()),
    Name("Demo Symbol"),
    Description("A simple symbol with two pins."),
    Keywords("simple,demo"),
    # ...
)

# Add pins
symbol.add_pin(Pin(str(uuid4()), Name("1"), Position(-10.16, 0.0), Rotation(0.0), Length(2.54)))
symbol.add_pin(Pin(str(uuid4()), Name("2"), Position(10.16, 0.0), Rotation(180.0), Length(2.54)))

# ...

# Print library element
print(str(symbol))
```

This is much easier to write, read and maintain. Furthermore, since the
entities are fully type annotated, you even benefit from type checking using
[mypy](http://mypy-lang.org/)!

### UUID Caching

In every generator script, you should first initialize the UUID cache:

```python
from common import init_cache, save_cache

# Initialize UUID cache, load any pre-existing entries
uuid_cache_file = 'uuid_cache_chip.csv'
uuid_cache = init_cache(uuid_cache_file)
```

The cache is a simple in-memory dictionary. The `init_cache` function will load
any pre-existing cache entries from the file system.

Every generated UUID should have its own stable lookup key. Depending on the
script, a wrapper function that generates missing UUIDs on the fly might make
sense:

```python
def uuid(category: str, full_name: str, identifier: str, create: bool = True) -> str:
    """
    Return a UUID for the specified element.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        full_name:
            For example "RESC3216X65".
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        if not create:
            raise ValueError('Unknown UUID: {}'.format(key))
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]

pad_uuids = [
    uuid('pkg', 'RESC3216X65', 'pad-1'),
    uuid('pkg', 'RESC3216X65', 'pad-2'),
]
```

At the end of the generator script, all cached UUIDs should be persisted to the
file system.

```python
# Persist the cache to the file system
save_cache(uuid_cache_file, uuid_cache)
```


## Testing

Run the tests using pytest:

    $ pytest


## License

MIT, see `LICENSE` file
