DEFAULT_USER_ID = "00000000-0000-0000-0000-000000000001"
DEFAULT_USER = {
    "id": DEFAULT_USER_ID,
    "email": "default@local.dev",
}


async def get_current_user() -> dict:
    return DEFAULT_USER


async def get_current_user_id() -> str:
    return DEFAULT_USER_ID
