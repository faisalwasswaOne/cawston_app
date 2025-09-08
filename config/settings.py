import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import streamlit as st


@dataclass
class AppConfig:
    """Application configuration settings."""
    
    # Security settings
    admin_password: str = "admin_password"
    session_timeout_minutes: int = 30
    max_failed_login_attempts: int = 3
    
    # UI settings
    page_title: str = "Cawston Parish Council Financial Dashboard"
    page_icon: str = "💰"
    layout: str = "wide"
    
    # Contact information
    contact_email: str = "clerk@cawstonpc.org"
    website_url: str = "https://cawstonparishcouncil.gov.uk/"
    
    # Data settings
    max_file_size_mb: int = 10
    supported_file_types: list = None
    
    # Public interface settings
    show_contact_info: bool = True
    show_website_links: bool = True
    enable_search: bool = True
    
    # Financial settings
    default_currency: str = "GBP"
    currency_symbol: str = "£"
    
    # Chart settings
    default_chart_height: int = 500
    color_scheme: Dict[str, str] = None
    
    def __post_init__(self):
        if self.supported_file_types is None:
            self.supported_file_types = ['pdf', 'csv', 'xlsx']
        
        if self.color_scheme is None:
            self.color_scheme = {
                'budget': '#1f77b4',
                'actual': '#ff7f0e',
                'income': '#2ca02c',
                'expenditure': '#d62728',
                'positive': '#2ca02c',
                'negative': '#d62728',
                'neutral': '#7f7f7f',
                'primary': '#1f77b4',
                'secondary': '#ff7f0e'
            }


class ConfigManager:
    """Manage application configuration from various sources."""
    
    def __init__(self):
        self._config: Optional[AppConfig] = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from Streamlit secrets, environment variables, and defaults."""
        config_data = {}
        
        # Try to load from Streamlit secrets first (for Streamlit Cloud)
        try:
            if hasattr(st, 'secrets') and 'dashboard' in st.secrets:
                secrets = st.secrets['dashboard']
                config_data['admin_password'] = secrets.get('admin_password', 'admin_password')
                config_data['session_timeout_minutes'] = int(secrets.get('session_timeout_minutes', '30'))
                config_data['contact_email'] = secrets.get('contact_email', 'clerk@cawstonpc.org')
                config_data['website_url'] = secrets.get('website_url', 'https://cawstonparishcouncil.gov.uk/')
                config_data['max_file_size_mb'] = int(secrets.get('max_file_size_mb', '10'))
                config_data['page_title'] = secrets.get('page_title', 'Cawston Parish Council Financial Dashboard')
                config_data['show_contact_info'] = secrets.get('show_contact_info', True)
                config_data['show_website_links'] = secrets.get('show_website_links', True)
                config_data['enable_search'] = secrets.get('enable_search', True)
            else:
                # Fall back to environment variables and defaults
                self._load_from_env(config_data)
        except:
            # Fall back to environment variables if secrets fail
            self._load_from_env(config_data)
        
        self._config = AppConfig(**config_data)
    
    def _load_from_env(self, config_data):
        """Load from environment variables and defaults."""
        # Load from environment variables
        config_data['admin_password'] = os.getenv('DASHBOARD_ADMIN_PASSWORD', 'admin_password')
        config_data['session_timeout_minutes'] = int(os.getenv('SESSION_TIMEOUT_MINUTES', '30'))
        config_data['contact_email'] = os.getenv('CONTACT_EMAIL', 'clerk@cawstonpc.org')
        config_data['website_url'] = os.getenv('WEBSITE_URL', 'https://cawstonparishcouncil.gov.uk/')
        config_data['max_file_size_mb'] = int(os.getenv('MAX_FILE_SIZE_MB', '10'))
        
        # Boolean settings
        config_data['show_contact_info'] = os.getenv('SHOW_CONTACT_INFO', 'true').lower() == 'true'
        config_data['show_website_links'] = os.getenv('SHOW_WEBSITE_LINKS', 'true').lower() == 'true'
        config_data['enable_search'] = os.getenv('ENABLE_SEARCH', 'true').lower() == 'true'
        
        # Page settings
        config_data['page_title'] = os.getenv('PAGE_TITLE', 'Cawston Parish Council Financial Dashboard')
        config_data['page_icon'] = os.getenv('PAGE_ICON', '💰')
    
    def get_config(self) -> AppConfig:
        """Get the current configuration."""
        if self._config is None:
            self._load_config()
        return self._config
    
    def reload_config(self):
        """Reload configuration from sources."""
        self._load_config()
    
    def get_streamlit_config(self) -> Dict[str, Any]:
        """Get configuration dict for Streamlit page config."""
        config = self.get_config()
        return {
            'page_title': config.page_title,
            'page_icon': config.page_icon,
            'layout': config.layout,
            'menu_items': {
                'Get Help': f'mailto:{config.contact_email}',
                'Report a bug': f'mailto:{config.contact_email}',
                'About': f"""
                # {config.page_title}
                
                This dashboard provides transparency into council finances with:
                - Public view for residents and stakeholders  
                - Admin interface for financial management
                
                For questions, contact the Parish Clerk.
                Website: {config.website_url}
                """
            }
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security-related configuration."""
        config = self.get_config()
        return {
            'admin_password': config.admin_password,
            'session_timeout_minutes': config.session_timeout_minutes,
            'max_failed_login_attempts': config.max_failed_login_attempts
        }
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI-related configuration."""
        config = self.get_config()
        return {
            'show_contact_info': config.show_contact_info,
            'show_website_links': config.show_website_links,
            'enable_search': config.enable_search,
            'color_scheme': config.color_scheme,
            'default_chart_height': config.default_chart_height,
            'currency_symbol': config.currency_symbol
        }
    
    def get_file_config(self) -> Dict[str, Any]:
        """Get file handling configuration."""
        config = self.get_config()
        return {
            'max_file_size_mb': config.max_file_size_mb,
            'supported_file_types': config.supported_file_types
        }
    
    def update_config_value(self, key: str, value: Any, persist: bool = False):
        """Update a configuration value."""
        if hasattr(self._config, key):
            setattr(self._config, key, value)
            
            if persist:
                # In a production environment, you might want to persist to a config file
                # For now, we'll just set it in the current session
                st.session_state[f'config_{key}'] = value
    
    def is_development_mode(self) -> bool:
        """Check if running in development mode."""
        return os.getenv('DASHBOARD_DEV_MODE', 'false').lower() == 'true'
    
    def get_environment_info(self) -> Dict[str, str]:
        """Get environment information for debugging."""
        return {
            'environment': os.getenv('DASHBOARD_ENV', 'production'),
            'version': os.getenv('DASHBOARD_VERSION', '1.0.0'),
            'deployment': os.getenv('DASHBOARD_DEPLOYMENT', 'local'),
            'debug_mode': str(self.is_development_mode())
        }


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get the current application configuration."""
    return get_config_manager().get_config()


# Convenience functions for common config access
def get_admin_password() -> str:
    """Get admin password from config."""
    return get_config().admin_password


def get_session_timeout() -> int:
    """Get session timeout in minutes."""
    return get_config().session_timeout_minutes


def get_contact_email() -> str:
    """Get contact email from config."""
    return get_config().contact_email


def get_website_url() -> str:
    """Get website URL from config."""
    return get_config().website_url


def get_color_scheme() -> Dict[str, str]:
    """Get color scheme configuration."""
    return get_config().color_scheme


def get_currency_symbol() -> str:
    """Get currency symbol."""
    return get_config().currency_symbol


# Environment validation
def validate_environment() -> list:
    """Validate environment configuration and return list of warnings."""
    warnings = []
    config = get_config()
    
    # Check for default password
    if config.admin_password == 'cawston2024!':
        warnings.append(
            "Using default admin password. Set DASHBOARD_ADMIN_PASSWORD environment variable."
        )
    
    # Check for required environment variables in production
    if not get_config_manager().is_development_mode():
        required_env_vars = [
            'DASHBOARD_ADMIN_PASSWORD',
            'CONTACT_EMAIL'
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                warnings.append(f"Production environment missing {var}")
    
    # Validate file size limits
    if config.max_file_size_mb > 50:
        warnings.append("File size limit is very high (>50MB)")
    
    return warnings