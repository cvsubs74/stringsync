from abc import ABC

from portals.BasePortal import BasePortal
import streamlit as st
import os


class TenantPortal(BasePortal, ABC):
    def __init__(self):
        super().__init__()

    def get_title(self):
        return f"{self.get_app_name()} Tenant Portal"

    def get_icon(self):
        return "🏠"

    def show_introduction(self):
        self.pre_introduction()
        st.write("""
            ### **Tenant Management Portal**!!

            **Your Centralized Platform for Multi-Organization Educational Oversight**

            This portal is  designed to offer you a streamlined experience in managing multiple educational organizations. Here are the core functionalities you can leverage:
            - 🏢 **Register New Tenants**: Seamlessly integrate new educational organizations into your existing network, complete with all essential details and administrative credentials.
            - 📋 **List All Tenants**: Gain a holistic view of all the educational organizations under your purview, including their administrative contacts and root organizations.

            Please log in to unlock the full range of management capabilities tailored to meet your organizational needs.
        """)

    def get_tab_dict(self):
        return {
            "🏢 Register a Tenant": self.register_tenant,
            "📋 List Tenants": self.list_tenants,
        }

    def register_tenant(self):
        # Build form
        form_key = 'register_form'
        field_names = ['Name', 'Description', 'Address', 'Email']
        button_label = 'Register'
        register_button, form_data = self.build_form(form_key, field_names, button_label)

        # Process form data
        name = form_data['Name']
        description = form_data['Description']
        address = form_data['Address']
        email = form_data['Email']
        if register_button:
            if not name or not description or not address or not email:
                st.error("All fields are mandatory. Please fill in all the details.")
                return

            success, message, tenant_id = self.tenant_repo.register_tenant(name)
            if success:
                success, org_id, join_code, org_message = self.org_repo.register_organization(
                    tenant_id, name, description, is_root=True)
                if not success:
                    st.error(org_message)
                    return

                username = f"{tenant_id}admin"
                password = os.environ["ADMIN_PASSWORD"]

                user_success, user_message = self.user_repo.register_user(
                    name=f"{tenant_id}_admin",
                    username=username,
                    email=email,
                    password=password,
                    org_id=org_id,
                    user_type="admin"
                )
                if user_success:
                    st.success(f"{message}, {org_message}, and {user_message}")
                else:
                    st.error(user_message)
            else:
                st.error(message)

    def list_tenants(self):
        tenants = self.tenant_repo.get_all_tenants()
        column_names = ["Name", "Id", "Root Organization", "Admin"]
        self.build_header(column_names)

        for tenant in tenants:
            tenant_name = tenant.get('name', 'Not Found')
            tenant_id = tenant.get('id', 'Not Found')

            root_org = self.org_repo.get_root_organization_by_tenant_id(tenant['id'])
            root_org_name = root_org.get('name', 'Not Found') if root_org else 'Not Found'

            admin_users = self.user_repo.get_admin_users_by_org_id(root_org.get('id', None))
            admin_username = admin_users[0].get('username', 'Not Found') if admin_users else 'Not Found'

            row_data = {
                "Name": tenant_name,
                "Id": tenant_id,
                "Root Organization": root_org_name,
                "Admin": admin_username
            }
            self.build_row(row_data)


