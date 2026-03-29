# MediQuery AI

A REST API that converts plain-English clinical questions into parameterized SQL, executes them against a patient database, and returns structured JSON. Built with a pluggable NLP layer designed for LLM integration.

## Architecture

```
POST /query  { "question": "How many patients are admitted?" }
     ↓
NLP Parser (rule-based → swap for LLM at nlp_parser.parse())
     ↓
SQL Generator (parameterized, injection-safe)
     ↓
SQLite (dev) / PostgreSQL or MySQL (prod via DATABASE_URL)
     ↓
{ question, generated_sql, results, result_count }
```

## Quickstart

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000/docs
```

## Docker

```bash
docker build -t mediquery-ai .
docker run -p 8000:8000 mediquery-ai
```

## Example

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many patients are currently admitted?"}'

{
  "question": "How many patients are currently admitted?",
  "generated_sql": "SELECT COUNT(*) AS count FROM patients WHERE status = 'admitted'",
  "results": [{"count": 6}],
  "result_count": 1
}
```

## Supported Questions
| Question | SQL Generated |
|----------|--------------|
| How many patients are admitted? | COUNT WHERE status='admitted' |
| List all patients in Cardiology | SELECT WHERE department='Cardiology' |
| Patients with Hypertension | SELECT WHERE diagnosis LIKE '%Hypertension%' |
| What is the average age? | AVG(age) |
| Who is the oldest patient? | ORDER BY age DESC LIMIT 1 |

## Swapping in an LLM
Replace the body of `nlp_parser.parse()` with any LLM API call. The router and database layer require zero changes.

## API Reference
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/query` | NL question → SQL → JSON |
| GET | `/patients` | List patients (filter by status/dept) |
| GET | `/patients/stats` | Aggregate dashboard stats |
| GET | `/patients/{id}` | Single patient by ID |

## Stack
Python 3.11 · FastAPI · SQLite · Pydantic · Docker
