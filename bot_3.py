import asyncio
import json
import re
import os
import tempfile
import base64
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

TOKEN = "8649506192:AAGj5MqSv0QiEI3O-OZ49fe_NqsWF3wSHok"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ── HTML-шаблон ───────────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <title>{title}</title>
  <style>
    :root {{
      --primary-color: #4285f4;
      --correct-color: #34a853;
      --wrong-color:   #ea4335;
      --text-color:    #202124;
      --bg-color:      #f8f9fa;
      --card-bg:       #ffffff;
    }}
    [data-theme="dark"] {{ --bg-color:#0f1923; --card-bg:#1a2736; --text-color:#e8eaed; }}
    [data-theme="dark"] .nav-btn {{ color:#e8eaed; border-color:#2d3f52; }}
    * {{ box-sizing:border-box; -webkit-tap-highlight-color:transparent; }}
    body {{ font-family:'Roboto',Arial,sans-serif; padding:12px; background:var(--bg-color); color:var(--text-color); line-height:1.5; max-width:100%; overflow-x:hidden; -webkit-text-size-adjust:100%; }}
    .container {{ max-width:600px; margin:0 auto; }}
    .question-counter {{ font-size:14px; color:#5f6368; margin-bottom:16px; font-weight:500; }}
    .question-card {{ background:var(--card-bg); border-radius:12px; padding:20px; margin-bottom:20px; box-shadow:0 1px 2px rgba(0,0,0,.1); animation:fadeIn .25s ease; }}
    .question-text {{ font-size:18px; font-weight:500; margin-bottom:20px; }}
    .question-image {{ width:100%; max-height:300px; object-fit:contain; border-radius:8px; margin-bottom:16px; display:block; }}
    .options-container {{ display:flex; flex-direction:column; gap:12px; }}
    .option-btn {{
      display:block; width:100%; padding:16px 20px;
      background:var(--card-bg); border:1px solid #dadce0; border-radius:8px;
      cursor:pointer; text-align:left; font-size:16px; color:var(--text-color);
      -webkit-appearance:none; appearance:none; position:relative;
      transition:transform .15s ease, box-shadow .15s ease, background-color .2s;
    }}
    .option-btn:hover  {{ background:#f1f3f4; border-color:#bdc1c6; transform:translateY(-2px); box-shadow:0 6px 12px rgba(0,0,0,.12); }}
    .option-btn:active {{ transform:scale(0.97); box-shadow:0 2px 6px rgba(0,0,0,.15) inset; }}
    .option-btn.correct {{ background-color:#e6f4ea; border-color:var(--correct-color); color:var(--correct-color); animation:correctPulse .35s ease; box-shadow:0 0 0 2px rgba(52,168,83,.3); }}
    .option-btn.wrong   {{ background-color:#fce8e6; border-color:var(--wrong-color);   color:var(--wrong-color);   animation:shake .35s; }}
    .navigation-buttons {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:20px; }}
    .nav-btn {{ min-width:42px; padding:10px 0; text-align:center; border-radius:8px; background:var(--card-bg); border:1px solid #dadce0; cursor:pointer; font-size:14px; }}
    .nav-btn.active           {{ background:#e8f0fe; border-color:var(--primary-color); color:var(--primary-color); }}
    .nav-btn.answered-correct {{ background:#e6f4ea; border-color:var(--correct-color); color:var(--correct-color); }}
    .nav-btn.answered-wrong   {{ background:#fce8e6; border-color:var(--wrong-color);   color:var(--wrong-color); }}
    .action-btn {{ display:block; width:100%; padding:16px; background:var(--primary-color); color:white; border:none; border-radius:8px; font-size:16px; font-weight:500; cursor:pointer; margin-top:20px; transition:background .2s; }}
    .action-btn:hover {{ background:#3367d6; }}
    .result-card {{ background:var(--card-bg); border-radius:12px; padding:20px; margin-top:20px; box-shadow:0 1px 2px rgba(0,0,0,.1); }}
    .result-title {{ font-size:20px; font-weight:500; margin-bottom:16px; }}
    .result-item {{ display:flex; align-items:center; margin-bottom:12px; font-size:16px; }}
    .result-icon {{ margin-right:12px; font-size:20px; }}
    @keyframes correctPulse {{ 0%{{transform:scale(1)}} 50%{{transform:scale(1.05)}} 100%{{transform:scale(1)}} }}
    @keyframes shake {{ 0%{{transform:translateX(0)}} 25%{{transform:translateX(-5px)}} 50%{{transform:translateX(5px)}} 75%{{transform:translateX(-5px)}} 100%{{transform:translateX(0)}} }}
    @keyframes fadeIn {{ from{{opacity:0;transform:translateY(6px)}} to{{opacity:1;transform:translateY(0)}} }}
    @media(max-width:480px) {{
      .question-text {{ font-size:17px; }}
      .option-btn {{ padding:14px 18px; font-size:15px; }}
      .nav-btn {{ min-width:36px; padding:8px 0; font-size:13px; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <button onclick="toggleTheme()" id="themeBtn" style="position:fixed;top:12px;right:12px;background:var(--card-bg);border:1px solid #dadce0;border-radius:20px;padding:8px 14px;cursor:pointer;font-size:14px;color:var(--text-color);box-shadow:0 1px 4px rgba(0,0,0,.2);z-index:999;">🌙 Тёмная</button>
    <div class="navigation-buttons" id="navigation"></div>
    <div class="question-counter" id="questionCounter"></div>
    <div class="question-card">
      <div id="questionImageContainer"></div>
      <div class="question-text" id="questionText">Загрузка...</div>
      <div class="options-container" id="answerButtons"></div>
    </div>
    <div id="nextBtnContainer"></div>
    <div class="result-card" id="testResult" style="display:none;"></div>
  </div>
<script>
  const ALL_QUESTIONS = {questions_json};

  let questions = [], currentQuestionIndex = 0, userAnswers = [];

  function toggleTheme() {{
    const isDark = document.documentElement.getAttribute("data-theme") === "dark";
    document.documentElement.setAttribute("data-theme", isDark ? "light" : "dark");
    document.getElementById("themeBtn").textContent = isDark ? "🌙 Тёмная" : "☀️ Светлая";
    localStorage.setItem("theme", isDark ? "light" : "dark");
  }}
  const savedTheme = localStorage.getItem("theme");
  if (savedTheme) {{
    document.documentElement.setAttribute("data-theme", savedTheme);
    if (savedTheme === "dark") document.getElementById("themeBtn").textContent = "☀️ Светлая";
  }}

  function shuffleArray(a) {{ return a.sort(() => Math.random() - 0.5); }}
  function shuffleAnswers(q) {{
    const correct = q.options[q.correctIndex];
    shuffleArray(q.options);
    q.correctIndex = q.options.indexOf(correct);
  }}

  function init() {{
    questions = shuffleArray(JSON.parse(JSON.stringify(ALL_QUESTIONS)));
    questions.forEach(q => shuffleAnswers(q));
    userAnswers = new Array(questions.length).fill(null);
    document.getElementById("testResult").style.display = "none";
    document.getElementById("testResult").innerHTML = "";
    renderNavigation();
    showQuestion();
  }}

  function renderNavigation() {{
    const nav = document.getElementById("navigation");
    nav.innerHTML = "";
    questions.forEach((_, i) => {{
      const btn = document.createElement("button");
      btn.textContent = i + 1;
      btn.className = "nav-btn";
      btn.onclick = () => {{ currentQuestionIndex = i; showQuestion(); }};
      nav.appendChild(btn);
    }});
    highlightActiveNavigation();
  }}

  function showQuestion() {{
    const q = questions[currentQuestionIndex];
    document.getElementById("questionCounter").textContent = `Вопрос ${{currentQuestionIndex + 1}} из ${{questions.length}}`;
    document.getElementById("questionText").textContent = q.text;

    // Фото вопроса
    const imgContainer = document.getElementById("questionImageContainer");
    imgContainer.innerHTML = "";
    if (q.image) {{
      const img = document.createElement("img");
      img.src = q.image;
      img.className = "question-image";
      img.alt = "Изображение к вопросу";
      imgContainer.appendChild(img);
    }}

    const ac = document.getElementById("answerButtons");
    ac.innerHTML = "";
    q.options.forEach((opt, i) => {{
      const btn = document.createElement("button");
      btn.className = "option-btn";
      btn.textContent = opt;
      btn.onclick = () => checkAnswer(i);
      ac.appendChild(btn);
    }});
    document.getElementById("nextBtnContainer").innerHTML = "";
    highlightActiveNavigation();
  }}

  function checkAnswer(selectedIndex) {{
    const correct = questions[currentQuestionIndex].correctIndex;
    const allButtons = document.querySelectorAll(".option-btn");
    userAnswers[currentQuestionIndex] = selectedIndex === correct;
    allButtons.forEach((b, i) => {{
      b.disabled = true;
      if (i === correct) b.classList.add("correct");
      else if (i === selectedIndex) b.classList.add("wrong");
    }});
    const nextBtn = document.createElement("button");
    nextBtn.textContent = "Следующий вопрос";
    nextBtn.className = "action-btn";
    nextBtn.onclick = nextQuestion;
    document.getElementById("nextBtnContainer").appendChild(nextBtn);
    highlightActiveNavigation();
  }}

  function nextQuestion() {{
    currentQuestionIndex++;
    if (currentQuestionIndex < questions.length) showQuestion();
    else showResults();
  }}

  function showResults() {{
    document.getElementById("questionCounter").textContent = "";
    document.getElementById("questionText").textContent = "Тест завершён";
    document.getElementById("answerButtons").innerHTML = "";
    document.getElementById("questionImageContainer").innerHTML = "";
    const total   = questions.length;
    const correct = userAnswers.filter(a => a === true).length;
    const wrong   = userAnswers.filter(a => a === false).length;
    const unanswered = userAnswers.filter(a => a === null).length;
    const pct = Math.round((correct / total) * 100);
    const resultDiv = document.getElementById("testResult");
    resultDiv.innerHTML = `
      <div class="result-title">Результат теста</div>
      <div class="result-item"><span class="result-icon">✅</span><span>Верных ответов: ${{correct}}</span></div>
      <div class="result-item"><span class="result-icon">❌</span><span>Неверных ответов: ${{wrong}}</span></div>
      <div class="result-item"><span class="result-icon">❓</span><span>Пропущенных вопросов: ${{unanswered}}</span></div>
      <div class="result-item" style="margin-top:16px;font-weight:500;"><span>Ваш результат: ${{pct}}%</span></div>`;
    resultDiv.style.display = "block";
    const restartBtn = document.createElement("button");
    restartBtn.textContent = "Пройти тест снова";
    restartBtn.className = "action-btn";
    restartBtn.onclick = init;
    document.getElementById("nextBtnContainer").innerHTML = "";
    document.getElementById("nextBtnContainer").appendChild(restartBtn);
    document.getElementById("navigation").innerHTML = "";
  }}

  function highlightActiveNavigation() {{
    document.querySelectorAll(".nav-btn").forEach((btn, idx) => {{
      btn.classList.remove("active","answered-correct","answered-wrong");
      if (userAnswers[idx] === true)  btn.classList.add("answered-correct");
      if (userAnswers[idx] === false) btn.classList.add("answered-wrong");
      if (idx === currentQuestionIndex) btn.classList.add("active");
    }});
  }}

  init();
</script>
</body>
</html>"""


# ── Парсер текста вопроса ─────────────────────────────────────────────────────
def parse_single_question(text: str):
    """Парсит ОДИН вопрос с ответами из текста."""
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    if not lines:
        return None

    # Убираем номер если есть ("1." или "1)")
    q_text = re.sub(r'^\d+[\.\)]\s*', '', lines[0]).strip()
    if not q_text:
        return None

    options = []
    correct_index = 0

    for line in lines[1:]:
        match = re.match(r'^[а-дa-eАБВГДABCDE]\s*[\)\.\-]\s*', line, re.IGNORECASE)
        if not match:
            continue
        option_text = line[match.end():].strip()
        is_correct = bool(re.search(r'\(правильный ответ\)', option_text, re.IGNORECASE))
        option_text = re.sub(r'\s*\(правильный ответ\)', '', option_text, flags=re.IGNORECASE).strip()
        if is_correct:
            correct_index = len(options)
        options.append(option_text)

    if len(options) >= 2:
        return {"text": q_text, "options": options, "correctIndex": correct_index}
    return None


def parse_questions_text(text: str):
    """Парсит несколько вопросов из одного текстового сообщения."""
    questions = []
    blocks = re.split(r'(?=^\d+[\.\)]\s)', text.strip(), flags=re.MULTILINE)
    blocks = [b.strip() for b in blocks if b.strip()]
    for block in blocks:
        q = parse_single_question(block)
        if q:
            questions.append(q)
    return questions if questions else None


def generate_html(questions: list, title: str) -> str:
    questions_json = json.dumps(questions, ensure_ascii=False, indent=2)
    return HTML_TEMPLATE.format(title=title, questions_json=questions_json)


# ── FSM ───────────────────────────────────────────────────────────────────────
class TestStates(StatesGroup):
    waiting_for_title      = State()
    collecting_questions   = State()   # ждём вопросы (текст или фото+подпись)
    waiting_for_more       = State()   # спрашиваем: ещё вопросы или готово?


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📝 Создать тест")]],
        resize_keyboard=True
    )

def collecting_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Готово — создать тест")],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True
    )


# ── Хэндлеры ──────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! 👋\n\n"
        "Я генерирую HTML-тесты по твоему шаблону.\n"
        "Нажми кнопку ниже, чтобы начать.",
        reply_markup=main_menu()
    )


@dp.message(F.text == "📝 Создать тест")
async def create_test(message: Message, state: FSMContext):
    await state.set_state(TestStates.waiting_for_title)
    await message.answer("Введи название теста\n(например: «Промышленная безопасность»):")


@dp.message(TestStates.waiting_for_title)
async def get_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip(), questions=[])
    await state.set_state(TestStates.collecting_questions)
    await message.answer(
        "Отлично! Теперь отправляй вопросы.\n\n"
        "<b>Вопрос без фото</b> — просто текст:\n"
        "<code>1. Вопрос?\n"
        "а) Правильный ответ (правильный ответ)\n"
        "б) Другой ответ\n"
        "в) Другой ответ\n"
        "г) Другой ответ</code>\n\n"
        "<b>Вопрос с фото</b> — отправь фото, а в подписи напиши вопрос и ответы в том же формате.\n\n"
        "Можно отправить сразу несколько текстовых вопросов одним сообщением.\n"
        "Когда закончишь — нажми <b>✅ Готово</b>.",
        parse_mode="HTML",
        reply_markup=collecting_menu()
    )


@dp.message(TestStates.collecting_questions, F.text == "✅ Готово — создать тест")
async def finish_collecting(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])
    title = data.get("title", "Тест")

    if not questions:
        await message.answer("❌ Ты ещё не добавил ни одного вопроса! Отправь хотя бы один.")
        return

    await build_and_send_html(message, state, questions, title)


@dp.message(TestStates.collecting_questions, F.text == "❌ Отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu())


# Текстовые вопросы (один или несколько)
@dp.message(TestStates.collecting_questions, F.text)
async def handle_text_questions(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("questions", [])

    new_questions = parse_questions_text(message.text)
    if not new_questions:
        await message.answer(
            "❌ Не удалось распознать вопросы. Проверь формат:\n"
            "<code>1. Вопрос?\n"
            "а) Правильный ответ (правильный ответ)\n"
            "б) Другой ответ\n"
            "в) Другой ответ</code>",
            parse_mode="HTML"
        )
        return

    questions.extend(new_questions)
    await state.update_data(questions=questions)
    await message.answer(
        f"✅ Добавлено вопросов: {len(new_questions)}\n"
        f"📊 Всего в тесте: {len(questions)}\n\n"
        "Отправь ещё вопросы или нажми <b>✅ Готово</b>.",
        parse_mode="HTML"
    )


# Вопрос с фото
@dp.message(TestStates.collecting_questions, F.photo)
async def handle_photo_question(message: Message, state: FSMContext):
    caption = message.caption or ""
    if not caption.strip():
        await message.answer(
            "❌ К фото нужно добавить подпись с вопросом и ответами:\n"
            "<code>Текст вопроса?\n"
            "а) Правильный ответ (правильный ответ)\n"
            "б) Другой ответ\n"
            "в) Другой ответ</code>",
            parse_mode="HTML"
        )
        return

    q = parse_single_question(caption)
    if not q:
        await message.answer(
            "❌ Не удалось распознать вопрос из подписи. Проверь формат:\n"
            "<code>Текст вопроса?\n"
            "а) Правильный ответ (правильный ответ)\n"
            "б) Другой ответ\n"
            "в) Другой ответ</code>",
            parse_mode="HTML"
        )
        return

    # Скачиваем фото и конвертируем в base64
    photo = message.photo[-1]  # берём наибольшее разрешение
    file = await bot.get_file(photo.file_id)
    tmp_photo = os.path.join(tempfile.gettempdir(), f"{photo.file_id}.jpg")
    await bot.download_file(file.file_path, tmp_photo)

    with open(tmp_photo, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    os.remove(tmp_photo)

    q["image"] = f"data:image/jpeg;base64,{img_b64}"

    data = await state.get_data()
    questions = data.get("questions", [])
    questions.append(q)
    await state.update_data(questions=questions)

    await message.answer(
        f"✅ Вопрос с фото добавлен!\n"
        f"📊 Всего в тесте: {len(questions)}\n\n"
        "Отправь ещё вопросы или нажми <b>✅ Готово</b>.",
        parse_mode="HTML"
    )


async def build_and_send_html(message: Message, state: FSMContext, questions: list, title: str):
    html_content = generate_html(questions, title)

    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:50]
    filename = f"{safe_title}.html"
    filepath = os.path.join(tempfile.gettempdir(), filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)

    await state.clear()

    file = FSInputFile(filepath, filename=filename)
    await message.answer_document(
        file,
        caption=(
            f"✅ Готово! Тест «{title}»\n"
            f"📊 Вопросов: {len(questions)}\n\n"
            "Залей HTML-файл на GitHub Pages и открывай в браузере 🚀"
        ),
        reply_markup=main_menu()
    )

    os.remove(filepath)


# ── Запуск ────────────────────────────────────────────────────────────────────
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
