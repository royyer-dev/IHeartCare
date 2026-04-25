"""
Módulos centrales de la aplicación IHeartCare.
Incluye autenticación, sidebar de navegación y tema visual.
"""

from .auth import login_user, logout_user, require_auth, hash_password
from .auth import verify_password, registrar_usuario_paciente, registrar_usuario_medico
from .sidebar import render_sidebar
from .theme import apply_global_theme
