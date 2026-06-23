import os
import pandas as pd
from dotenv import load_dotenv
from groq import Groq
import json

# --- Part 1: Environment Setup ---
# Load environment variables
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists("project.env"):
    load_dotenv("project.env")
else:
    load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
SHEET_URL = os.getenv(
    "GOOGLE_SHEET_URL",
    "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit?usp=sharing"
)

if not api_key:
    print("Error: GROQ_API_KEY not found.")
    print("Please make sure you have a file named .env with: GROQ_API_KEY=your_key_here")
    exit(1)

# Initialize Groq client
client = Groq(api_key=api_key)

# --- Part 2: Eligibility Validation ---
def check_technical_eligibility(motivation_text):
    """
    Uses Groq LLM to analyze the motivation text and determine eligibility.
    The candidate is qualified if they meet AT LEAST ONE of the following:
    1. Technical background
    2. AI interest
    3. Automation interest
    Returns a tuple: (is_qualified, reason)
    """
    prompt = f"""
    Analyze the following motivation text from a student applying for a tech event.
    The candidate should be marked as QUALIFIED if they demonstrate AT LEAST ONE of these criteria:
    - Technical background (any programming or tech experience).
    - AI interest (genuine interest in learning or using AI).
    - Automation interest (interest in automating tasks or workflows).

    Motivation Text: "{motivation_text}"

    Respond ONLY in the following JSON format:
    {{
        "qualified": true/false,
        "reason": "A brief explanation in English mentioning which criteria they met (Technical background, AI interest, or Automation interest)"
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical recruiter. You qualify candidates if they show EITHER technical background, AI interest, OR automation interest. Respond only in JSON and in English."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )

        result = json.loads(chat_completion.choices[0].message.content)
        return result.get("qualified", False), result.get("reason", "No specific reason provided")
    except Exception as e:
        return False, f"Error in technical analysis: {str(e)}"


def validate_eligibility(df):
    """
    Validates applicants based on Technical background, AI interest, OR Automation interest.
    GPA is not a mandatory requirement for eligibility.
    """
    eligibility_list = []
    reason_list = []

    print("Starting eligibility validation...")

    for index, row in df.iterrows():
        name = row['name']
        motivation = str(row['motivation'])

        is_qualified, tech_reason = check_technical_eligibility(motivation)

        if is_qualified:
            eligibility_list.append("Accepted")
            reason_list.append(f"Qualified: {tech_reason}")
            print(f"Processed {name}: Accepted")
        else:
            eligibility_list.append("Rejected")
            reason_list.append(f"Rejected: {tech_reason}")
            print(f"Processed {name}: Rejected")

    df['Eligibility'] = eligibility_list
    df['Reason'] = reason_list
    return df


# --- Part 3: Scoring System ---
def score_motivation_quality(motivation_text):
    """
    Uses Groq AI to score the quality of the motivation text.
    Returns a score from 0-100 based on:
    - Clarity and coherence
    - Specificity and detail
    - Passion and enthusiasm
    - Relevance to tech/AI/automation
    """
    prompt = f"""
    Analyze the following motivation text from a student applying for a tech event.
    Score the quality of their motivation on a scale of 0-100 based on:
    1. Clarity and coherence (25 points)
    2. Specificity and detail (25 points)
    3. Passion and enthusiasm (25 points)
    4. Relevance to tech/AI/automation (25 points)

    Motivation Text: "{motivation_text}"

    Respond ONLY in the following JSON format:
    {{
        "score": <number between 0-100>,
        "breakdown": {{
            "clarity": <0-25>,
            "specificity": <0-25>,
            "passion": <0-25>,
            "relevance": <0-25>
        }},
        "brief_feedback": "One sentence explaining the score"
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert evaluator of student applications. Score motivation texts objectively and fairly. Respond only in JSON."
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )

        result = json.loads(chat_completion.choices[0].message.content)
        return result.get("score", 50), result.get("brief_feedback", "No feedback provided")
    except Exception as e:
        print(f"Error scoring motivation: {str(e)}")
        return 50, "Error in scoring"


def calculate_comprehensive_score(df):
    """
    Calculates a comprehensive score for each applicant based on:
    - GPA Score (30% weight): Normalized GPA out of 5.0
    - Motivation Quality Score (40% weight): AI-analyzed quality score
    - Eligibility Bonus (30% weight): Bonus points for being accepted

    Final Score Range: 0-100
    """
    print("\n" + "=" * 60)
    print("Starting Comprehensive Scoring System...")
    print("=" * 60)

    gpa_scores = []
    motivation_scores = []
    motivation_feedback = []
    eligibility_scores = []
    total_scores = []

    WEIGHT_GPA = 0.30
    WEIGHT_MOTIVATION = 0.40
    WEIGHT_ELIGIBILITY = 0.30

    print(f"\nScoring Weights:")
    print(f"  - GPA: {WEIGHT_GPA * 100}%")
    print(f"  - Motivation Quality: {WEIGHT_MOTIVATION * 100}%")
    print(f"  - Eligibility Bonus: {WEIGHT_ELIGIBILITY * 100}%")
    print("\n" + "-" * 60)

    for index, row in df.iterrows():
        name = row['name']
        gpa = float(row['gpa'])
        motivation = str(row['motivation'])
        eligibility = row['Eligibility']

        gpa_score = (gpa / 5.0) * 100
        motivation_score, feedback = score_motivation_quality(motivation)
        eligibility_score = 100 if eligibility == "Accepted" else 0

        total_score = (
            (gpa_score * WEIGHT_GPA) +
            (motivation_score * WEIGHT_MOTIVATION) +
            (eligibility_score * WEIGHT_ELIGIBILITY)
        )

        total_score = round(total_score, 2)
        gpa_score = round(gpa_score, 2)

        gpa_scores.append(gpa_score)
        motivation_scores.append(motivation_score)
        motivation_feedback.append(feedback)
        eligibility_scores.append(eligibility_score)
        total_scores.append(total_score)

        print(f"\n{name}:")
        print(f"  GPA Score: {gpa_score}/100 (GPA: {gpa}/5.0)")
        print(f"  Motivation Score: {motivation_score}/100")
        print(f"  Feedback: {feedback}")
        print(f"  Eligibility Score: {eligibility_score}/100 ({eligibility})")
        print(f"  TOTAL SCORE: {total_score}/100")

    df['GPA_Score'] = gpa_scores
    df['Motivation_Score'] = motivation_scores
    df['Motivation_Feedback'] = motivation_feedback
    df['Eligibility_Score'] = eligibility_scores
    df['Total_Score'] = total_scores

    df['Rank'] = df['Total_Score'].rank(ascending=False, method='min').astype(int)

    print("\n" + "=" * 60)
    print("Scoring Complete!")
    print("=" * 60)

    return df


# --- Part 4: Organizer Summary & Human-in-the-Loop Review ---
def create_organizer_summary(df_sorted, top_n=10):
    summary_df = df_sorted.head(top_n)[
        ['Rank', 'name', 'Total_Score', 'GPA_Score',
         'Motivation_Score', 'Eligibility']
    ]

    summary_text = "Top Candidates Summary:\n\n"

    for _, row in summary_df.iterrows():
        summary_text += (
            f"Rank {row['Rank']} — {row['name']}\n"
            f"  • Total Score: {row['Total_Score']}\n"
            f"  • GPA Score: {row['GPA_Score']}\n"
            f"  • Motivation Score: {row['Motivation_Score']}\n"
            f"  • Status: {row['Eligibility']}\n\n"
        )

    return summary_text


def format_message_to_organizer(summary_text):
    return f"""
Dear Organizer,

The applicant evaluation process has been completed.

{summary_text}

Reply with:

APPROVED — finalize
REJECTED — request changes

GDSC Automation System
"""


def organizer_review_loop(df_sorted):
    """
    Human-in-the-loop organizer review.
    """
    while True:
        summary = create_organizer_summary(df_sorted)
        message = format_message_to_organizer(summary)

        print("\n" + "=" * 60)
        print("MESSAGE TO ORGANIZER")
        print("=" * 60)
        print(message)

        decision = input(
            "\nEnter decision (APPROVE / EDIT / REJECT): "
        ).strip().upper()

        if decision == "APPROVE":
            print("✓ Organizer approved final results.")
            return df_sorted, True

        elif decision == "EDIT":
            print("Opening organizer editing interface...")
            df_sorted = organizer_edit_interface(df_sorted)

        elif decision == "REJECT":
            print("Organizer rejected the batch.")
            return df_sorted, False

        else:
            print("Invalid response.")


def organizer_edit_interface(df_sorted):
    """
    Allows the organizer to manually adjust candidate status or rank.
    Returns the modified dataframe.
    """
    df_sorted = df_sorted.copy()

    while True:
        print("\nOrganizer Edit Menu:")
        print("1 — Change candidate Eligibility")
        print("2 — Adjust Total Score")
        print("3 — View top candidates")
        print("0 — Finish editing")

        choice = input("Select option: ").strip()

        if choice == "1":
            name = input("Enter candidate name: ").strip()

            if name not in df_sorted['name'].values:
                print("Candidate not found.")
                continue

            new_status = input("Enter new status (Accepted/Rejected): ").strip()

            df_sorted.loc[df_sorted['name'] == name, 'Eligibility'] = new_status
            print("Eligibility updated.")

        elif choice == "2":
            name = input("Enter candidate name: ").strip()

            if name not in df_sorted['name'].values:
                print("Candidate not found.")
                continue

            try:
                new_score = float(input("Enter new Total Score: "))
                df_sorted.loc[df_sorted['name'] == name, 'Total_Score'] = new_score
                print("Score updated.")
            except ValueError:
                print("Invalid number.")

        elif choice == "3":
            print(df_sorted[['Rank', 'name', 'Total_Score', 'Eligibility']]
                  .sort_values('Total_Score', ascending=False)
                  .head(10)
                  .to_string(index=False))

        elif choice == "0":
            print("Editing finished.")
            break

        else:
            print("Invalid option.")

    df_sorted = df_sorted.sort_values('Total_Score', ascending=False)
    df_sorted['Rank'] = df_sorted['Total_Score'].rank(
        ascending=False, method='min'
    ).astype(int)

    return df_sorted


def main():
    print("=" * 60)
    print("GDSC Applicant Processing System")
    print("=" * 60)
    print("\nFetching data from Google Sheets...")
    csv_url = SHEET_URL.replace("/edit?usp=sharing", "/export?format=csv")

    try:
        df = pd.read_csv(csv_url)
        print(f"Successfully loaded {len(df)} applicants")
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    print("\n" + "=" * 60)
    df_validated = validate_eligibility(df)

    df_scored = calculate_comprehensive_score(df_validated)

    print("\n" + "=" * 60)
    print("FINAL RANKINGS")
    print("=" * 60)

    df_sorted = df_scored.sort_values('Total_Score', ascending=False)

    df_sorted, approved = organizer_review_loop(df_sorted)

    if not approved:
        print("Process ended without approval.")
        return

    print("\nTop 5 Candidates:")
    print("-" * 60)
    top_columns = ['Rank', 'name', 'Total_Score', 'GPA_Score', 'Motivation_Score', 'Eligibility']
    print(df_sorted[top_columns].head().to_string(index=False))

    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"Total Applicants: {len(df_scored)}")
    print(f"Accepted: {len(df_scored[df_scored['Eligibility'] == 'Accepted'])}")
    print(f"Rejected: {len(df_scored[df_scored['Eligibility'] == 'Rejected'])}")
    print(f"\nAverage Total Score: {df_scored['Total_Score'].mean():.2f}")
    print(f"Highest Score: {df_scored['Total_Score'].max():.2f}")
    print(f"Lowest Score: {df_scored['Total_Score'].min():.2f}")

    output_file = "validated_applicants_with_scores.csv"
    df_sorted.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\nResults saved to '{output_file}'")
    print("=" * 60)


if __name__ == "__main__":
    main()
