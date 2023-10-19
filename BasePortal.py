import os
from abc import ABC, abstractmethod

import streamlit as st

from TenantRepository import TenantRepository
from UserRepository import UserRepository
from OrganizationRepository import OrganizationRepository


class BasePortal(ABC):
    def __init__(self):
        self.set_env()
        self.tenant_repo = TenantRepository()
        self.org_repo = OrganizationRepository()
        self.user_repo = UserRepository()
        
    def start(self):
        self.init_session()
        self.set_app_layout()
        self.show_introduction()
        if not self.user_logged_in():
            self.login_user()
        else:
            st.success(f"Welcome {self.get_username()}!")
            self.build_tabs()

        self.show_copyright()

    def set_app_layout(self):
        st.set_page_config(
            layout='wide'
        )
        hide_streamlit_style = """
                    <style>
                    #MainMenu {visibility: hidden;}
                    header {visibility: hidden;}
                    footer {visibility: hidden;}   
                    </style>

                    """
        st.markdown(hide_streamlit_style, unsafe_allow_html=True)

        # Create columns for header and logout button
        col1, col2 = st.columns([8.5, 1.5])  # Adjust the ratio as needed

        with col1:
            self.show_app_header()
        with col2:
            if self.user_logged_in():
                self.show_user_menu()

    @staticmethod
    def show_app_header():
        st.markdown("<h1 style='margin-bottom:0px;'>StringSync</h1>", unsafe_allow_html=True)

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

    @abstractmethod
    def show_introduction(self):
        pass

    def login_user(self):
        st.header("Login")
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
                st.rerun()
            else:
                st.error("Invalid username or password.")

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

    @staticmethod
    def user_logged_in():
        return st.session_state['user_logged_in']

    @staticmethod
    def get_username():
        return st.session_state['username']

    @abstractmethod
    def build_tabs(self):
        pass

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

    @staticmethod
    def set_env():
        os.environ['ROOT_USER'] = st.secrets["ROOT_USER"]
        os.environ['ROOT_PASSWORD'] = st.secrets["ROOT_PASSWORD"]
        os.environ['ADMIN_PASSWORD'] = st.secrets["ADMIN_PASSWORD"]
        os.environ["GOOGLE_APP_CRED"] = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]
        os.environ["SQL_SERVER"] = st.secrets["SQL_SERVER"]
        os.environ["SQL_DATABASE"] = st.secrets["SQL_DATABASE"]
        os.environ["SQL_USERNAME"] = st.secrets["SQL_USERNAME"]
        os.environ["SQL_PASSWORD"] = st.secrets["SQL_PASSWORD"]
        os.environ["MYSQL_CONNECTION_STRING"] = st.secrets["MYSQL_CONNECTION_STRING"]
        os.environ["EMAIL_ID"] = st.secrets["EMAIL_ID"]
        os.environ["EMAIL_PASSWORD"] = st.secrets["EMAIL_PASSWORD"]
