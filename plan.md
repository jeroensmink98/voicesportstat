Here’s a **one-page plan** for your soccer event recording app using **SvelteKit + FastAPI + Azure services**.

---

# ⚽ Voice-to-Structured-Events App – One Page Plan

## 🎯 Goal

Capture live **voice commentary** during a soccer match, extract structured events (pass, shot, goal, etc.), and store them in a database for dashboards & analysis.

---

## 🏗️ Architecture Overview

```
[SvelteKit Client] → WebSocket → [FastAPI Gateway] 
      ↓                             ↓
  Stream Audio                 Publish to Queue (Azure Service Bus)
                                    ↓
                          [Workers (FastAPI/Celery/Azure Functions)]
                          ├─ STT Worker → TranscriptQueue
                          ├─ NLP Worker → EventQueue
                          └─ Event Processor → Database
                                    ↓
                           [API + Live Dashboard]
```

---

## 🔑 Components

### 1. **Frontend – SvelteKit**

* Mic capture (`MediaRecorder API`).
* Stream chunks over **WebSocket** to FastAPI.
* UI for live match dashboard.

### 2. **Backend – FastAPI**

* **WebSocket endpoint**: receives audio chunks.
* Stores audio (Azure Blob Storage).
* Publishes metadata message → `AudioQueue` (Service Bus).

### 3. **Workers**

* **STT Worker**

  * Reads from `AudioQueue`.
  * Calls Azure Speech → transcript.
  * Publishes → `TranscriptQueue`.

* **NLP Worker**

  * Reads transcript.
  * Calls Azure OpenAI → structured events JSON.
  * Publishes → `EventQueue`.

* **Event Processor**

  * Reads events.
  * Validates & enriches (match time, player names).
  * Writes to DB (`MatchEvents`).

### 4. **Database (Azure SQL or CosmosDB)**

Schema (flexible for dynamic events):

```sql
MatchEvents(
  id INT PRIMARY KEY,
  match_id INT,
  event_time TIME,
  event_type VARCHAR(50),
  player_from VARCHAR(100) NULL,
  player_to VARCHAR(100) NULL,
  description TEXT,
  metadata JSONB
)
```

### 5. **Dashboard**

* Query events API (FastAPI REST/GraphQL).
* Show timeline & stats in real time.

---

## 🌩️ Azure Services

* **Azure Service Bus** → queues (`AudioQueue`, `TranscriptQueue`, `EventQueue`).
* **Azure Speech-to-Text** → transcription.
* **Azure OpenAI** → structured event extraction.
* **Azure SQL** or **CosmosDB** → event storage.
* **Azure Blob Storage** → raw audio storage.

---

## 🚀 MVP Roadmap

1. **Phase 1 (MVP)**

   * SvelteKit client streams audio → FastAPI WebSocket.
   * STT Worker (Azure Speech) → transcript → DB.
   * Simple dashboard showing transcript log.

2. **Phase 2**

   * Add NLP Worker (Azure OpenAI) → structured events.
   * Store JSON in DB.
   * Dashboard shows structured events (pass, shot, goal).

3. **Phase 3**

   * Add match context engine (state tracking).
   * Parent/child event grouping (corner → header → goal).
   * Real-time push to dashboard (WebSockets).

---

👉 This keeps the system modular: each worker can fail/retry independently, queues smooth out spikes, and the app scales per match.

---

Do you want me to also draft a **minimal FastAPI WebSocket endpoint** example that receives mic audio from SvelteKit and pushes it to Service Bus?
