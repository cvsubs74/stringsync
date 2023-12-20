import base64
import os
import random
import streamlit as st

from enums.SoundEffect import SoundEffect
from repositories.StorageRepository import StorageRepository


class SoundEffectGenerator:
    def __init__(self, storage_repo: StorageRepository):
        self.storage_repo = storage_repo

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
        st.balloons()

    @staticmethod
    def get_sound_effects_bucket():
        return 'sound effects'
