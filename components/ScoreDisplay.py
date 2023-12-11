import base64
import os
import random
import streamlit as st
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
            st.balloons()
            self.play_sound_effect(SoundEffect.AWARD)

        st.success(message)

    def get_sound_effect(self, sound_effect: SoundEffect):
        # Directory where sound effects are stored locally
        local_directory = self.get_sound_effects_bucket()

        # Choose a random effect
        effect = random.choice(sound_effect.effects)
        local_file_path = os.path.join(local_directory, effect)

        # Download from remote if not found locally
        if not os.path.exists(local_file_path):
            remote_path = f"{self.get_sound_effects_bucket()}/{effect}"
            self.storage_repo.download_blob_and_save(remote_path, local_file_path)

        return local_file_path

    def play_sound_effect(self, effect_type: SoundEffect):
        file_path = self.get_sound_effect(effect_type)
        with open(file_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"<audio autoplay><source src='data:audio/mp3;base64,{b64}' type='audio/mp3'></audio>"
            st.markdown(md, unsafe_allow_html=True)

    @staticmethod
    def get_sound_effects_bucket():
        return 'sound effects'
