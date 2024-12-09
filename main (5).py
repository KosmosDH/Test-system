import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import firebase_admin
from firebase_admin import credentials, firestore

# Инициализация Firebase
cred = credentials.Certificate("testsystem-78c54-firebase-adminsdk-ab2tu-4e8ac76af3.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Функция регистрации пользователя
def register_user():
    username = reg_username_entry.get().strip()
    password = reg_password_entry.get().strip()
    role = role_var.get()
    class_grade = reg_class_entry.get().strip() if role == "student" else None

    if not username or not password or not role:
        messagebox.showerror("Ошибка", "Заполните все поля!")
        return

    if role == "student" and not class_grade:
        messagebox.showerror("Ошибка", "Укажите класс для ученика!")
        return

    try:
        user_data = {
            "username": username,
            "password": password,
            "role": role,
            "class_grade": class_grade
        }
        db.collection("users").add(user_data)
        messagebox.showinfo("Успешно", "Регистрация прошла успешно!")
        reg_window.destroy()
    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

# Глобальная переменная для хранения текущего пользователя
current_user = None

# Функция входа пользователя
def login_user():
    global current_user
    username = login_username_entry.get().strip()
    password = login_password_entry.get().strip()

    users_ref = db.collection("users")
    query = users_ref.where("username", "==", username).where("password", "==", password).stream()

    result = list(query)
    if result:
        user_data = result[0].to_dict()
        current_user = username
        messagebox.showinfo("Успешно", f"Вы вошли как {user_data['role'].capitalize()}!")
        login_window.destroy()
        if user_data['role'] == "teacher":
            open_teacher_dashboard(user_data)
        elif user_data['role'] == "student":
            open_student_dashboard(user_data['class_grade'])
    else:
        messagebox.showerror("Ошибка", "Неправильное имя пользователя или пароль!")

# Окно регистрации
def open_register_window():
    global reg_window, reg_username_entry, reg_password_entry, reg_class_entry, role_var

    reg_window = ctk.CTkToplevel()
    reg_window.title("Регистрация")
    reg_window.geometry("400x400")

    ctk.CTkLabel(reg_window, text="Регистрация", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

    ctk.CTkLabel(reg_window, text="Имя пользователя").pack(pady=5)
    reg_username_entry = ctk.CTkEntry(reg_window, width=300)
    reg_username_entry.pack(pady=5)

    ctk.CTkLabel(reg_window, text="Пароль").pack(pady=5)
    reg_password_entry = ctk.CTkEntry(reg_window, show="*", width=300)
    reg_password_entry.pack(pady=5)

    ctk.CTkLabel(reg_window, text="Роль").pack(pady=5)
    role_var = ctk.StringVar(value="student")
    ctk.CTkRadioButton(reg_window, text="Учитель", variable=role_var, value="teacher").pack(pady=5)
    ctk.CTkRadioButton(reg_window, text="Ученик", variable=role_var, value="student").pack(pady=5)

    ctk.CTkLabel(reg_window, text="Класс (только для учеников)").pack(pady=5)
    reg_class_entry = ctk.CTkEntry(reg_window, width=300)
    reg_class_entry.pack(pady=5)

    ctk.CTkButton(reg_window, text="Зарегистрироваться", command=register_user).pack(pady=20)


# Панель учителя
def open_teacher_dashboard(user_data):
    teacher_window = ctk.CTk()
    teacher_window.title("Панель учителя")
    teacher_window.geometry("500x400")

    ctk.CTkLabel(teacher_window, text="Добро пожаловать, Учитель!", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

    ctk.CTkButton(teacher_window, text="Создать тест", command=lambda: open_create_test_window(user_data),
                  width=250, height=50, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

    ctk.CTkButton(teacher_window, text="Просмотреть результаты", command=lambda: open_view_results_window(user_data),
                  width=250, height=50, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

    teacher_window.mainloop()

def open_view_results_window(user_data):
    results_window = ctk.CTkToplevel()
    results_window.title("Результаты тестов")
    results_window.geometry("500x400")

    ctk.CTkLabel(results_window, text="Результаты тестов", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

    # Создаем рамку с прокруткой
    frame = ctk.CTkFrame(results_window)
    frame.pack(fill=ctk.BOTH, expand=True)

    canvas = ctk.CTkCanvas(frame)
    scrollbar = ctk.CTkScrollbar(frame, orientation="vertical", command=canvas.yview)
    scrollable_frame = ctk.CTkFrame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Получение тестов, созданных учителем
    tests_ref = db.collection("tests").where("teacher_id", "==", user_data['username']).stream()
    tests = list(tests_ref)

    if not tests:
        ctk.CTkLabel(scrollable_frame, text="Вы еще не создали ни одного теста.", font=ctk.CTkFont(size=14)).pack(pady=10)
    else:
        for test in tests:
            test_data = test.to_dict()
            ctk.CTkButton(scrollable_frame, text=test_data['title'], font=ctk.CTkFont(size=14, weight="bold"),
                          width=300, height=40,
                          command=lambda t_id=test.id: show_test_results(t_id)).pack(pady=5)


# Окно результатов теста
def show_test_results(test_id):
    test_results_window = ctk.CTkToplevel()
    test_results_window.title("Результаты теста")
    test_results_window.geometry("500x400")

    test_data = db.collection("tests").document(test_id).get().to_dict()
    ctk.CTkLabel(test_results_window, text=f"Результаты теста: {test_data['title']}", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

    # Создаем рамку с прокруткой
    frame = ctk.CTkFrame(test_results_window)
    frame.pack(fill=ctk.BOTH, expand=True)
    canvas = ctk.CTkCanvas(frame)
    scrollbar = ctk.CTkScrollbar(frame, orientation="vertical", command=canvas.yview)
    scrollable_frame = ctk.CTkFrame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Получение результатов
    results_ref = db.collection("results").where("test_id", "==", test_id).stream()
    results = list(results_ref)

    if not results:
        ctk.CTkLabel(scrollable_frame, text="Никто еще не прошел этот тест.", font=ctk.CTkFont(size=14)).pack(pady=10)
    else:
        for result in results:
            result_data = result.to_dict()

            # Получение данных студента
            student_ref = db.collection("users").where("username", "==", result_data['student_id']).stream()
            student = list(student_ref)[0].to_dict() if student_ref else {}

            student_info = f"Ученик: {student.get('username', 'Неизвестно')} ({student.get('class_grade', '-')})"
            score_info = f"Результат: {result_data['score']}"
            ctk.CTkLabel(scrollable_frame, text=f"{student_info} - {score_info}", font=ctk.CTkFont(size=14)).pack(pady=5)

# Функция создания теста
def open_create_test_window(user_data):
    create_test_window = ctk.CTkToplevel()
    create_test_window.title("Создать тест")
    create_test_window.geometry("400x400")

    ctk.CTkLabel(create_test_window, text="Создание теста", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

    ctk.CTkLabel(create_test_window, text="Название теста", font=ctk.CTkFont(size=14)).pack(pady=5)
    test_title_entry = ctk.CTkEntry(create_test_window, width=350, height=40, font=ctk.CTkFont(size=14))
    test_title_entry.pack(pady=5)

    ctk.CTkLabel(create_test_window, text="Класс (например, 11А)", font=ctk.CTkFont(size=14)).pack(pady=5)
    class_entry = ctk.CTkEntry(create_test_window, width=350, height=40, font=ctk.CTkFont(size=14))
    class_entry.pack(pady=5)

    def save_test():
        test_title = test_title_entry.get().strip()
        class_grade = class_entry.get().strip()

        if not test_title or not class_grade:
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return

        test_data = {
            "teacher_id": user_data['username'],
            "title": test_title,
            "class_grade": class_grade
        }

        try:
            # Добавляем тест и получаем ссылку на документ
            _, test_ref = db.collection("tests").add(test_data)
            messagebox.showinfo("Успешно", "Тест создан! Теперь добавьте вопросы.")
            create_questions_window(test_ref)  # Передаем ID теста
            create_test_window.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать тест: {str(e)}")

    ctk.CTkButton(create_test_window, text="Создать тест", command=save_test,
                  width=250, height=50, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)


# Функция добавления вопросов
def create_questions_window(test_ref):
    questions_window = ctk.CTkToplevel()
    questions_window.title("Добавить вопросы")
    questions_window.geometry("500x500")

    ctk.CTkLabel(questions_window, text="Добавление вопросов", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)

    ctk.CTkLabel(questions_window, text="Текст вопроса", font=ctk.CTkFont(size=14)).pack(pady=5)
    question_text_entry = ctk.CTkEntry(questions_window, width=400, height=40, font=ctk.CTkFont(size=14))
    question_text_entry.pack(pady=5)

    ctk.CTkLabel(questions_window, text="Тип вопроса", font=ctk.CTkFont(size=14)).pack(pady=5)
    question_type_var = ctk.StringVar(value="multiple_choice")
    ctk.CTkRadioButton(questions_window, text="С выбором ответа", variable=question_type_var, value="multiple_choice",
                       font=ctk.CTkFont(size=14)).pack(pady=5)
    ctk.CTkRadioButton(questions_window, text="Свободный ответ", variable=question_type_var, value="open",
                       font=ctk.CTkFont(size=14)).pack(pady=5)

    ctk.CTkLabel(questions_window, text="Варианты ответа (через запятую)", font=ctk.CTkFont(size=14)).pack(pady=5)
    options_entry = ctk.CTkEntry(questions_window, width=400, height=40, font=ctk.CTkFont(size=14))
    options_entry.pack(pady=5)
    ctk.CTkLabel(questions_window, text="Правильный ответ", font=ctk.CTkFont(size=14)).pack(pady=5)
    correct_answer_entry = ctk.CTkEntry(questions_window, width=400, height=40, font=ctk.CTkFont(size=14))
    correct_answer_entry.pack(pady=5)

    def save_question():
        question_text = question_text_entry.get().strip()
        question_type = question_type_var.get()
        options = options_entry.get().strip()
        correct_answer = correct_answer_entry.get().strip()

        if not question_text or (question_type == "multiple_choice" and (not options or not correct_answer)):
            messagebox.showerror("Ошибка", "Заполните все необходимые поля!")
            return

        question_data = {
            "test_id": test_ref.id,  # Используем test_id, который мы передали
            "question_text": question_text,
            "options": options.split(","),
            "correct_answer": correct_answer,
            "question_type": question_type
        }
        db.collection("questions").add(question_data)
        messagebox.showinfo("Успешно", "Вопрос добавлен!")
        question_text_entry.delete(0, tk.END)
        options_entry.delete(0, tk.END)
        correct_answer_entry.delete(0, tk.END)

    ctk.CTkButton(questions_window, text="Добавить вопрос", command=save_question,
                  width=250, height=50, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)

# Панель ученика
def open_student_dashboard(class_grade):
    student_window = ctk.CTk()
    student_window.title("Панель ученика")
    student_window.geometry("500x400")

    ctk.CTkLabel(student_window, text=f"Добро пожаловать, Ученик {class_grade}!", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=10)
    ctk.CTkLabel(student_window, text="Доступные тесты:", font=ctk.CTkFont(size=14)).pack(pady=5)

    # Создаем рамку с прокруткой
    frame = ctk.CTkFrame(student_window)
    frame.pack(fill=ctk.BOTH, expand=True)

    canvas = ctk.CTkCanvas(frame)
    scrollbar = ctk.CTkScrollbar(frame, orientation="vertical", command=canvas.yview)
    scrollable_frame = ctk.CTkFrame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Функция для обновления доступных тестов
    def update_tests():
        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        # Получение тестов для класса
        tests_ref = db.collection("tests").where("class_grade", "==", class_grade).stream()
        tests = list(tests_ref)

        if not tests:
            ctk.CTkLabel(scrollable_frame, text="Нет доступных тестов.", font=ctk.CTkFont(size=14)).pack(pady=10)
        else:
            for test in tests:
                test_data = test.to_dict()
                # Проверяем, проходил ли студент этот тест
                student_results_ref = db.collection("results").where("student_id", "==", current_user).where(
                    "test_id", "==", test.id).stream()
                results = list(student_results_ref)

                if not results:  # Если тест еще не пройден
                    ctk.CTkButton(scrollable_frame, text=test_data['title'], font=ctk.CTkFont(size=14, weight="bold"),
                                  width=300, height=40,
                                  command=lambda t_id=test.id: start_test(t_id, student_window, update_tests)).pack(pady=5)

    update_tests()
    student_window.mainloop()


# Функция начала прохождения теста
def start_test(test_id, parent_window, update_tests):
    parent_window.withdraw()  # Скрываем главное окно вместо закрытия
    questions_ref = db.collection("questions").where("test_id", "==", test_id).stream()
    questions = list(questions_ref)

    if not questions:
        messagebox.showerror("Ошибка", "У этого теста нет вопросов.")
        parent_window.deiconify()  # Показываем главное окно обратно
        return

    test_window = ctk.CTkToplevel()
    test_window.title("Прохождение теста")
    test_window.geometry("500x400")

    current_question_index = [0]  # Для отслеживания текущего вопроса
    user_answers = []  # Для хранения ответов пользователя

    def show_question(index):
        for widget in test_window.winfo_children():
            widget.destroy()

        if index >= len(questions):
            calculate_result(user_answers, test_id)
            test_window.destroy()
            parent_window.deiconify()  # Показываем главное окно после завершения теста
            update_tests()  # Обновляем список доступных тестов
            return

        question_data = questions[index].to_dict()
        ctk.CTkLabel(test_window, text=f"Вопрос {index + 1}/{len(questions)}", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        ctk.CTkLabel(test_window, text=question_data['question_text'], font=ctk.CTkFont(size=14)).pack(pady=10)

        if question_data['question_type'] == "multiple_choice":
            answer_var = ctk.StringVar(value="")
            for option in question_data.get('options', []):
                ctk.CTkRadioButton(test_window, text=option, variable=answer_var, value=option, font=ctk.CTkFont(size=14)).pack(anchor="w")

            def save_answer():
                if not answer_var.get():
                    messagebox.showwarning("Ошибка", "Выберите ответ перед продолжением!")
                    return
                user_answers.append(answer_var.get())
                current_question_index[0] += 1
                show_question(current_question_index[0])

            ctk.CTkButton(test_window, text="Ответить", command=save_answer, width=200, height=40, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        elif question_data['question_type'] == "open":
            answer_entry = ctk.CTkEntry(test_window, width=400, height=40, font=ctk.CTkFont(size=14))
            answer_entry.pack(pady=5)

            def save_answer():
                user_answers.append(answer_entry.get().strip())
                current_question_index[0] += 1
                show_question(current_question_index[0])

            ctk.CTkButton(test_window, text="Ответить", command=save_answer, width=200, height=40, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

    show_question(current_question_index[0])  # Показываем первый вопрос

# Функция подсчета результатов теста
def calculate_result(user_answers, test_id):
    # Без изменений
    correct_answers = []
    questions_ref = db.collection("questions").where("test_id", "==", test_id).stream()
    for question in questions_ref:
        correct_answers.append(question.to_dict()['correct_answer'])

    score = 0
    for user_answer, correct_answer in zip(user_answers, correct_answers):
        if user_answer.strip().lower() == correct_answer.strip().lower():
            score += 1

    # Используем глобальную переменную current_user
    student_data = db.collection("users").where("username", "==", current_user).stream()
    student_id = list(student_data)[0].to_dict()['username']
    result_data = {
        "student_id": student_id,
        "test_id": test_id,
        "score": score
    }
    db.collection("results").add(result_data)

    messagebox.showinfo("Результат", f"Тест завершен! Ваш результат: {score} из {len(correct_answers)}.")

# Главное окно входа
login_window = ctk.CTk()
login_window.title("Тестирующая система")
login_window.geometry("400x500")

ctk.CTkLabel(login_window, text="Вход", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

ctk.CTkLabel(login_window, text="Имя пользователя", font=ctk.CTkFont(size=14)).pack(pady=10)
login_username_entry = ctk.CTkEntry(login_window, width=300, height=40, font=ctk.CTkFont(size=14))
login_username_entry.pack(pady=10)

ctk.CTkLabel(login_window, text="Пароль", font=ctk.CTkFont(size=14)).pack(pady=10)
login_password_entry = ctk.CTkEntry(login_window, show="*", width=300, height=40, font=ctk.CTkFont(size=14))
login_password_entry.pack(pady=10)

ctk.CTkButton(login_window, text="Войти", command=login_user, width=250, height=50, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=20)
ctk.CTkButton(login_window, text="Регистрация", command=open_register_window, width=250, height=50, font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

login_window.mainloop()