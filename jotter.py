import sys


async def coro():
    pass


t = type(coro)


print(f"Python {sys.version_info[:2]}: {t} {isinstance(t, type)}")
