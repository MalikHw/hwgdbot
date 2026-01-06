import sys
import platform

class NotificationService:
    def __init__(self):
        self.os = platform.system()
    
    def show_success(self, message: str):
        self._show_notification("HwGDBot - Success", message, "info")
    
    def show_error(self, message: str):
        self._show_notification("HwGDBot - Error", message, "error")
    
    def show_warning(self, message: str):
        self._show_notification("HwGDBot - Warning", message, "warning")
    
    def _show_notification(self, title: str, message: str, level: str):
        if self.os == "Windows":
            self._windows_toast(title, message)
        elif self.os == "Linux":
            self._linux_toast(title, message)
        elif self.os == "Darwin":  # macOS
            self._macos_toast(title, message)
    
    def _windows_toast(self, title: str, message: str):
        try:
            from win10toast import ToastNotifier
            toaster = ToastNotifier()
            toaster.show_toast(title, message, duration=3, threaded=True)
        except ImportError:
            # Fallback: use system tray
            print(f"[NOTIFICATION] {title}: {message}")
    
    def _linux_toast(self, title: str, message: str):
        try:
            import subprocess
            subprocess.run(['notify-send', title, message], check=False)
        except:
            print(f"[NOTIFICATION] {title}: {message}")
    
    def _macos_toast(self, title: str, message: str):
        try:
            import subprocess
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], check=False)
        except:
            print(f"[NOTIFICATION] {title}: {message}")
