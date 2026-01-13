SAMPLE_SWAGGER_API = {
    "openapi": "3.1.0",
    "info": {"title": "Title", "description": "Title", "version": "1.0.0"},
    "servers": [{"url": "https"}],
    "paths": {
        "/": {
            "get": {
                "operationId": "rootRedirect",
                "tags": ["Docs"],
                "summary": "Redirect root path to Swagger UI",
                "responses": {
                    "302": {
                        "description": "Redirects to /doc",
                        "headers": {
                            "Location": {
                                "description": "URL to redirect",
                                "schema": {
                                    "type": "string",
                                    "example": "/doc",
                                },
                            }
                        },
                    }
                },
            }
        },
        "/ping": {
            "get": {
                "operationId": "pong",
                "tags": ["Health"],
                "summary": "Check if the server is alive",
                "responses": {
                    "200": {
                        "description": "A message showing that the server is alive",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "string",
                                    "example": "pong",
                                }
                            }
                        },
                    }
                },
            }
        },
        "/health/bucket": {
            "get": {
                "operationId": "healthBucketCheck",
                "tags": ["Health"],
                "summary": "Check bucket health",
            }
        },
        "/health/email": {
            "get": {
                "operationId": "sendHealthEmail",
                "tags": ["Health"],
                "summary": "Send health check email",
            }
        },
        "/health/message": {
            "get": {
                "operationId": "triggerDummyEvents",
                "tags": ["Health"],
                "summary": "Trigger dummy health check events",
            }
        },
        "/health/db": {
            "get": {
                "operationId": "healthDbCheck",
                "tags": ["Health"],
                "summary": "Health check for the database",
            }
        },
    },
    "components": {
        "schemas": {
            "ErrorResponse": {"type": "object"},
            "DateTime": {"type": "string"},
            "UUID": {"type": "string"},
            "Dummy": {"type": "object"},
        }
    },
}
