"""
설정 데이터 관리 클래스
ConfigViewModel에서 학점, 요일, 시간대 설정 책임을 분리
"""
from typing import Dict, List, Tuple


def normalize_time_str(time_str: str) -> str:
    """시간 문자열을 HH:MM 형태로 정규화 (예: '9:00' -> '09:00', '9' -> '09:00')"""
    if not time_str:
        return ""
    time_str = str(time_str).strip()
    if ':' in time_str:
        parts = time_str.split(':')
        h = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 and parts[1] else 0
    else:
        h = int(time_str)
        m = 0
    if 0 <= h <= 23 and 0 <= m <= 59:
        return f"{h:02d}:{m:02d}"
    return ""


class SettingsManager:
    """
    학점 범위, 공강 요일, 제외 시간대 관리 담당
    """
    
    def __init__(self, config_service):
        self.config_service = config_service
    
    def get_credits(self) -> Tuple[str, str]:
        """현재 학점 범위 반환"""
        config = self.config_service.get_config()
        if not config:
            return ("12", "18")
        return (str(config.min_credits), str(config.max_credits))
    
    def update_credits(self, min_credits: str, max_credits: str) -> bool:
        """학점 범위 업데이트"""
        try:
            min_val = int(min_credits)
            max_val = int(max_credits)
            
            if min_val > max_val:
                return False
            
            self.config_service.update_credits_range(min_val, max_val)
            return True
        except ValueError:
            return False
    
    def get_excluded_days(self) -> Dict[str, bool]:
        """공강 요일 정보 반환"""
        config = self.config_service.get_config()
        if not config:
            return {day: False for day in ['월', '화', '수', '목', '금']}
        
        return {day: (day in config.excluded_days) for day in ['월', '화', '수', '목', '금']}
    
    def update_excluded_days(self, day_vars: Dict) -> None:
        """공강 요일 업데이트"""
        excluded = []
        
        if isinstance(day_vars, dict):
            for d, v in day_vars.items():
                # CheckBox object handling
                is_checked = v.isChecked() if hasattr(v, 'isChecked') else v
                # BooleanVar handling
                if hasattr(v, 'get'):
                    is_checked = v.get()
                
                if is_checked:
                    excluded.append(d)
        
        self.config_service.update_excluded_days(excluded)
    
    def get_excluded_times(self) -> List[Tuple[str, str, str]]:
        """제외 시간대 목록 반환"""
        config = self.config_service.get_config()
        if not config or not hasattr(config, 'excluded_time_slots'):
            return []
        return config.excluded_time_slots
    
    def add_excluded_time(self, day: str, start_time: str, end_time: str) -> bool:
        """제외 시간대 추가 (검증 및 정규화 포함)"""
        try:
            start_norm = normalize_time_str(start_time)
            end_norm = normalize_time_str(end_time)
            if not start_norm or not end_norm:
                return False
            if start_norm >= end_norm:
                return False
            
            self.config_service.add_excluded_time_slot(day, start_norm, end_norm)
            return True
        except Exception:
            return False
    
    def remove_excluded_time(self, index: int) -> bool:
        """제외 시간대 삭제"""
        try:
            self.config_service.remove_excluded_time_slot(index)
            return True
        except Exception:
            return False
    
    def apply_all_settings(self, min_c: str, max_c: str, day_vars: Dict) -> bool:
        """모든 설정 한번에 적용"""
        # 학점 업데이트
        if not self.update_credits(min_c, max_c):
            return False
        
        # 공강 요일 업데이트
        self.update_excluded_days(day_vars)
        
        return True
