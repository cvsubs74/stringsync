import json
import os
import tempfile
import time
from abc import ABC, abstractmethod
import pandas as pd
import streamlit as st

from enums.ActivityType import ActivityType
from enums.UserType import UserType
from repositories.PortalRepository import PortalRepository
from repositories.RecordingRepository import RecordingRepository
from repositories.SettingsRepository import SettingsRepository
from repositories.StorageRepository import StorageRepository
from repositories.TenantRepository import TenantRepository
from repositories.TrackRepository import TrackRepository
from repositories.UserActivityRepository import UserActivityRepository
from repositories.UserRepository import UserRepository
from repositories.OrganizationRepository import OrganizationRepository
from repositories.UserSessionRepository import UserSessionRepository


class BasePortal(ABC):
    def __init__(self):
        self.tenant_repo = None
        self.org_repo = None
        self.user_repo = None
        self.user_session_repo = None
        self.user_activity_repo = None
        self.portal_repo = None
        self.settings_repo = None
        self.recording_repo = None
        self.track_repo = None
        self.storage_repo = None
        self.set_env()
        self.init_repositories()

    def init_repositories(self):
        self.tenant_repo = TenantRepository()
        self.org_repo = OrganizationRepository()
        self.user_repo = UserRepository()
        self.user_session_repo = UserSessionRepository()
        self.user_activity_repo = UserActivityRepository()
        self.portal_repo = PortalRepository()
        self.settings_repo = SettingsRepository()
        self.recording_repo = RecordingRepository()
        self.track_repo = TrackRepository()
        self.storage_repo = StorageRepository('melodymaster')

    def start(self, register=False):
        self.init_session()
        self.set_app_layout()
        self.show_introduction()
        if not self.user_logged_in():
            if register:
                self.register_and_login_user()
            else:
                self.login_user()
        else:
            self.build_tabs()

        self.show_copyright()

    def set_app_layout(self):
        st.set_page_config(
            page_title=self.get_title(),
            page_icon=self.get_icon(),
            layout="wide"
        )
        custom_css = """
                <style>
                    #MainMenu {visibility: hidden;}
                    header {visibility: hidden;}
                    footer {visibility: hidden;}   
                </style>
            """
        st.markdown(custom_css, unsafe_allow_html=True)

        # Create columns for header and logout button
        col1, col2 = st.columns([8.5, 1.5])  # Adjust the ratio as needed

        with col1:
            self.show_app_header()
        with col2:
            if self.user_logged_in():
                self.show_user_menu()

    def show_app_header(self):
        left_column, center_column, right_column = st.columns([5.5, 8, 2.5])
        with center_column:
            image = self.storage_repo.download_blob_by_name(f"logo/{self.get_app_name()}.png")
            st.image(image, use_column_width=True)

    @staticmethod
    def pre_introduction():
        st.markdown("""
                        <style>
                            .cursive-font {
                                font-family: 'Comic Sans MS', cursive, sans-serif;
                                font-size: 30px;
                                color: #853507; 
                                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5); /* Text shadow effect */
                            }
                        </style>
                        <div class="cursive-font" style="text-align: center">
                            Welcome to <span class="bold-text">GuruShishya</span>
                        </div>
                    """, unsafe_allow_html=True)

        st.markdown("""<div style="text-align: center; font-size: 17px; "> Embark on a musical journey from novice to 
        maestro at GuruShishya, where the age-old guru-shishya tradition fosters endless artistic 
        exploration.</div>""", unsafe_allow_html=True)

        st.write("")
        st.write("")

    def show_user_menu(self):
        col2_1, col2_2 = st.columns([1, 3])  # Adjust the ratio as needed
        with col2_2:
            user_options = st.selectbox("", ["", "Settings", "Logout"], index=0,
                                        format_func=lambda
                                            x: f"👤\u2003{self.get_username()}" if x == "" else x)

            if user_options == "Logout":
                self.logout_user()
            elif user_options == "Settings":
                # Navigate to settings page or open settings dialog
                pass

    def login_user(self):
        st.write("### Login")
        # Build form
        form_key = 'login_form'
        field_names = ['Username', 'Password']
        button_label = 'Login'
        login_button, form_data = self.build_form(form_key, field_names, button_label, False)

        # Process form data
        username = form_data['Username']
        password = form_data['Password']
        if login_button:
            if not username or not password:
                st.error("Both username and password are required.")
                return
            success, user_id, org_id = self.user_repo.authenticate_user(username, password)
            if success:
                self.set_session_state(user_id, org_id, username)
                st.session_state['session_id'] = self.user_session_repo.open_session(user_id)
                self.user_activity_repo.log_activity(user_id, ActivityType.LOG_IN)
                print("session_id:", st.session_state['session_id'])
                st.rerun()
            else:
                st.error("Invalid username or password.")

    def register_and_login_user(self):
        """
        Handle student login and registration through the sidebar.
        """
        is_authenticated = False
        if not self.register_user():
            st.header("Login")
            is_authenticated = False
            password, username = self.show_login_screen()
            # Create two columns for the buttons
            col1, col2, col3 = st.columns([2, 4, 32])
            # Login button in the first column
            if col1.button("Login", type="primary"):
                if username and password:
                    is_authenticated, user_id, org_id = \
                        self.user_repo.authenticate_user(username, password)
                    if is_authenticated:
                        self.set_session_state(user_id, org_id, username)
                        st.session_state['session_id'] = self.user_session_repo.open_session(user_id)
                        self.user_activity_repo.log_activity(user_id, ActivityType.LOG_IN)
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")
                else:
                    st.error("Both username and password are required")

            # Register button in the second column
            if col2.button("Register", type="primary"):
                st.session_state["show_register_section"] = True
                st.rerun()
        else:
            st.subheader("Register")
            reg_email, reg_name, reg_password, reg_username, join_code = \
                self.show_user_registration_screen()

            # Create two columns for the buttons
            col1, col2, col3 = st.columns([3, 4, 40])
            # Ok button
            if col1.button("Submit", type="primary"):
                if reg_name and reg_username and reg_email and reg_password and join_code:
                    _, org_id = self.org_repo.get_org_id_by_join_code(join_code)
                    is_registered, message, user_id = self.user_repo.register_user(
                        reg_name, reg_username, reg_email, reg_password, org_id, UserType.STUDENT.value)
                    if is_registered:
                        st.success(message)
                        st.session_state["show_register_section"] = False
                        self.user_activity_repo.log_activity(user_id, ActivityType.LOG_IN)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("All fields are required for registration")
            if col2.button("Cancel", type="primary"):
                st.session_state["show_register_section"] = False
                st.rerun()

        return is_authenticated

    @staticmethod
    def show_login_screen():
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        return password, username

    @staticmethod
    def show_user_registration_screen():
        reg_name = st.text_input("Name")
        reg_email = st.text_input("Email")
        reg_username = st.text_input(key="registration_username", label="User")
        reg_password = st.text_input(key="registration_password", type="password", label="Password")
        join_code = st.text_input("Join Code")
        return reg_email, reg_name, reg_password, reg_username, join_code

    @staticmethod
    def ok():
        return st.button("Ok", type="primary")

    @staticmethod
    def login():
        return st.button("Login", type="primary")

    @staticmethod
    def register():
        return st.button("Register", type="primary")

    @staticmethod
    def cancel():
        return st.button("Cancel", type="primary")

    @staticmethod
    def init_session():
        if 'user_logged_in' not in st.session_state:
            st.session_state['user_logged_in'] = False
        if 'user_id' not in st.session_state:
            st.session_state['user_id'] = None
        if 'org_id' not in st.session_state:
            st.session_state['org_id'] = None
        if 'tenant_id' not in st.session_state:
            st.session_state['tenant_id'] = None
        if 'username' not in st.session_state:
            st.session_state['username'] = None
        if 'show_register_section' not in st.session_state:
            st.session_state['show_register_section'] = None
        if 'last_selected_track' not in st.session_state:
            st.session_state['last_selected_track'] = None

    def set_session_state(self, user_id, org_id, username):
        st.session_state['user_logged_in'] = True
        st.session_state['user_id'] = user_id
        st.session_state['org_id'] = org_id
        st.session_state['username'] = username
        success, organization = self.org_repo.get_organization_by_id(org_id)
        if success:
            st.session_state['tenant_id'] = organization['tenant_id']

    @staticmethod
    def clear_session_state():
        st.session_state['user_logged_in'] = False
        st.session_state['user_id'] = None
        st.session_state['org_id'] = None
        st.session_state['tenant_id'] = None
        st.session_state['username'] = None

    def logout_user(self):
        session_id = st.session_state.get('session_id')
        if session_id:
            self.user_session_repo.close_session(session_id)
            self.user_activity_repo.log_activity(self.get_user_id(), ActivityType.LOG_OUT)
        self.clear_session_state()
        st.rerun()

    @staticmethod
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

    def build_tabs(self):
        tab_dict = self.get_tab_dict()
        tab_dict['Sessions'] = self.show_sessions_tab
        tab_dict['Activities'] = self.show_user_activities_tab
        tab_names = list(tab_dict.keys())
        tab_functions = list(tab_dict.values())
        tabs = st.tabs(tab_names)

        for tab, tab_function in zip(tabs, tab_functions):
            with tab:
                tab_function()

    def show_user_activities_tab(self):
        user_id = self.get_user_id()  # Get the current user ID

        # Fetch user activities data for the current user
        user_activities_data = self.user_activity_repo.get_user_activities(user_id)

        if not user_activities_data:
            st.write("No user activity data available.")
            return

        # Build the header for the user activities listing
        self.build_header(['Activity Type', 'Timestamp', 'Additional Information'])

        # Build rows for the user activities listing
        for activity in user_activities_data:
            print(activity)
            activity_type = activity['activity_type']
            timestamp = activity['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            additional_params_dict = activity.get('additional_params', '{}')
            if len(additional_params_dict) > 0:
                additional_params_str = ', '.join(f'{key}: {value}' for key, value in additional_params_dict.items())
            else:
                additional_params_str = 'No additional information available'

            self.build_row({
                'Activity Type': activity_type,
                'Timestamp': timestamp,
                'Additional Parameters': additional_params_str
            })

    def show_sessions_tab(self):
        user_id = self.get_user_id()  # Get the current user ID

        # Fetch time series data for the current user
        time_series_data = self.user_session_repo.get_time_series_data(user_id)

        if not time_series_data:
            st.write("No session data available.")
            return

        # Prepare data for visualization
        dates = [entry['date'] for entry in time_series_data]
        total_sessions = [entry['total_sessions'] for entry in time_series_data]
        total_duration = [entry['total_duration'] for entry in time_series_data]

        # Create a DataFrame for visualization
        import pandas as pd
        df = pd.DataFrame({
            'Date': pd.to_datetime(dates),
            'Total Sessions': total_sessions,
            'Total Duration': total_duration
        })

        # Draw a line chart
        st.line_chart(df.set_index('Date'))

        # Fetch session details for the current user
        session_details = self.user_session_repo.get_user_sessions(user_id)  # Corrected method name

        if not session_details:
            st.write("No session details available.")
            return

        # Build the header for the session listing
        self.build_header(['Open Session Time', 'Close Session Time', 'Duration (minutes)'])

        # Build rows for the session listing
        for session in session_details:
            open_time = session['open_session_time'].strftime('%Y-%m-%d %H:%M:%S')
            close_time = session['close_session_time'].strftime('%Y-%m-%d %H:%M:%S') if session[
                'close_session_time'] else 'N/A'
            # Convert the session duration from seconds to minutes
            duration_minutes = session['session_duration'] / 60
            self.build_row({'Open Session Time': open_time, 'Close Session Time': close_time,
                            'Duration (minutes)': f'{duration_minutes:.2f}'})

    @staticmethod
    def build_form(form_key, field_names, button_label='Submit', clear_on_submit=True):
        # Custom CSS to remove form border and adjust padding and margin
        css = r'''
                <style>
                    [data-testid="stForm"] {
                        border: 0px;
                        padding: 0px;
                        margin: 0px;
                    }
                </style>
            '''
        st.markdown(css, unsafe_allow_html=True)

        form_data = {}
        with st.form(key=form_key, clear_on_submit=clear_on_submit):
            for field in field_names:
                if field.lower() == 'password':
                    form_data[field] = st.text_input(field.capitalize(), type='password')
                else:
                    form_data[field] = st.text_input(field.capitalize())

            button = st.form_submit_button(label=button_label, type="primary")

        return button, form_data

    @staticmethod
    def build_form_with_select_boxes(form_key, select_box_options, button_label='Submit', clear_on_submit=True):
        # Custom CSS to remove form border and adjust padding and margin
        css = r'''
                <style>
                    [data-testid="stForm"] {
                        border: 0px;
                        padding: 0px;
                        margin: 0px;
                    }
                </style>
            '''
        st.markdown(css, unsafe_allow_html=True)

        form_data = {}
        with st.form(key=form_key, clear_on_submit=clear_on_submit):
            for label, options in select_box_options.items():
                default_option = f"--Select a {label.lower()}--"
                form_data[label] = st.selectbox(label, [default_option] + list(options.keys()))

            button = st.form_submit_button(label=button_label, type="primary")

        return button, form_data

    @staticmethod
    def build_header(column_names):
        num_columns = len(column_names)
        width = int(100 / num_columns)  # Calculate the width for each column

        header_html = "<div style='background-color:lightgrey;padding:5px;border-radius:3px;border:1px solid black;'>"

        for column_name in column_names:
            header_html += f"<div style='display:inline-block;width:{width}%;text-align:left;box-sizing: border-box;'>"
            header_html += f"<p style='color:black;margin:0;font-size:15px;font-weight:bold;'>{column_name}</p>"
            header_html += "</div>"

        header_html += "</div>"
        st.markdown(header_html, unsafe_allow_html=True)

    @staticmethod
    def build_row(row_data):
        num_columns = len(row_data)
        width = int(100 / num_columns)  # Calculate the width for each column

        row_html = "<div style='padding:5px;border-radius:3px;border:1px solid black;'>"

        for column_name, value in row_data.items():
            row_html += f"<div style='display:inline-block;width:{width}%;text-align:left;box-sizing: border-box;'>"
            row_html += f"<p style='color:black;margin:0;font-size:14px;'>{value}</p>"
            row_html += "</div>"

        row_html += "</div>"
        st.markdown(row_html, unsafe_allow_html=True)

    def download_to_temp_file_by_url(self, blob_url):
        """Download a blob to a temporary file and return the file's path."""
        blob_data = self.storage_repo.download_blob_by_url(blob_url)
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
            temp_file.write(blob_data)
            return temp_file.name

    def download_to_temp_file_by_name(self, blob_name):
        """Download a blob to a temporary file and return the file's path."""
        blob_data = self.storage_repo.download_blob_by_name(blob_name)
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as temp_file:
            temp_file.write(blob_data)
            return temp_file.name

    @staticmethod
    def user_logged_in():
        return st.session_state['user_logged_in']

    @staticmethod
    def get_org_id():
        return st.session_state['org_id']

    @staticmethod
    def get_user_id():
        return st.session_state['user_id']

    @staticmethod
    def get_username():
        return st.session_state['username']

    @staticmethod
    def get_tenant_id():
        return st.session_state['tenant_id']

    @staticmethod
    def register_user():
        return st.session_state["show_register_section"]

    def get_org_dir_bucket(self):
        return f'{self.get_tenant_id()}/{self.get_org_id()}'

    def get_tracks_bucket(self):
        return f'{self.get_org_dir_bucket()}/tracks'

    def get_recordings_bucket(self):
        return f'{self.get_org_dir_bucket()}/recordings'

    @staticmethod
    def get_badges_bucket():
        return 'badges'

    @staticmethod
    def get_logo_bucket():
        return 'logo'

    @staticmethod
    def set_env():
        env_vars = ['ROOT_USER', 'ROOT_PASSWORD', 'ADMIN_PASSWORD',
                    'SQL_SERVER', 'SQL_DATABASE', 'SQL_USERNAME', 'SQL_PASSWORD',
                    'MYSQL_CONNECTION_STRING', 'EMAIL_ID', 'EMAIL_PASSWORD']
        for var in env_vars:
            os.environ[var] = st.secrets[var]
        os.environ["GOOGLE_APP_CRED"] = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]

    @staticmethod
    def get_app_name():
        return "Guru Shishya"

    @abstractmethod
    def get_title(self):
        pass

    @abstractmethod
    def get_icon(self):
        pass

    @abstractmethod
    def show_introduction(self):
        pass

    @abstractmethod
    def get_tab_dict(self):
        pass
