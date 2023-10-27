import os

import streamlit as st

from repositories.AppInstanceRepository import AppInstanceRepository


def main():
    if 'redirect_done' not in st.session_state:
        st.session_state['redirect_done'] = False  # Initialize redirect flag

    if 'app_instance_url' not in st.session_state and not st.session_state['redirect_done']:
        set_env()
        app_instance_repo = AppInstanceRepository()
        st.write("Load balancer active")
        app_instance = app_instance_repo.get_earliest_instance()
        app_instance_url = app_instance['url']
        app_instance_repo.update_last_used(app_instance['id'])
        st.session_state['app_instance_url'] = app_instance_url  # Store in session state
        st.write(app_instance_url)
        app_instance_url = "www.google.com"
        st.write(f'<meta http-equiv="refresh" content="0; URL={app_instance_url}" />', unsafe_allow_html=True)
        st.session_state['redirect_done'] = True  # Set redirect flag to true

def set_env():
    env_vars = ['ROOT_USER', 'ROOT_PASSWORD', 'ADMIN_PASSWORD',
                'SQL_SERVER', 'SQL_DATABASE', 'SQL_USERNAME', 'SQL_PASSWORD',
                'MYSQL_CONNECTION_STRING', 'EMAIL_ID', 'EMAIL_PASSWORD']
    for var in env_vars:
        os.environ[var] = st.secrets[var]
    os.environ["GOOGLE_APP_CRED"] = st.secrets["GOOGLE_APPLICATION_CREDENTIALS"]


if __name__ == "__main__":
    main()
