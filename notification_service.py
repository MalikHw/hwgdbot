import sys
import platform

class NotificationService:
    def __init__(self):
        self.os = platform.system()
        self.toaster = None
        
        # Initialize Windows toaster if on Windows
        if self.os == "Windows":
            try:
                from windows_toasts import Toast, WindowsToaster
                self.toaster = WindowsToaster("HwGDBot")
            except ImportError:
                print("windows-toasts not installed, notifications disabled")
    
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
            if self.toaster:
                from windows_toasts import Toast
                toast = Toast()
                toast.text_fields = [title, message]
                self.toaster.show_toast(toast)
            else:
                # Fallback
                print(f"[NOTIFICATION] {title}: {message}")
        except Exception as e:
            print(f"[NOTIFICATION] {title}: {message}")
            print(f"Toast error: {e}")
    
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