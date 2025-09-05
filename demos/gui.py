"""Ví dụ giao diện đồ họa đơn giản cho mijiaAPI.

Cho phép đăng nhập bằng mã QR và hiển thị danh sách thiết bị.
"""

import tkinter as tk
from tkinter import messagebox

from mijiaAPI import mijiaLogin, mijiaAPI


class MijiaGUI(tk.Tk):
    """Cửa sổ chính của ứng dụng."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Mijia API GUI")
        self.api: mijiaAPI | None = None

        tk.Button(self, text="Đăng nhập bằng QR", command=self.login_qr).pack(pady=5)
        tk.Button(self, text="Lấy danh sách thiết bị", command=self.list_devices).pack(pady=5)

        self.text = tk.Text(self, width=60, height=20)
        self.text.pack(padx=5, pady=5)

    def login_qr(self) -> None:
        """Đăng nhập tài khoản Mi thông qua mã QR."""

        login = mijiaLogin()
        try:
            auth = login.QRlogin()
            self.api = mijiaAPI(auth)
            messagebox.showinfo("Thông báo", "Đăng nhập thành công")
        except Exception as exc:  # pragma: no cover - phụ thuộc môi trường
            messagebox.showerror("Lỗi", str(exc))

    def list_devices(self) -> None:
        """Lấy và hiển thị danh sách thiết bị."""

        if not self.api:
            messagebox.showwarning("Cảnh báo", "Vui lòng đăng nhập trước")
            return
        try:
            devices = self.api.get_devices_list()
            self.text.delete("1.0", tk.END)
            for dev in devices:
                self.text.insert(tk.END, f"{dev['name']} ({dev['model']})\n")
        except Exception as exc:  # pragma: no cover - phụ thuộc môi trường
            messagebox.showerror("Lỗi", str(exc))


if __name__ == "__main__":
    app = MijiaGUI()
    app.mainloop()

