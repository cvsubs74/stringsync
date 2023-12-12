import librosa
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import cosine, euclidean
from scipy.stats import zscore


class AudioProcessor:

    @staticmethod
    def load_and_normalize_audio(audio_path):
        y, sr = librosa.load(audio_path)
        y = librosa.util.normalize(y)
        return y, sr

    @staticmethod
    def compute_mfcc(audio, sr):
        return librosa.feature.mfcc(y=audio, sr=sr)

    @staticmethod
    def compute_chromagram(audio, sr):
        return librosa.feature.chroma_stft(y=audio, sr=sr)

    @staticmethod
    def euclidean_distance(feature1, feature2):
        return euclidean(feature1.flatten(), feature2.flatten())

    @staticmethod
    def cosine_distance(feature1, feature2):
        return cosine(feature1.flatten(), feature2.flatten())

    @staticmethod
    def dtw_euclidean_distance(feature1, feature2):
        distance, _ = fastdtw(feature1.T, feature2.T, dist=euclidean)
        return distance

    @staticmethod
    def dtw_cosine_distance(feature1, feature2):
        distance, _ = fastdtw(feature1.T, feature2.T, dist=cosine)
        return distance

    @classmethod
    def extract_features(cls, audio_path):
        y, sr = cls.load_and_normalize_audio(audio_path)
        chroma = cls.compute_chromagram(y, sr)
        mfcc = cls.compute_mfcc(y, sr)
        return chroma, zscore(mfcc)

    @classmethod
    def compare_audio(cls, teacher_path, student_path):
        t_chroma, t_mfcc = cls.extract_features(teacher_path)
        s_chroma, s_mfcc = cls.extract_features(student_path)
        return np.mean([cls.dtw_euclidean_distance(t_chroma, s_chroma)])

    @staticmethod
    def calculate_audio_duration(path):
        y, sr = librosa.load(path)
        return librosa.get_duration(y=y, sr=sr)
