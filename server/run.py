"""
開発サーバーを起動するスクリプト
"""
import argparse
import os
import sys
from pathlib import Path

import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Felica gate server")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")), help="Server port")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    sys.path.insert(0, str(script_dir))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=args.port,
        reload=True,
        log_level="info"
    )
