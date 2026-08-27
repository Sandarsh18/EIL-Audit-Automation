#!/bin/bash
cd backend
source ../venv/bin/activate
export PYTHONPATH=.
uvicorn app.main:app --port 8000 &
UVICORN_PID=$!
cd ../frontend
sleep 3
npx playwright test e2e/workflow.spec.ts
TEST_EXIT_CODE=$?
kill $UVICORN_PID
exit $TEST_EXIT_CODE
