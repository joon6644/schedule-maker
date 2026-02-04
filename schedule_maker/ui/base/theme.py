"""
UI 테마 설정 모듈
현대적인 색상 팔레트와 디자인 토큰 제공
"""


class AppTheme:
    """애플리케이션 테마 싱글톤 클래스"""
    
    # ===== 색상 팔레트 =====
    # Primary Colors (인디고)
    PRIMARY = '#6366f1'
    PRIMARY_DARK = '#4f46e5'
    PRIMARY_LIGHT = '#818cf8'
    PRIMARY_LIGHTER = '#a5b4fc'
    
    # Secondary Colors (보라)
    SECONDARY = '#8b5cf6'
    SECONDARY_DARK = '#7c3aed'
    SECONDARY_LIGHT = '#a78bfa'
    
    # Accent Colors
    ACCENT = '#ec4899'
    ACCENT_DARK = '#db2777'
    ACCENT_LIGHT = '#f472b6'
    
    # Semantic Colors
    SUCCESS = '#10b981'
    SUCCESS_LIGHT = '#34d399'
    WARNING = '#f59e0b'
    WARNING_LIGHT = '#fbbf24'
    DANGER = '#ef4444'
    DANGER_LIGHT = '#f87171'
    INFO = '#3b82f6'
    INFO_LIGHT = '#60a5fa'
    
    # Neutral Colors (슬레이트)
    BACKGROUND = '#f8fafc'
    SURFACE = '#ffffff'
    SURFACE_HOVER = '#f1f5f9'
    
    BORDER = '#e2e8f0'
    BORDER_LIGHT = '#f1f5f9'
    DIVIDER = '#cbd5e0'
    
    TEXT_PRIMARY = '#1e293b'
    TEXT_SECONDARY = '#64748b'
    TEXT_TERTIARY = '#94a3b8'
    TEXT_DISABLED = '#cbd5e0'
    
    # Dark Theme (향후 지원)
    DARK_BG = '#0f172a'
    DARK_SURFACE = '#1e293b'
    DARK_TEXT = '#f1f5f9'
    
    # ===== 타이포그래피 =====
    FONT_FAMILY = "'Segoe UI', 'Malgun Gothic', system-ui, -apple-system, sans-serif"
    
    # Font Sizes
    FONT_SIZE_TITLE = 24
    FONT_SIZE_HEADING = 18
    FONT_SIZE_SUBHEADING = 16
    FONT_SIZE_BODY = 14
    FONT_SIZE_CAPTION = 12
    FONT_SIZE_SMALL = 11
    
    # Font Weights
    FONT_WEIGHT_LIGHT = 300
    FONT_WEIGHT_NORMAL = 400
    FONT_WEIGHT_MEDIUM = 500
    FONT_WEIGHT_SEMIBOLD = 600
    FONT_WEIGHT_BOLD = 700
    
    # ===== 간격 시스템 =====
    SPACE_XS = 4
    SPACE_S = 8
    SPACE_M = 16
    SPACE_L = 24
    SPACE_XL = 32
    SPACE_XXL = 48
    
    # ===== Border Radius =====
    RADIUS_SM = 4
    RADIUS_MD = 8
    RADIUS_LG = 12
    RADIUS_XL = 16
    RADIUS_FULL = 9999
    
    # ===== 그림자 =====
    SHADOW_SM = '0 1px 2px rgba(0, 0, 0, 0.05)'
    SHADOW_MD = '0 4px 6px rgba(0, 0, 0, 0.07)'
    SHADOW_LG = '0 10px 15px rgba(0, 0, 0, 0.1)'
    SHADOW_XL = '0 20px 25px rgba(0, 0, 0, 0.15)'
    
    # ===== 애니메이션 타이밍 =====
    TRANSITION_FAST = 150  # ms
    TRANSITION_NORMAL = 200  # ms
    TRANSITION_SLOW = 300  # ms
    
    # ===== 특수 효과 색상 =====
    GLASS_BG = 'rgba(255, 255, 255, 0.8)'
    GLASS_BORDER = 'rgba(255, 255, 255, 0.3)'
    OVERLAY = 'rgba(0, 0, 0, 0.5)'
    OVERLAY_LIGHT = 'rgba(0, 0, 0, 0.2)'
    
    # ===== Helper 메서드 =====
    @staticmethod
    def get_hover_color(base_color: str) -> str:
        """주어진 색상의 호버 상태 색상 반환 (조금 더 어둡게)"""
        color_map = {
            AppTheme.PRIMARY: AppTheme.PRIMARY_DARK,
            AppTheme.SECONDARY: AppTheme.SECONDARY_DARK,
            AppTheme.ACCENT: AppTheme.ACCENT_DARK,
            AppTheme.SUCCESS: '#059669',
            AppTheme.WARNING: '#d97706',
            AppTheme.DANGER: '#dc2626',
            AppTheme.SURFACE: AppTheme.SURFACE_HOVER,
        }
        return color_map.get(base_color, base_color)
    
    @staticmethod
    def rgba(hex_color: str, alpha: float) -> str:
        """Hex 색상을 RGBA로 변환 (투명도 추가)"""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
            return f'rgba({r}, {g}, {b}, {alpha})'
        return hex_color
    
    @classmethod
    def get_button_style(cls, variant='primary'):
        """버튼 스타일 프리셋 반환"""
        styles = {
            'primary': {
                'bg': cls.PRIMARY,
                'fg': '#ffffff',
                'hover_bg': cls.PRIMARY_DARK,
                'active_bg': '#3730a3',
            },
            'secondary': {
                'bg': cls.SECONDARY,
                'fg': '#ffffff',
                'hover_bg': cls.SECONDARY_DARK,
                'active_bg': '#6d28d9',
            },
            'accent': {
                'bg': cls.ACCENT,
                'fg': '#ffffff',
                'hover_bg': cls.ACCENT_DARK,
                'active_bg': '#be185d',
            },
            'danger': {
                'bg': cls.DANGER,
                'fg': '#ffffff',
                'hover_bg': '#dc2626',
                'active_bg': '#b91c1c',
            },
            'ghost': {
                'bg': cls.SURFACE,
                'fg': cls.TEXT_PRIMARY,
                'hover_bg': cls.SURFACE_HOVER,
                'active_bg': cls.BORDER,
            },
            'outline': {
                'bg': cls.SURFACE,
                'fg': cls.PRIMARY,
                'hover_bg': cls.PRIMARY_LIGHTER,
                'active_bg': cls.PRIMARY_LIGHT,
                'border': cls.PRIMARY,
            },
        }
        return styles.get(variant, styles['primary'])


# 전역 테마 인스턴스
theme = AppTheme()
