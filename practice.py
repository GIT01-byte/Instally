# import tkinter as tk

# root = tk.Tk()
# root.title("FSFASF")
# root.geometry("300x200")

# # [Здесь создаются виджеты]
# label = tk.Label(root, text="FSAS")
# label.pack()

# btn = tk.Button(root, text="FSAS")
# btn.pack()

# entry = tk.Entry(root, width=20)
# entry.pack()


# def show_text_entry():
#     entry_text = entry.get()
#     entry_input = tk.Label(root, text=entry_text)
#     entry_input.pack()


# sbmt_btn = tk.Button(root, text="Отправить текст", command=show_text_entry)
# sbmt_btn.pack()


# def show_text():
#     user_text = entry.get()
#     # Меняем текст у существующей метки (Label)
#     result_label.config(text=f"Вы написали: {user_text}")


# entry = tk.Entry(root, width=20)
# entry.pack(pady=10)

# btn = tk.Button(root, text="Отобразить на экране", command=show_text)
# btn.pack(pady=5)

# # Создаем пустую метку под кнопкой, куда и пойдет текст
# result_label = tk.Label(root, text="", font=("Arial", 10, "bold"))
# result_label.pack(pady=10)


# from tkinter import messagebox

# messagebox.showinfo("Заголовок", "Операция выполнена успешно!")
# messagebox.showerror("Ошибка", "Доступ запрещен!")


# root.mainloop()


import os

choco_path = "C:/Programming/Projects/SISADMIN_PROGRAMM/choco_files/tools/chocolateyInstall/choco.exe"
choco_dir = r"C:\\Programming\\Projects\\SISADMIN_PROGRAMM\\choco_files"

if not os.path.exists(choco_path):
    error_msg = f"Файл choco.exe отсутствует по указанному пути: {choco_path}"
    raise FileNotFoundError(error_msg)
print("11")

