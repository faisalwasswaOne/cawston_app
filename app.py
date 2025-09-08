import streamlit as st
import os
from auth import Authentication, show_access_selector
from public_dashboard import show_public_dashboard
from admin_dashboard import show_admin_dashboard


def main():
    """Main application router with authentication and access control."""
    
    # Configure the page
    st.set_page_config(
        page_title="Cawston Parish Council Financial Dashboard",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="auto",
        menu_items={
            'Get Help': 'mailto:clerk@cawston-pc.org.uk',
            'Report a bug': 'mailto:clerk@cawston-pc.org.uk',
            'About': """
            # Cawston Parish Council Financial Dashboard
            
            This dashboard provides transparency into council finances with:
            - Public view for residents and stakeholders
            - Admin interface for financial management
            
            For questions, contact the Parish Clerk.
            """
        }
    )
    
    # Initialize authentication
    auth = Authentication()
    
    # Check if user has selected access mode
    if 'access_mode' not in st.session_state:
        st.session_state.access_mode = None
    
    # Route based on access mode and authentication
    if st.session_state.access_mode is None:
        # Show access selection screen
        show_access_selector()
    
    elif st.session_state.access_mode == "public":
        # Show public dashboard
        _show_public_interface()
    
    elif st.session_state.access_mode == "admin":
        # Handle admin authentication and dashboard
        _show_admin_interface(auth)
    
    else:
        # Fallback to access selector
        st.session_state.access_mode = None
        st.rerun()


def _show_public_interface():
    """Show the public interface with option to switch to admin."""
    # Add header with switch option
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown("## 👥 Public Financial View")
    
    with col2:
        if st.button("🔒 Admin Login", help="Switch to admin interface"):
            st.session_state.access_mode = "admin"
            st.rerun()
    
    st.markdown("---")
    
    # Show public dashboard
    show_public_dashboard()
    
    # Footer with navigation
    _show_public_footer()


def _show_admin_interface(auth: Authentication):
    """Show admin interface with authentication."""
    # Check if admin is logged in
    if not auth.is_admin_logged_in():
        # Show login form
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Show login form
            if auth.show_login_form():
                st.rerun()
        
        with col2:
            st.markdown("### 👥 Switch to Public View")
            if st.button("View Public Dashboard", type="secondary"):
                st.session_state.access_mode = "public"
                st.rerun()
            
            st.markdown("---")
            st.markdown(
                """
                ### 🔒 Admin Access
                
                The admin interface provides:
                - Data upload and management
                - Advanced analytics and forecasting
                - Probability scenario modeling
                - Risk assessment tools
                - Data export capabilities
                
                Contact the system administrator for login credentials.
                """
            )
    else:
        # Admin is logged in, show admin dashboard
        show_admin_dashboard()
        
        # Add footer navigation for admin
        _show_admin_footer()


def _show_public_footer():
    """Show footer for public interface."""
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.markdown("**Quick Links:**")
        st.markdown(
            """
            - [Parish Council Website](https://cawston-pc.org.uk)
            - [Meeting Minutes](https://cawston-pc.org.uk/minutes)
            - [Contact Information](https://cawston-pc.org.uk/contact)
            """
        )
    
    with col2:
        st.markdown("**About This Dashboard:**")
        st.markdown(
            """
            This public dashboard provides transparency into Cawston Parish Council's 
            financial position. Data is updated by council administrators following 
            monthly financial reviews.
            
            For detailed financial reports, please refer to the official council 
            meeting minutes available on the parish website.
            """
        )
    
    with col3:
        st.markdown("**Data Information:**")
        if 'data_version' in st.session_state and st.session_state.data_version > 0:
            st.success(f"Data Version: {st.session_state.data_version}")
        
        # Show last update info if available
        import datetime
        st.text(f"Page loaded: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")


def _show_admin_footer():
    """Show footer for admin interface."""
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("**Admin Tools:** Upload data | Manage reports | Export analysis | Configure settings")
    
    with col2:
        if st.button("👥 View Public Dashboard", key="admin_to_public"):
            # Keep admin logged in but switch to public view
            st.session_state.access_mode = "public"
            st.rerun()


def _handle_navigation():
    """Handle navigation between different views."""
    # Add navigation sidebar for admins
    if (st.session_state.get('access_mode') == 'admin' and 
        'admin_logged_in' in st.session_state and 
        st.session_state.admin_logged_in):
        
        with st.sidebar:
            st.markdown("### 🧭 Navigation")
            
            if st.button("📊 Public View"):
                st.session_state.access_mode = "public"
                st.rerun()
            
            st.markdown("---")
            
            # Show admin session info
            auth = Authentication()
            if 'admin_login_time' in st.session_state:
                from datetime import datetime, timedelta
                login_time = st.session_state.admin_login_time
                session_remaining = auth.session_timeout_minutes - (datetime.now() - login_time).seconds // 60
                
                if session_remaining > 0:
                    st.info(f"⏱️ Session: {session_remaining}min remaining")
                else:
                    st.warning("⚠️ Session expired")


def _check_environment():
    """Check environment setup and display warnings if needed."""
    warnings = []
    
    # Check if admin password is default
    default_password = 'cawston2024!'
    current_password = os.getenv('DASHBOARD_ADMIN_PASSWORD', default_password)
    
    if current_password == default_password:
        warnings.append(
            "⚠️ Using default admin password. Set DASHBOARD_ADMIN_PASSWORD environment variable for security."
        )
    
    # Display warnings in sidebar for admins
    if (warnings and 
        st.session_state.get('access_mode') == 'admin' and 
        st.session_state.get('admin_logged_in', False)):
        
        with st.sidebar:
            st.markdown("### ⚠️ System Warnings")
            for warning in warnings:
                st.warning(warning)


if __name__ == "__main__":
    # Check environment setup
    _check_environment()
    
    # Handle navigation
    _handle_navigation()
    
    # Run main application
    main()