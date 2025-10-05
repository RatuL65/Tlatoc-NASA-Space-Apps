# 🚀 Project Tlatoc: Your Personal Climate Assistant

**Team Tlatoc | NASA Space Apps Challenge 2025**

## Our Mission

In a world of changing climates, planning outdoor activities can feel like a gamble. **Project Tlatoc** is a conversational climate assistant designed to transform that uncertainty into confidence. By leveraging 30 years of NASA's POWER project data, Tlatoc provides hyper-localized, personalized climate insights to help users plan everything from a hike to a beach day, anywhere on Earth.

Our goal is not just to present data, but to provide actionable advice and tell a story about our planet's climate.

---

## ✨ Key Features

* **Conversational "Wizard" UI:** An intuitive, step-by-step interface that guides users from their planned activity to a detailed climate analysis, complete with back buttons for easy navigation.
* **Personalized Recommendations:** Tlatoc provides rich, emoji-filled recommendations tailored to the user's chosen activity (e.g., "🥵 Warning: Extreme heat likely. Plan to hike early...").
* **Intelligent Date Suggestions:** If historical data shows poor conditions for a selected date, the assistant suggests a better month to plan the activity.
* **NASA-Powered Data:** All analyses are powered by a 30-year dataset (1994-2023) from the official NASA POWER (Prediction of Worldwide Energy Resources) project.
* **At-a-Glance "Comfort Index":** Synthesizes temperature and humidity data into a simple, understandable score (e.g., "75/100, Comfortable").
* **Data Download:** Users can download the raw NASA data for their selected location as a single CSV file for their own analysis.

---

## 🔧 How to Run the Project

This project is a standard Python Flask web application.

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/RatuL65/Tlatoc-NASA-Space-Apps.git]
    cd Tlatoc-NASA-Space-Apps
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # On Windows
    python -m venv .venv
    .venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python app.py
    ```

5.  Open your web browser and navigate to **`http://127.0.0.1:5000`** to use the Climate Assistant.

---

## 🛰️ Data Source

This project exclusively uses data from the **NASA POWER Project**, accessed via their official API. The POWER (Prediction of Worldwide Energy Resources) project provides global meteorological and solar energy data from NASA research, making it a reliable and authoritative source for this climate analysis tool.

