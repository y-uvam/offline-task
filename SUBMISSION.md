# Product Engineering Challenge Submission

## Candidate

- **Name:** Yuvam
- **Email:** yuvamdhanda975@gmail.com
- **GitHub:** https://github.com/y-uvam
- **Selected problem:** Problem 2: Offline-Mobile Conversation
- **Demo video:** https://drive.google.com/file/d/1g73jFO67VrVXMAzGpowNIkQp7PS2Y8Tn/view?usp=sharing

## Run the project

**Prerequisites:**

- Node.js >= 22.0.0
- Python >= 3.9
- React Native environment setup for Android or iOS

**Start the Backend:**

```bash
cd backend

# Option A: Using uv (Fastest)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Option B: Using standard venv / pip
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Start the Frontend:**

```bash
cd frontend
npm install
npm run android # or npm run ios
```

*Note: If running on a physical Android device over USB, run `adb reverse tcp:8000 tcp:8000` to forward localhost traffic.*

## Run the tests

**Backend Tests:**

```bash
cd backend
uv run pytest -v  # or pytest -v with activated venv
```

**Frontend Tests:**

```bash
cd frontend
npm test
```

## Acceptance scenarios and verification

- **AC1: Offline send** - Supported. Turn off Wi-Fi / Airplane mode on the device, then create an incident. It instantly appears with a pending status icon.
- **AC2: Force-close durability** - Supported. Create incidents offline, force close the app, and reopen. All incidents are loaded from `AsyncStorage` and persist across restarts.
- **AC3: Reconnection synchronization** - Supported. Turn Wi-Fi back on. The connection indicator transitions to "Back online", and the sync engine automatically flushes the queue in FIFO order to the server.
- **AC4: Temporary failure and retry** - Supported. If the server is temporarily unavailable or returns an error, incidents remain pending and retry on reconnection.
- **AC5: Uncertain acknowledgement (Idempotency)** - Supported. Each incident uses a stable client-generated UUID as an idempotency key. If an ACK is lost or a request is retried, the backend safely deduplicates the request and returns the existing record with `was_duplicate: true`.

**Verification Benchmark:**

To run the verification benchmark, follow these steps:

1. Ensure both frontend and backend are running.
2. Put the mobile device / simulator in Airplane mode or turn off Wi-Fi.
3. Create 10 incidents rapidly using the form.
4. Reload / force close the app and reopen.
5. Verify all 10 incidents persist in pending state.
6. Re-enable Wi-Fi / disable Airplane mode.
7. Watch the queue automatically sync to the server and update each incident status.
8. Verify backend state: Navigate to `http://localhost:8000/api/incidents` in your browser.

**Observed Results:** The backend endpoint returns exactly 10 incidents with 0 duplicates, with matching `client_id`s.

## Architecture and data flow

The architecture separates concerns into distinct layers:

1. **UI Layer (`IncidentStore` context & Screens):** Manages what the user sees. Unaware of network internals.
2. **Persistence Layer (`incidentStorage.ts`):** Serializes the entire queue to durable `AsyncStorage`. Ensures crash recovery by converting `SYNCING` states back to `PENDING` upon load.
3. **Synchronization Layer (`syncEngine.ts`):** A queue processor that listens to connectivity changes. It pulls pending incidents one-by-one in FIFO order and manages state transitions (`PENDING -> SYNCING -> SYNCED/FAILED`) with exponential backoff.
4. **Backend Idempotency (`store.py` & `routes.py`):** Uses the stable `client_id` provided by the app as an idempotency key. A concurrent dict guards against duplicates.

## Technology choices

**Frontend:** React Native (bare workflow). It provides a fast way to build a real native prototype. `@react-native-async-storage/async-storage` was used for persistence as it's the standard, lightweight KV store for RN, perfectly suited for a small prototype. `@react-native-community/netinfo` handles connectivity.

**Backend:** FastAPI + Python. FastAPI is exceptionally fast to build prototypes with and features built-in Pydantic validation which perfectly matches the required strict data models.

## Important decisions

1. **Client-generated UUIDs as Idempotency Keys:** By generating UUIDs on the client at creation time, the backend can safely deduplicate incoming requests. This eliminates the edge case where an incident is created on the server but the client never receives the response (AC5).
2. **Single-threaded Queue Processor:** The `syncEngine` uses a simple `while (true)` loop with a mutex flag (`isSyncing`) to process items one at a time. This guarantees strict FIFO ordering and prevents race conditions from concurrent sync attempts (e.g., if connectivity flaps).

## Assumptions and limitations

- **Storage Scaling:** The current implementation serializes the entire array of incidents into a single AsyncStorage key. This is fine for a prototype (handling hundreds of items easily), but would cause performance issues with thousands.
- **Background Sync:** The app does not sync when fully terminated in the background. It relies on the user reopening the app to resume the queue.

## Production and scale

If this needed to scale to thousands of pending incidents or larger payloads:

1. **Database:** Replace AsyncStorage with a local SQLite database (e.g., WatermelonDB). This allows for indexed querying (e.g., `SELECT * FROM incidents WHERE status = 'pending' ORDER BY created_at LIMIT 50`) rather than loading the whole array into memory.
2. **Batching:** The `syncEngine` currently sends one incident per HTTP request. In production, it should batch incidents (e.g., arrays of 50) to minimize network overhead and battery drain.
3. **Background Tasks:** Implement WorkManager (Android) and BGTaskScheduler (iOS) to process the queue in the background when connectivity returns, even if the app isn't active.

## AI usage

I used Claude Opus and Gemini to assist with boilerplate generation, testing, and implementation plan formulation. All architecture decisions, specifically around idempotency and the state machine transitions, were explicitly guided and reviewed by me.

## Credibility note

- **The problem it solved:** Re-architecting a legacy data ingestion pipeline that was losing events during high-traffic spikes.
- **Your personal contribution:** Designed and implemented a durable queueing system using Kafka and Redis to buffer incoming events before writing to the primary database.
- **The scale or operational complexity involved:** Processed over 10,000 events per second during peak hours with strict ordering requirements and zero-data-loss guarantees.
- **One difficult engineering or product decision:** Decided to drop strict global ordering in favor of partition-key ordering (by customer ID). Global ordering was bottlenecking throughput, and product analysis showed that only events _within a single customer's context_ needed strict ordering.
