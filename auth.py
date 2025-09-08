import streamlit as st
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional


class Authentication:
    """Handle authentication for admin access to financial dashboard."""
    
    def __init__(self):
        # Default admin password - should be changed via environment variable
        self.admin_password = os.getenv('DASHBOARD_ADMIN_PASSWORD', 'admin_password')
        self.session_timeout_minutes = 30
        
    def hash_password(self, password: str) -> str:
        """Create a hash of the password for secure comparison."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify if the provided password matches the admin password."""
        return self.hash_password(password) == self.hash_password(self.admin_password)
    
    def is_admin_logged_in(self) -> bool:
        """Check if admin is currently logged in and session is valid."""
        if 'admin_logged_in' not in st.session_state:
            return False
            
        if not st.session_state.admin_logged_in:
            return False
            
        # Check session timeout
        if 'admin_login_time' in st.session_state:
            login_time = st.session_state.admin_login_time
            current_time = datetime.now()
            
            if current_time - login_time > timedelta(minutes=self.session_timeout_minutes):
                self.logout_admin()
                return False
                
        return True
    
    def login_admin(self, password: str) -> bool:
        """Attempt to log in admin with provided password."""
        if self.verify_password(password):
            st.session_state.admin_logged_in = True
            st.session_state.admin_login_time = datetime.now()
            return True
        return False
    
    def logout_admin(self):
        """Log out admin and clear session."""
        st.session_state.admin_logged_in = False
        if 'admin_login_time' in st.session_state:
            del st.session_state.admin_login_time
    
    def show_login_form(self) -> bool:
        """Display login form and handle authentication."""
        st.markdown("## 🔒 Admin Login")
        st.markdown("Enter the admin password to access financial data management.")
        
        with st.form("admin_login"):
            password = st.text_input(
                "Admin Password", 
                type="password", 
                help="Contact the system administrator for login credentials"
            )
            
            col1, col2 = st.columns([1, 3])
            with col1:
                login_button = st.form_submit_button("Login", type="primary")
            
            if login_button:
                if password:
                    if self.login_admin(password):
                        st.success("✅ Login successful! Redirecting to admin dashboard...")
                        st.rerun()
                    else:
                        st.error("❌ Invalid password. Please try again.")
                        # Add a small delay to prevent brute force attacks
                        st.session_state.failed_login_attempts = st.session_state.get('failed_login_attempts', 0) + 1
                        if st.session_state.failed_login_attempts >= 3:
                            st.warning("⚠️ Multiple failed attempts detected. Please wait before trying again.")
                else:
                    st.error("Please enter a password.")
        
        return False
    
    def show_admin_header(self):
        """Show admin header with logout option."""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.markdown("### 👑 Admin Mode")
        
        with col2:
            if 'admin_login_time' in st.session_state:
                login_time = st.session_state.admin_login_time
                time_remaining = self.session_timeout_minutes - (datetime.now() - login_time).seconds // 60
                if time_remaining > 0:
                    st.info(f"Session expires in {time_remaining} minutes")
        
        with col3:
            if st.button("🚪 Logout", key="admin_logout"):
                self.logout_admin()
                st.rerun()
    
    def require_admin(self):
        """Decorator-like function to require admin authentication."""
        if not self.is_admin_logged_in():
            st.error("🔒 Admin access required")
            return False
        return True


def get_user_role() -> str:
    """Determine current user role based on session state."""
    auth = Authentication()
    if auth.is_admin_logged_in():
        return "admin"
    return "public"


def show_access_selector():
    """Show interface for selecting public or admin access."""
    st.markdown("# 💰 Cawston Parish Council Financial Dashboard")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("## Choose Access Level")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button(
                "👥 Public View", 
                help="View financial summaries and reports",
                use_container_width=True
            ):
                st.session_state.access_mode = "public"
                st.rerun()
        
        with col_b:
            if st.button(
                "🔒 Admin Access", 
                help="Full access to data management and analysis",
                use_container_width=True
            ):
                st.session_state.access_mode = "admin"
                st.rerun()
        
        st.markdown("---")
        st.markdown(
            """
            **Public View**: Access financial summaries, income/expenditure breakdowns, and key metrics  
            **Admin Access**: Full dashboard with data management, analysis tools, and advanced features
            """
        )