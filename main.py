# Production ASGI entrypoint — render.yaml runs `uvicorn main:app`. Not dead code;
# a linter will call this unused. It is not.
from saas.app.main import app  # noqa: F401
