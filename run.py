import sys
import os

# Custom module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication

def main():
    # Initialize PySide6 App (Must be first)
    app = QApplication(sys.argv)

    # Defer imports to avoid early QWidget creation
    from schedule_maker.controllers.app_controller import AppController
    from schedule_maker.ui.main_window import MainWindow
    # ConfigInterface imported inside MainWindow typically, but if needed here for check:
    # from schedule_maker.ui.interfaces.config_interface import ConfigInterface 
    
    from qfluentwidgets import setTheme, Theme, qconfig
    
    # Force Light Theme
    qconfig.theme = Theme.LIGHT
    qconfig.save() 
    setTheme(Theme.LIGHT)

    # PyInstaller Path Handling
    if getattr(sys, 'frozen', False):
        resource_path = sys._MEIPASS
        # EXE location for data storage
        data_path = os.path.dirname(sys.executable)
    else:
        # Script location
        resource_path = os.path.dirname(os.path.abspath(__file__))
        data_path = resource_path
        
    # Ensure data directory exists
    os.makedirs(os.path.join(data_path, 'data'), exist_ok=True)
    
    # Initialize Controller
    controller = AppController(resource_path=resource_path, data_path=data_path)
    if not controller.initialize():
        print("Failed to initialize application.")
        return

    # Create Main Window
    window = MainWindow(controller)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
