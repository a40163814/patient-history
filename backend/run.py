import uvicorn
import os
import sys

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_root)

if __name__ == "__main__":
    from backend.app.core.config import settings
    app_dir = os.path.join(backend_root, "backend", "app")
    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.APP_ENV == "development"),
        reload_dirs=[app_dir] if settings.APP_ENV == "development" else None
    )
