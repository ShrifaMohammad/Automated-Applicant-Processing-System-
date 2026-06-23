# GDSC Applicant Processing System

An AI-powered candidate evaluation pipeline built for **Google Developer Student Clubs (GDSC)** event applications. It automates eligibility screening, scores candidate motivation using an LLM, and runs a human-in-the-loop review before finalizing rankings.

## What it does

1. **Fetches applicant data** directly from a Google Sheet (no manual export needed)
2. **Validates eligibility** — uses [Groq](https://groq.com/)'s `llama-3.3-70b-versatile` model to read each applicant's motivation text and accept them if they show *any* of: a technical background, genuine AI interest, or automation interest
3. **Scores candidate quality** with a weighted formula:
   - GPA Score — 30%
   - AI-evaluated Motivation Quality — 40%
   - Eligibility Bonus — 30%
4. **Ranks all candidates** by total score
5. **Human-in-the-loop review** — prints a summary for the event organizer, who can `APPROVE`, `EDIT` (manually override eligibility/scores), or `REJECT` the batch before it's finalized
6. **Exports final results** to a CSV file

## Why I built it

Manually screening and scoring dozens of event applications is slow and inconsistent between reviewers. This pipeline standardizes the process — using an LLM to fairly evaluate open-ended motivation text instead of just GPA — while still keeping a human organizer in control of the final decision.

## Tech stack

- Python, pandas
- [Groq API](https://groq.com/) (`llama-3.3-70b-versatile`)
- Google Sheets (as the live data source)

## Setup

1. Clone this repo
   ```bash
   git clone https://github.com/YOUR_USERNAME/gdsc-applicant-processing.git
   cd gdsc-applicant-processing
   ```
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your own values
   ```bash
   cp .env.example .env
   ```
   - `GROQ_API_KEY` — get a free key at [console.groq.com](https://console.groq.com/)
   - `GOOGLE_SHEET_URL` — link to your applicant Google Sheet (must be shared as "Anyone with the link can view")

Your Google Sheet needs these columns: `name`, `gpa`, `motivation`.

4. Run it
   ```bash
   python main.py
   ```

## Sample output

See [`sample_output.csv`](sample_output.csv) for an example of the final ranked results from a test run with 10 candidates.

| Rank | Name | Total Score | GPA Score | Motivation Score | Eligibility |
|---|---|---|---|---|---|
| 1 | Sara Ahmed | 69.0 | 90.0 | 30 | Accepted |
| 2 | Noor Ali | 68.0 | 100.0 | 20 | Accepted |
| 3 | Lama Saleh | 66.2 | 94.0 | 20 | Accepted |

## Team

Built as a group project — data integration, eligibility validation, and scoring/ranking logic were split across team members.

## What I'd improve next

- Add automated tests for the scoring logic
- Cache LLM responses to avoid re-scoring on reruns
- Add a simple web UI for the organizer review step instead of a CLI prompt
