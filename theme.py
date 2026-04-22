import streamlit as st

def apply_global_theme():
    """
    Aplica un tema profesional y refinado.
    Paleta: gris, azul oscuro, cian y verde.
    Minimalista, sin excesos visuales.
    """
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;500;600;700&display=swap');
    
    :root {
        /* Paleta de colores profesional */
        --color-primary: #1E40AF;          /* Azul oscuro */
        --color-primary-light: #3B82F6;    /* Azul claro */
        --color-primary-dark: #1e3a8a;     /* Azul más oscuro */
        --color-secondary: #0891B2;        /* Cian */
        --color-accent: #10B981;           /* Verde */
        
        /* Escala de grises */
        --color-text: #1F2937;             /* Gris oscuro (texto) */
        --color-text-light: #6B7280;       /* Gris medio */
        --color-bg-light: #F3F4F6;         /* Gris muy claro */
        --color-bg-lighter: #FFFFFF;       /* Blanco */
        --color-border: #D1D5DB;           /* Gris borde */
        
        /* Estados */
        --color-success: #10B981;
        --color-warning: #F59E0B;
        --color-danger: #EF4444;
        
        /* Tipografía */
        --font-body: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
        
        /* Espaciado */
        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --spacing-xl: 2rem;
        
        /* Sombras sutiles */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(16px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInDown {
        from {
            opacity: 0;
            transform: translateY(-16px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-16px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(16px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Estilos Base */
    html {
        scroll-behavior: smooth;
    }
    
    body {
        font-family: var(--font-body);
        color: var(--color-text);
        background-color: var(--color-bg-light);
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-body);
        font-weight: 600;
        color: var(--color-text);
        letter-spacing: -0.01em;
    }
    
    h1 { font-size: 2rem; line-height: 1.2; margin-bottom: var(--spacing-lg); }
    h2 { font-size: 1.5rem; line-height: 1.3; margin-bottom: var(--spacing-md); }
    h3 { font-size: 1.25rem; line-height: 1.4; margin-bottom: var(--spacing-sm); }
    
    p {
        line-height: 1.6;
        color: var(--color-text);
        font-size: 0.95rem;
    }
    
    /* Links */
    a {
        color: var(--color-primary);
        text-decoration: none;
        transition: color 0.2s ease;
    }
    
    a:hover {
        color: var(--color-primary-dark);
    }
    
    /* Botones */
    button {
        font-family: var(--font-body);
        font-weight: 500;
        border-radius: 0.375rem;
        transition: all 0.2s ease;
        border: none;
    }
    
    /* Inputs */
    input, select, textarea {
        font-family: var(--font-body);
        border: 1px solid var(--color-border);
        border-radius: 0.375rem;
        padding: 0.5rem 0.75rem;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    
    input:focus, select:focus, textarea:focus {
        outline: none;
        border-color: var(--color-primary);
        box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
    }
    
    /* Scroll Bar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--color-bg-light);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--color-border);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--color-text-light);
    }
    
    /* Dividers */
    hr {
        border: none;
        border-top: 1px solid var(--color-border);
        margin: var(--spacing-lg) 0;
    }
    
    </style>
    """, unsafe_allow_html=True)
