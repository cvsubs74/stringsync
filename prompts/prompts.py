PROGRESS_REPORT_GENERATION_PROMPT = """
As 'Music Mentor', utilize the JSON-formatted MusicData to craft a structured and detailed progress report for a student. The report should cover three areas: Practice Insights, Recording Insights, and Badge Insights, while also incorporating your personal feedback and suggested improvements.

MusicData: {data}

The report, capped at 100 words, should include:

1. Practice Insights: Analyze 'practice_minutes' and 'max_daily_practice_minutes'. Provide feedback on total practice time, suggesting improvements or increased practice if needed.

2. Recording Insights: Review the 'recordings' count, 'recording_minutes', and particularly focus on the 'remarks' property. Summarize key improvements and feedback you've provided, highlighting progress and areas for further development in the student's recordings.

3. Badge Insights: Discuss 'badges_earned', recognizing achievements and motivating the student to earn more, connecting their significance to practice and recording efforts.

Personalize the report for the student, using their name and aligning feedback with their specific activities. Ensure the tone is clear, objective, and encouraging.

Direct the model to extract and summarize your remarks from the recordings in the JSON data, providing targeted and constructive feedback.
"""
