import datetime
import time
import pandas as pd
import hashlib
import librosa
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import cosine, euclidean
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import tempfile
import os
from scipy.stats import zscore
import re

from RecordingRepository import RecordingRepository
from StorageRepository import StorageRepository
from TrackRepository import TrackRepository
from UserRepository import UserRepository


def load_and_normalize_audio(audio_path):
    y, sr = librosa.load(audio_path)
    y = librosa.util.normalize(y)
    return y, sr


def compute_mfcc(audio, sr):
    return librosa.feature.mfcc(y=audio, sr=sr)


def compute_chromagram(audio, sr):
    return librosa.feature.chroma_stft(y=audio, sr=sr)


def euclidean_distance(feature1, feature2):
    return euclidean(feature1.flatten(), feature2.flatten())


def cosine_distance(feature1, feature2):
    return cosine(feature1.flatten(), feature2.flatten())


def dtw_euclidean_distance(feature1, feature2):
    distance, _ = fastdtw(feature1.T, feature2.T, dist=euclidean)
    return distance


def dtw_cosine_distance(feature1, feature2):
    distance, _ = fastdtw(feature1.T, feature2.T, dist=cosine)
    return distance


def distance_to_score(distance, min_distance=0, max_distance=1000):
    """
    Convert a distance value to a score between 0 and 10.

    Parameters:
        distance (float): The distance value to convert.
        min_distance (float): The distance that corresponds to a score of 10.
        max_distance (float): The distance that corresponds to a score of 0.

    Returns:
        int: The converted score.
    """
    print(distance)
    if distance <= min_distance:
        return 10
    elif distance >= max_distance:
        return 0
    else:
        return round(10 - ((distance - min_distance) / (max_distance - min_distance) * 10))


def extract_features(audio_path):
    """
    Extract chroma short-time Fourier transform (STFT) features from an audio file.

    Parameters:
        audio_path (str): The path of the audio file.

    Returns:
        np.ndarray: The chroma STFT features.
    """
    y, sr = librosa.load(audio_path)
    y = librosa.util.normalize(y)
    # Chroma
    chroma1 = compute_chromagram(y, sr)
    # mfcc
    mfcc = compute_mfcc(y, sr)
    return chroma1, zscore(mfcc)


def compare_audio(teacher_path, student_path):
    """
    Compare two audio files using Fast Dynamic Time Warping (FastDTW).

    Parameters:
        teacher_path (str): The path of the teacher's audio file.
        student_path (str): The path of the student's audio file.

    Returns:
        float: The distance between the two audio files.
    """
    t_chroma, t_mfcc = extract_features(teacher_path)
    s_chroma, s_mfcc = extract_features(student_path)
    # Compute distances
    return np.mean([dtw_euclidean_distance(t_chroma, s_chroma)])


def audio_display(filename):
    """
    Display an audio file in the Streamlit app.

    Parameters:
        filename (str): The path of the audio file.
    """
    st.empty().audio(filename, format='audio/wav')


def record_audio(text):
    """
    Record audio using the Streamlit audio recorder plugin.

    Parameters:
        text (str): The text to display next to the recorder.

    Returns:
        bytes: The recorded audio data.
    """
    st.markdown('<span style="font-size: smaller; font-style: italic;">Record your performance</span>',
                unsafe_allow_html=True)

    audio_data = audio_recorder(
        key=text,
        text="",
        energy_threshold=0.01,
        pause_threshold=5,
        sample_rate=96000,
        neutral_color="#303030",
        recording_color="#de1212",
        icon_name="microphone",
        icon_size="2x",
    )

    st.empty().audio(audio_data, format="audio/wav")
    recorded_audio_file = ""
    if audio_data:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio_file:
            tmp_audio_file.write(audio_data)
        recorded_audio_file = tmp_audio_file.name
    return recorded_audio_file


def error_and_missing_notes(set_a, set_b):
    """
    Find notes that are incorrect or missing between two lists.

    Parameters:
        set_a (list): The list of correct notes.
        set_b (list): The list of notes to check.

    Returns:
        tuple: Two sets containing notes that are incorrect and missing.
    """
    set_a = set(set_a)
    set_b = set(set_b)
    elements_in_b_not_in_a = set_b - set_a
    elements_in_a_not_in_b = set_a - set_b
    return elements_in_b_not_in_a, elements_in_a_not_in_b


def freq_to_note(freq):
    """
    Convert a frequency to a musical note.

    Parameters:
        freq (float): The frequency to convert.

    Returns:
        str: The corresponding musical note.
    """
    a4_freq = 440.0
    all_notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    swaras = ['N3', 'S', 'R1', 'R2', 'G2', 'G3', 'M1', 'M2', 'P', 'D1', 'D2', 'N2']
    num_semitones = int(round(12.0 * np.log2(freq / a4_freq)))
    return swaras[num_semitones % 12]


def get_notes(audio_path):
    """
    Extract notes from an audio file.

    Parameters:
        audio_path (str): The path of the audio file.

    Returns:
        list: The list of extracted notes.
    """
    y, sr = librosa.load(audio_path)
    o_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_frames = librosa.onset.onset_detect(onset_envelope=o_env, normalize=True, sr=sr)
    onset_samples = librosa.frames_to_samples(onset_frames)
    slices = [y[start:end] for start, end in zip(onset_samples[:-1], onset_samples[1:])]
    notes = []
    for audio_slice in slices:
        fft_result = np.fft.fft(audio_slice)
        frequencies = np.fft.fftfreq(len(fft_result))
        magnitude = np.abs(fft_result)
        peak_frequency = frequencies[np.argmax(magnitude)]
        if peak_frequency > 0:
            note = freq_to_note(peak_frequency)
            notes.append(note)
    return notes


def filter_consecutive_notes(notes, min_consecutive=3):
    """
    Filters out notes that don't appear consecutively at least `min_consecutive` times.

    Parameters:
        notes (list): List of detected notes.
        min_consecutive (int): Minimum number of consecutive occurrences for a note to be considered.

    Returns:
        list: List of filtered notes.
    """
    filtered_notes = []
    prev_note = None
    count = 0
    for note in notes:
        if note == prev_note:
            count += 1
        else:
            count = 1
        if count == min_consecutive:
            filtered_notes.append(note)
        prev_note = note
    filtered_notes = list(dict.fromkeys(filtered_notes))
    return filtered_notes


# Main function where the Streamlit app runs
def setup_streamlit_app():
    """
    Set up the Streamlit app with headers and markdown text.
    """
    st.set_page_config(layout='wide')
    st.header('**String Sync**', divider='rainbow')
    st.markdown(
        """
        String Sync is an innovative platform designed to help music teachers and students enhance 
        their learning experience. By leveraging advanced audio analysis, this app allows you to 
        compare your musical performance with a reference recording, providing you with a 
        quantifiable score based on the similarity.
        
        ### How Does it Work? 
        1. **Listen to the track**: Each track comes with a reference audio file. Listen to it carefully to understand what you need to achieve. 
        2. **Upload Your Recording**: Record your own performance and upload it here. 
        3. **Get Your Score**: Our advanced algorithm will compare your performance with the reference audio and give you a score based on how closely they match. 
        
        ### Why Use String Sync?
        - **Objective Feedback**: Get unbiased, data-driven feedback on your performance.
        - **Progress Tracking**: Keep track of your scores to monitor your improvement over time.
        - **Flexible**: Suitable for any instrument and skill level.
        
        "Ready to get started? Select your track from the sidebar and either directly record or upload your 
        performance!" """
    )


def handle_student_login():
    """
    Handle student login and registration through the sidebar.
    """
    user_repo = UserRepository()  # Initialize UserRepository
    user_repo.connect()

    is_authenticated = False
    if user_not_logged_in():
        if not register_user():
            st.sidebar.header("Student Login")
            is_authenticated = False
            password, username = show_login_screen()
            # Create two columns for the buttons
            col1, col2, col3 = st.sidebar.columns([4, 5, 3])
            # Login button in the first column
            with col1:
                if login():
                    if username and password:
                        is_authenticated, user_id = user_repo.authenticate_user(username, password)
                        if is_authenticated:
                            login_user(username, user_id, password)
                        else:
                            fail_login()
                    else:
                        st.sidebar.error("Both username and password are required")

            # Register button in the second column
            with col2:
                if register():
                    st.session_state["show_register_section"] = True
                    st.rerun()
        else:
            st.sidebar.subheader("Register")
            reg_email, reg_name, reg_password, reg_username = show_user_registration_screen()

            # Create two columns for the buttons
            col1, col2, col3 = st.sidebar.columns([3, 5, 4])
            # Ok button
            with col1:
                if ok():
                    if reg_name and reg_username and reg_email and reg_password:
                        is_registered, message = user_repo.register_user(reg_name, reg_username, reg_email,
                                                                         reg_password)
                        if is_registered:
                            st.sidebar.success(message)
                            st.session_state["show_register_section"] = False
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.sidebar.error(message)
                    else:
                        st.sidebar.error("All fields are required for registration")
            with col2:
                if cancel():
                    st.session_state["show_register_section"] = False
                    st.rerun()
    else:
        st.sidebar.success(f"You are already logged in.")

    user_repo.close()  # Close the database connection
    return is_authenticated


def register_user():
    return st.session_state["show_register_section"]


def show_user_registration_screen():
    reg_name = st.sidebar.text_input("Name")
    reg_email = st.sidebar.text_input("Email")
    reg_username = st.sidebar.text_input(key="registration_username", label="User")
    reg_password = st.sidebar.text_input(key="registration_password", type="password", label="Password")
    return reg_email, reg_name, reg_password, reg_username


def init_session():
    if "user_logged_in" not in st.session_state:
        st.session_state["user_logged_in"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "password" not in st.session_state:
        st.session_state["password"] = None
    if "show_register_section" not in st.session_state:
        st.session_state["show_register_section"] = False


def fail_login():
    st.sidebar.error("Invalid credentials")


def login_user(username, user_id, password):
    st.sidebar.success(f"Welcome, {username}!")
    st.session_state["user_logged_in"] = True
    st.session_state['user'] = username
    st.session_state['user_id'] = user_id
    st.session_state['username'] = username  # Save username
    st.session_state['password'] = password  # Save password
    st.rerun()


def login():
    return st.button("Login", type="primary")


def register():
    return st.button("Register", type="primary")


def ok():
    return st.button("Ok", type="primary")


def cancel():
    return st.button("Cancel", type="primary")


def get_user_id():
    return st.session_state['user_id']


def show_login_screen():
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    return password, username


def user_logged_in():
    return st.session_state["user_logged_in"]


def user_not_logged_in():
    return "user_logged_in" not in st.session_state or not user_logged_in()


def create_track_headers():
    """
    Create headers for the track section.
    """
    col1, col2, col3 = st.columns([3, 3, 5])
    with col1:
        st.subheader('Track', divider='rainbow')
    with col2:
        st.subheader('Upload', divider='rainbow')
    with col3:
        st.subheader('Analysis', divider='rainbow')


def display_track_files(track_file):
    """
    Display the teacher's track files.

    Parameters:
        track_file (str): The path to the track file.
    """
    st.write("")
    st.write("")
    st.audio(track_file, format='audio/m4a')


def display_notation_pdf_link():
    """
    Display a link to the musical notation PDF for the track and an option to download it.
    """
    notation_pdf_path = "notations/Practice Worksheet 1.pdf"

    # Provide a download button for the PDF
    with open(notation_pdf_path, "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="Download Notations",
        data=pdf_bytes,
        file_name="Practice Worksheet 1.pdf",
        mime="application/pdf",
        type="primary"
    )


def download_track(track):
    # Provide a download button for the original audio file
    st.write("")
    with open(track, "rb") as f:
        audio_bytes = f.read()
    st.download_button(
        label="Download track",
        data=audio_bytes,
        file_name=track,
        mime="audio/mp3",
        type="primary"
    )


def handle_audio_option():
    option = st.radio("", ["Upload Audio File", "Use Audio Recorder"])
    if option == "Use Audio Recorder":
        return True
    return False


def handle_audio_recording():
    st.write("")
    return record_audio("Record")


def handle_file_upload(user_id, track_id):
    student_path = ""
    recording_id = -1
    uploaded_student_file = st.file_uploader("", type=["m4a", "wav", "mp3"])
    if uploaded_student_file is not None:
        timestamp = datetime.datetime.now()
        student_path = f"{user_id}-{track_id}-{timestamp}.m4a"

        # Read the uploaded file into a bytes buffer
        recording_data = uploaded_student_file.getbuffer()

        # Calculate the hash of the file
        file_hash = hashlib.md5(recording_data).hexdigest()

        # Check if a recording with the same hash already exists
        recording_repository = RecordingRepository()
        if recording_repository.is_duplicate_recording(user_id, track_id, file_hash):
            st.error("You have already uploaded this recording.")
            return student_path, recording_id, False

        # Calculate duration
        with open(student_path, "wb") as f:
            f.write(recording_data)

        y, sr = librosa.load(student_path)
        duration = librosa.get_duration(y=y, sr=sr)

        # Store in database
        storage_repository = StorageRepository("stringsync")
        url = storage_repository.upload_file(student_path, student_path)
        recording_id = recording_repository.add_recording(
            get_user_id(), track_id, student_path, url, timestamp, duration, file_hash)
        st.audio(student_path, format='audio/m4a')

    return student_path, recording_id, True


def display_student_performance(track_file, student_path, track_notes, offset_distance):
    """
    Display the student's performance score and remarks.

    Parameters:
        track_file (str): The path to the track file.
        student_path (str): The path to the student's recorded or uploaded file.
        offset_distance: The distance between the track file and its reference.
        track_notes: The unique notes in the track
    """
    st.write("")
    st.write("")
    score = -1
    analysis = ""
    if student_path:
        distance = compare_audio(track_file, student_path)
        print("Distance: ", distance)
        relative_distance = distance - offset_distance
        if len(track_notes) == 0:
            track_notes = get_notes(track_file)
            track_notes = filter_consecutive_notes(track_notes)
        print("track notes:", track_notes)
        student_notes = get_notes(student_path)
        print(student_notes)
        student_notes = filter_consecutive_notes(student_notes)
        print("Student notes:", student_notes)
        error_notes, missing_notes = error_and_missing_notes(track_notes, student_notes)
        score = distance_to_score(relative_distance)
        analysis = display_score_and_analysis(score, error_notes, missing_notes)
        os.remove(student_path)

    return score, analysis


def display_score_and_analysis(score, error_notes, missing_notes):
    """
    Display the student's score and any error or missing notes.

    Parameters:
        score (int): The student's performance score.
        error_notes (list): The list of error notes.
        missing_notes (list): The list of missing notes.
    """
    message = f"Similarity score: {score}\n"
    if score <= 3:
        st.error(message)
    elif score <= 7:
        st.warning(message)
    elif score <= 9:
        st.success(message)
    else:
        st.success(message)

    # Create dictionaries to hold the first alphabet of each note and the corresponding notes
    error_dict = {}
    missing_dict = {}

    for note in error_notes:
        first_letter = note[0]
        if first_letter not in error_dict:
            error_dict[first_letter] = []
        error_dict[first_letter].append(note)

    for note in missing_notes:
        first_letter = note[0]
        if first_letter not in missing_dict:
            missing_dict[first_letter] = []
        missing_dict[first_letter].append(note)

    # Correlate error notes with missing notes
    analysis = ""
    message = "Note analysis:\n"
    if error_dict == missing_dict:
        message += f"Your recording had all the notes that the track had.\n"
    else:
        for first_letter, error_note_list in error_dict.items():
            if first_letter in missing_dict:
                for error_note in error_note_list:
                    message += f"Play {missing_dict[first_letter][0]} instead of {error_note}\n"
            else:
                for error_note in error_note_list:
                    message += f"You played the note {error_note}, however that is not present in the track\n"

        for first_letter, missing_note_list in missing_dict.items():
            if first_letter not in error_dict:
                for missing_note in missing_note_list:
                    message += f"You missed playing the note {missing_note}\n"
    st.info(message)
    analysis += message
    message = ""
    if score <= 3:
        message += "Keep trying. You can do better!"
        st.error(message)
    elif score <= 7:
        message += "Good job. You are almost there!"
        st.warning(message)
    elif score <= 9:
        message += "Great work. Keep it up!"
        st.success(message)
    else:
        message += "Excellent! You've mastered this track!"
        st.success(message)
    analysis += message
    return analysis


def display_notation(track, notation_path):
    unique_notes = []
    if os.path.exists(notation_path):
        with open(notation_path, "r") as f:
            notation_content = f.read()
        st.markdown(f"**Notation:**")
        display_notes_with_subscript(notation_content)

        # Extract and filter notes
        notes = re.split(r'[,\s_]+', notation_content.replace('b', '').strip())
        valid_notes = {'S', 'R1', 'R2', 'R3', 'G1', 'G2', 'G3', 'M1', 'M2', 'P', 'D1', 'D2', 'D3', 'N1', 'N2', 'N3'}
        unique_notes = list(set(notes).intersection(valid_notes))
    else:
        st.warning(f"No notation file found for track: {track}")
    return unique_notes


def display_notes_with_subscript(notation_content):
    formatted_notes = ""
    buffer = ""
    bold_flag = False
    section_flag = False

    for char in notation_content:
        if char.isalpha() and char != 'b':
            buffer += char
        elif char == ':':
            buffer += char
        elif char.isdigit():
            buffer += char
        elif char == 'b':
            bold_flag = True
        else:
            if section_flag:
                formatted_notes += f"<b>{buffer}</b>"
                section_flag = False
            else:
                if len(buffer) > 1:
                    note = f"{buffer[0]}<sub>{buffer[1:]}</sub>"
                else:
                    note = buffer

                if bold_flag:
                    formatted_notes += f"<b>{note}</b>"
                else:
                    formatted_notes += note

            if char in ['_', ',', '\n', ' ']:
                formatted_notes += char if char != '\n' else "<br>"

            buffer = ""
            bold_flag = False

        if buffer == "Section:":
            section_flag = True
            buffer = ""

    if buffer:
        if len(buffer) > 1:
            note = f"{buffer[0]}<sub>{buffer[1:]}</sub>"
        else:
            note = buffer

        if bold_flag:
            formatted_notes += f"<b>{note}</b>"
        else:
            formatted_notes += note

    st.markdown(f"<div style='font-size: 16px; font-weight: normal;'>{formatted_notes}</div>",
                unsafe_allow_html=True)


def set_env():
    os.environ["GOOGLE_APP_CRED"] = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]
    os.environ["SQL_SERVER"] = st.secrets["SQL_SERVER"]
    os.environ["SQL_DATABASE"] = st.secrets["SQL_DATABASE"]
    os.environ["SQL_USERNAME"] = st.secrets["SQL_USERNAME"]
    os.environ["SQL_PASSWORD"] = st.secrets["SQL_PASSWORD"]
    os.environ["MYSQL_CONNECTION_STRING"] = st.secrets["MYSQL_CONNECTION_STRING"]
    os.environ["EMAIL_ID"] = st.secrets["EMAIL_ID"]
    os.environ["EMAIL_PASSWORD"] = st.secrets["EMAIL_PASSWORD"]


def main():
    set_env()
    setup_streamlit_app()
    init_session()
    if not user_logged_in():
        st.session_state["user_logged_in"] = handle_student_login()

    if user_logged_in():
        st.sidebar.success(f"Welcome {st.session_state['user']}")
        use_recorder = handle_audio_option()
        create_track_headers()
        # Initialize the AudioRepository
        track_repo = TrackRepository()

        # Fetch all levels, ragams, and tags
        all_levels = track_repo.get_all_levels()
        all_ragams = track_repo.get_all_ragams()
        all_tags = track_repo.get_all_tags()
        all_track_types = track_repo.get_all_track_types()

        # Add filters in the sidebar
        selected_track_type = st.sidebar.selectbox("Filter by Track Type", ["All"] + all_track_types)
        selected_level = st.sidebar.selectbox("Filter by Level", ["All"] + all_levels)
        selected_ragam = st.sidebar.selectbox("Filter by Ragam", ["All"] + all_ragams)
        selected_tags = st.sidebar.multiselect("Filter by Tags", all_tags)

        # Fetch tracks based on selected filters
        tracks = track_repo.search_tracks(
            ragam=None if selected_ragam == "All" else selected_ragam,
            level=None if selected_level == "All" else selected_level,
            tags=selected_tags if selected_tags else None,
            track_type=None if selected_track_type == "All" else selected_track_type,
        )
        if len(tracks) == 0:
            return

        # Convert tracks to a list of track names for the selectbox
        track_names = [track[1] for track in tracks]
        selected_track = st.sidebar.selectbox("Select a Track", track_names)

        # Display a Logout button when the user is logged in
        if st.sidebar.button("Logout", type="primary"):
            st.session_state["user_logged_in"] = False
            st.rerun()

        selected_track_details = next((track for track in tracks if track[1] == selected_track), None)

        # Use the selected track
        track_id = selected_track_details[0]
        track_name = selected_track_details[1]
        track_file = selected_track_details[2]
        track_ref_file = selected_track_details[3]
        notation_file = selected_track_details[4]
        offset_distance = compare_audio(track_file, track_ref_file)
        print("Offset:", offset_distance)

        student_recording = None
        col1, col2, col3 = st.columns([3, 3, 5])
        with col1:
            display_track_files(track_file)
            unique_notes = display_notation(selected_track, notation_file)
        with col2:
            if use_recorder:
                student_recording = handle_audio_recording()
            else:
                student_recording, recording_id, is_success = handle_file_upload(get_user_id(), track_id)
        with col3:
            if is_success:
                score, analysis = display_student_performance(track_file, student_recording, unique_notes, offset_distance)
                update_score_and_analysis(recording_id, score, analysis)

        # List all recordings for the track
        st.write("")
        st.write("")
        st.write("")

        list_recordings(st.session_state['user'], get_user_id())

    show_copyright()


def update_score_and_analysis(recording_id, score, analysis):
    recording_repository = RecordingRepository()
    recording_repository.update_score_and_analysis(recording_id, score, analysis)


def list_recordings(username, user_id):
    # Center-align the subheader with reduced margin-bottom
    st.markdown("<h3 style='text-align: center; margin-bottom: 0;'>Performances</h3>", unsafe_allow_html=True)

    # Add a rainbow divider with reduced margin-top
    st.markdown(
        "<hr style='height:2px; margin-top: 0; border-width:0; background: linear-gradient(to right, violet, indigo, blue, green, yellow, orange, red);'>",
        unsafe_allow_html=True)

    storage_repository = StorageRepository("stringsync")
    recording_repository = RecordingRepository()
    recordings = recording_repository.get_all_recordings_by_user(user_id)

    if not recordings:
        st.write("No recordings found.")
        return

    # Create a DataFrame to hold the recording data
    df = pd.DataFrame(recordings)

    # Create a table header
    col1, col2, col3, col4, col5 = st.columns([3.5, 1, 3, 3, 2])
    col2.markdown("**Score**", unsafe_allow_html=True)
    col3.markdown("**Analysis**", unsafe_allow_html=True)
    col4.markdown("**Remarks**", unsafe_allow_html=True)
    col5.markdown("**Time**", unsafe_allow_html=True)

    # Loop through each recording and create a table row
    for index, recording in df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([3.5, 1, 3, 3, 2])
        if recording['blob_url']:
            filename = storage_repository.download_blob(recording['blob_name'])
            col1.audio(filename, format='audio/m4a')
        else:
            col1.write("No audio data available.")

        # Use Markdown to make the text black and larger
        col2.markdown(f"<div style='padding-top:15px;color:black;font-size:14px;'>{recording['score']}</div>",
                      unsafe_allow_html=True)
        col3.markdown(
            f"<div style='padding-top:15px;color:black;font-size:14px;'>{recording.get('analysis', 'N/A')}</div>",
            unsafe_allow_html=True)
        col4.markdown(
            f"<div style='padding-top:15px;color:black;font-size:14px;'>{recording.get('remarks', 'N/A')}</div>",
            unsafe_allow_html=True)
        col5.markdown(f"<div style='padding-top:15px;color:black;font-size:14px;'>{recording['timestamp']}</div>",
                      unsafe_allow_html=True)

    recording_repository.close()  # Close the database connection


def show_copyright():
    st.write("")
    st.write("")
    st.write("")
    footer_html = """
        <div style="text-align: center; color: gray;">
            <p style="font-size: 14px;">© 2023 KA Academy of Indian Music and Dance. All rights reserved.</p>
        </div>
        """
    st.markdown(footer_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()