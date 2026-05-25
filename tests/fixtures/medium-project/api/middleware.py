"""Request middleware."""


def cors_middleware(request, handler):
    response = handler(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def auth_middleware(request, handler):
    if not request.headers.get("Authorization"):
        return {"error": "unauthorized"}, 401
    return handler(request)
