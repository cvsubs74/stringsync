import base64
import os
import random
import streamlit as st

from components.SoundEffectGenerator import SoundEffectGenerator
from enums.SoundEffect import SoundEffect
from repositories.StorageRepository import StorageRepository


class ScoreDisplay:
    def __init__(self, storage_repo: StorageRepository):
        self.storage_repo = storage_repo

    def display_score(self, score):
        """
        Displays the score and provides feedback based on the score value, divided into eleven bands, with emojis.
        :param score: The score to be displayed.
        """
        if score is None:
            st.error("🚫 No score available.")
            return

        # Format the score to have two decimal places
        formatted_score = f"**{score:.2f}**"

        # Determine the message based on the score range
        feedback = [
            ("🐢 Just beginning, keep practicing!", 0.00, 0.99),
            ("🌱 Small steps forward!", 1.00, 1.99),
            ("🐾 Gaining ground!", 2.00, 2.99),
            ("🚶‍♂️ On the right path!", 3.00, 3.99),
            ("🏃‍♂️ Making good progress!", 4.00, 4.99),
            ("🚀 Taking off!", 5.00, 5.99),
            ("🌟 Shining brighter!", 6.00, 6.99),
            ("🎯 Getting closer to the target!", 7.00, 7.99),
            ("🏅 Almost there, excellent work!", 8.00, 8.99),
            ("🏆 Outstanding achievement!", 9.00, 9.99),
            ("🎉 Perfect score, incredible!", 10.00, 10.00)
        ]

        for emoji, lower_bound, upper_bound in feedback:
            if lower_bound <= score <= upper_bound:
                message = f"You scored {formatted_score}\n\n{emoji}"
                break
        else:
            message = "Score out of range."

        if 8.50 <= score <= 10.00:
            sound_effect_generator = SoundEffectGenerator(self.storage_repo)
            sound_effect_generator.play_sound_effect(SoundEffect.AWARD)

        st.success(message)

