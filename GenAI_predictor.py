import time
import random
import google.generativeai as genai

# Calibration constants (example values; adjust as needed)
P_NEUTRAL = 10.0  # Raw sensor value when stick is not loaded
P_MAX = 100.0     # Raw sensor value for max load
S_MAX = 1.5       # Maximum comfortable walking speed (m/s)
F_MAX = 200.0     # Maximum comfortable gait force (Newtons)
D_BASELINE = 0.6  # Baseline step duration (seconds)

# Test the API with a simple request
def test_gemini_api(api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Write a haiku about AI")
    print("API Test - Haiku about AI:")
    print(response.text)
    print("-" * 40)


def normalize_speed(S_raw):
    return max(0.0, min(S_raw / S_MAX, 1.0))

def normalize_force(F_raw):
    return max(0.0, min(F_raw / F_MAX, 1.0))

def normalize_duration(D_raw):
    return max(0.0, min(D_BASELINE / D_raw, 1.0))

def generate_prompt(S_norm, F_norm, D_norm, recent_trend):
    s_trend_str = ", ".join([f"{x:.2f}" for x in recent_trend['S_trend']])
    f_trend_str = ", ".join([f"{x:.2f}" for x in recent_trend['F_trend']])
    d_trend_str = ", ".join([f"{x:.2f}" for x in recent_trend['D_trend']])

    prompt = f"""
You are a walking-aid health assistant. For each input, you will receive:
  - S_norm: Gait speed normalized 0–1 = {S_norm:.2f}
  - F_norm: Gait force normalized 0–1 = {F_norm:.2f}
  - D_norm: Step duration normalized 0–1 = {D_norm:.2f}
  - recent_trend: {{
      'S_trend': [{s_trend_str}],
      'F_trend': [{f_trend_str}],
      'D_trend': [{d_trend_str}]
    }}

Your task:
1. Determine if the user is walking too fast/slow, unsteady, or placing excessive force on steps.
2. Provide a concise suggestion (one sentence) like:
   - "Consider taking a short break."
   - "Your gait speed is lower than usual; watch your footing."
   - "You've been walking with high force; try slowing your pace."
3. Optionally include the key metric(s) that triggered the advice.

Example 1:
Input:
S_norm=0.50, F_norm=0.85, D_norm=0.90,
recent_trend={{'S_trend':[0.52,0.50,0.50], 'F_trend':[0.82,0.84,0.85], 'D_trend':[0.88,0.90,0.90]}}

Output:
"You're walking with high impact—try softening your steps or taking a brief pause."

Example 2:
Input:
S_norm=0.20, F_norm=0.15, D_norm=0.50,
recent_trend={{'S_trend':[0.22,0.20,0.20], 'F_trend':[0.18,0.16,0.15], 'D_trend':[0.60,0.55,0.50]}}

Output:
"Your gait is slow and force is low—make sure you’re maintaining good posture and balance."

Now, based on the input above, provide your suggestion in plain text.
"""
    return prompt


def get_suggestion(S_raw, F_raw, D_raw, recent_readings, gemini_api_key):
    genai.configure(api_key=gemini_api_key)

    S_norm = normalize_speed(S_raw)
    F_norm = normalize_force(F_raw)
    D_norm = normalize_duration(D_raw)

    trend_dict = {
        'S_trend': [normalize_speed(x) for x in recent_readings['S_raw']],
        'F_trend': [normalize_force(x) for x in recent_readings['F_raw']],
        'D_trend': [normalize_duration(x) for x in recent_readings['D_raw']],
    }

    prompt = generate_prompt(S_norm, F_norm, D_norm, trend_dict)

    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=50,
            temperature=0.2,
        )
    )
    
    return response.text.strip()


def simulate_data():
    # Simulate raw readings for testing
    return {
        'S_raw': random.uniform(0.0, 1.8),
        'F_raw': random.uniform(50, 220),
        'D_raw': random.uniform(0.4, 1.2)
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Smart Walking Stick Suggestion Generator")
    parser.add_argument("--api_key", type=str, required=True, help="Google Gemini API key")
    args = parser.parse_args()

    # Test the API first
    test_gemini_api(args.api_key)

    # Example recent readings (last 3 values); in real use, collect real sensor data
    recent_readings = {
        'S_raw': [simulate_data()['S_raw'] for _ in range(3)],
        'F_raw': [simulate_data()['F_raw'] for _ in range(3)],
        'D_raw': [simulate_data()['D_raw'] for _ in range(3)],
    }

    # Simulate a new reading
    new_reading = simulate_data()
    suggestion = get_suggestion(
        new_reading['S_raw'],
        new_reading['F_raw'],
        new_reading['D_raw'],
        recent_readings,
        args.api_key
    )

    print("Latest Readings (raw):", new_reading)
    print("Suggestion:", suggestion)