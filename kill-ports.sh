#!/bin/bash
# Kill processes using ports 8000 (backend) and 5173-5180 (frontend/Vite fallbacks)

echo "Stopping processes on ports 8000 and 5173-5180..."

for port in 8000 5173 5174 5175 5176 5177 5178 5179 5180; do
  if lsof -ti:$port >/dev/null 2>&1; then
    echo "  Killing process on port $port..."
    lsof -ti:$port | xargs kill -9 2>/dev/null
    echo "  Port $port freed"
  fi
done

echo "Done. You can now run ./start-all.sh or start the servers manually."
