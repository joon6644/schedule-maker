"""
기본 ViewModel 클래스
모든 ViewModel의 부모 클래스로, 데이터 바인딩 및 공통 기능 제공
"""
from typing import Callable, Any, List, Dict
import threading

class BaseViewModel:
    """
    Observer 패턴을 사용한 기본 ViewModel
    """
    
    def __init__(self):
        self._observers: Dict[str, List[Callable[[Any], None]]] = {}
        self._error_handler: Callable[[str, str], None] = None
        self._interaction_service = None
        
    def bind(self, property_name: str, callback: Callable[[Any], None]):
        """
        속성 변경 감시자 등록
        
        Args:
            property_name: 감시할 속성 이름
            callback: 변경 시 호출될 콜백 함수 (new_value 인자 받음)
        """
        if property_name not in self._observers:
            self._observers[property_name] = []
        self._observers[property_name].append(callback)
        
    def notify(self, property_name: str, new_value: Any):
        """
        속성 변경 알림
        """
        if property_name in self._observers:
            for callback in self._observers[property_name]:
                # UI 스레드 안전성 확보를 위해 필요하다면 여기서 처리 가능
                # 현재는 직접 호출 (Tkinter는 메인 스레드에서만 업데이트해야 함에 유의)
                try:
                    callback(new_value)
                except Exception as e:
                    print(f"Error notifying observer for {property_name}: {e}")

    def set_interaction_service(self, service):
        """사용자 상호작용 서비스 설정"""
        self._interaction_service = service
        
    def show_error(self, title: str, message: str):
        """에러 메시지 표시"""
        if self._interaction_service:
            self._interaction_service.show_error(title, message)
        else:
            print(f"[ERROR] {title}: {message}")

    def show_info(self, title: str, message: str):
        """정보 메시지 표시"""
        if self._interaction_service:
            self._interaction_service.show_info(title, message)
        else:
            print(f"[INFO] {title}: {message}")
