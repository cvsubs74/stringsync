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
        Displays the score and provides feedback based on the score value, divided into five bands, with emojis.
        :param score: The score to be displayed.
        """
        if score is None:
            st.error("🚫 No score available.")
            return

        # Format the score to have two decimal places
        formatted_score = f"**{score:.2f}**"

        # Determine the message based on the score range
        if 0 <= score <= 2:
            message = f"You scored {formatted_score}\n\n🐌 Keep trying! Focus on the basics and practice regularly."
            st.error(message)
        elif 3 <= score <= 4:
            message = f"You scored {formatted_score}\n\n🌱 You're getting there! Review the challenging parts and keep practicing."
            st.warning(message)
        elif 5 <= score <= 6:
            message = f"You scored {formatted_score}\n\n📈 Good progress! Keep refining your skills."
            st.info(message)
        elif 7 <= score <= 8:
            message = f"You scored {formatted_score}\n\n🎉 Great job! You're showing strong understanding and skill."
            st.success(message)
        elif 9 <= score <= 10:
            message = f"You scored {formatted_score}\n\n🌟 Outstanding performance! Your dedication is truly paying off."
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
