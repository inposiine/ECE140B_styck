# Smart Walking Stick Suggestion Generator

A Python script that uses Google’s Gemini LLM to provide real-time, data-driven walking tips based on three normalized gait parameters:
- **Gait Speed** (m/s)
- **Gait Force** (Newtons)
- **Step Duration** (seconds)

This README explains how the script works, how to set it up, and how it applies to our smart walking stick startup project.

---

## 📘 Table of Contents

1. [Project Overview](#project-overview)  
2. [Prerequisites](#prerequisites)  
3. [Installation](#installation)  
4. [Calibration Constants](#calibration-constants)  
5. [How It Works](#how-it-works)  
   - [1. Simulating or Reading Sensor Data](#1-simulating-or-reading-sensor-data)  
   - [2. Normalization Functions](#2-normalization-functions)  
   - [3. Prompt Generation](#3-prompt-generation)  
   - [4. Calling Gemini](#4-calling-gemini)  
   - [5. Interpreting the Suggestion](#5-interpreting-the-suggestion)  
6. [Usage](#usage)  
7. [Applying to the Startup Project](#applying-to-the-startup-project)  
   - [Real-World Sensor Integration](#real-world-sensor-integration)  
   - [Calibrating for Individual Users](#calibrating-for-individual-users)  
   - [Possible Extensions](#possible-extensions)  
8. [License & Acknowledgements](#license--acknowledgements)

---

## Project Overview

Our smart walking stick collects three raw sensor readings on each step:
1. **Gait Speed** (`S_raw`)  
2. **Gait Force** (`F_raw`)  
3. **Step Duration** (`D_raw`)  

These raw values are normalized according to user-specific calibration constants (e.g., maximum comfortable speed or force, baseline step duration). The normalized values (`S_norm`, `F_norm`, `D_norm`) plus their recent trends are fed into a few-shot prompt. Google’s Gemini LLM processes this prompt and returns a concise, human-friendly suggestion, such as:

> “Your gait speed is lower than usual; watch your footing.”  
> “You’re walking with high impact—try softening your steps or taking a brief pause.”

This approach lets us offload complex “if-then” logic to the LLM, making it easy to iterate on advice style without rewriting sensor code.

---

## Prerequisites

1. **Python 3.8+**  
2. **Google Gemini API access** (API key with `genai` library enabled)  
3. **`google-generativeai` Python package**  
   ```bash
   pip install google-generativeai
