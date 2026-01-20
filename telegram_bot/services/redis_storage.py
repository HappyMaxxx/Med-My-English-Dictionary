from aiogram.fsm.storage.redis import RedisStorage

storage = RedisStorage.from_url("redis://redis:6379/0")

async def store_user_token(chat_id: int, token: str):
    await storage.redis.set(f"user_token:{chat_id}", token)

async def get_user_token(chat_id: int) -> str | None:
    token = await storage.redis.get(f"user_token:{chat_id}")
    if token:
        return token.decode()
    return None
