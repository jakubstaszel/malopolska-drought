import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start our FastAPI.")
    parser.add_argument("--development", "-dev", action="store_true")
    parser.add_argument("--prod", "-prod", action="store_true")

    args = parser.parse_args()

    if args.development:
        uvicorn.run(
            "src.api.app:app",
            host="127.0.0.2",
            port=8000,
            reload=True,
            log_level="debug",
        )
    else:
        uvicorn.run(
            "src.api.app:app",
            host="127.0.0.2",
            port=8000,
            reload=False,
            log_level="info",
            debug=True,
        )
