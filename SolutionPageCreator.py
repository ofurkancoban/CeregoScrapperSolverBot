#SolutionPageCreator
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import green, red, black
import textwrap
import os

def wrap_text_lines(text, width=100):
    return textwrap.wrap(text, width=width)

def create_answer_key_pdf(json_path, output_path="quiz_answer_key.pdf"):
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    x = 2 * cm
    y = height - 2 * cm
    line_height = 9

    # Centered Quiz Answer Key title
    c.setFont("Helvetica-Bold", 12)
    title = "Quiz Answer Key"
    title_width = c.stringWidth(title, "Helvetica-Bold", 12)
    c.drawString((width - title_width) / 2, y, title)
    y -= 2 * line_height

    for idx, quiz in enumerate(data):
        quiz_title = quiz.get('quiz_title', 'Quiz')

        # Start a new page for each unit except the first
        if idx > 0:
            c.showPage()
            y = height - 2 * cm

        # Centered and underlined unit title
        c.setFont("Helvetica-Bold", 11)
        quiz_title_width = c.stringWidth(quiz_title, "Helvetica-Bold", 11)
        quiz_title_x = (width - quiz_title_width) / 2
        c.setFillColor(black)
        c.drawString(quiz_title_x, y, quiz_title)
        # Underline
        underline_y = y - 2
        c.setLineWidth(0.7)
        c.line(quiz_title_x, underline_y, quiz_title_x + quiz_title_width, underline_y)
        y -= 1.5 * line_height

        questions = quiz.get('questions', [])
        for i, item in enumerate(questions, 1):
            if y < 5 * cm:
                c.showPage()
                y = height - 2 * cm

            # Bold question text
            c.setFont("Helvetica-Bold", 8)
            question_text = f"{i}. {item.get('question', '')}"
            for line in wrap_text_lines(question_text, 100):
                c.setFillColor(black)
                c.drawString(x, y, line)
                y -= line_height

            # Ordering type support
            if item.get("type", "") == "ordering":
                c.setFont("Helvetica", 7)
                c.setFillColor(green)
                c.drawString(x + 15, y, "Correct Order:")
                y -= line_height
                for order_line in item.get("correct_order", []):
                    for wrapped in wrap_text_lines(order_line, 90):
                        c.drawString(x + 30, y, wrapped)
                        y -= line_height
                y -= line_height
                c.setFillColor(black)
                continue

            # Choices (colored marking)
            for choice in item.get("choices", []):
                is_correct = choice in item.get("correct_answers", [])
                lines = wrap_text_lines(choice, 95)

                if is_correct:
                    c.setFont("Helvetica", 7)
                    c.setFillColor(green)
                    prefix = "✔"
                else:
                    c.setFont("Helvetica", 7)
                    c.setFillColor(red)
                    prefix = "✘"

                for j, line in enumerate(lines):
                    bullet = f"{prefix} " if j == 0 else "   "
                    c.drawString(x + 15, y, bullet + line)
                    y -= line_height

            y -= line_height
            c.setFillColor(black)

        y -= line_height  # Extra space between quizzes

    c.save()
    print(f"✅ PDF saved to: {output_path}")

# Usage
if __name__ == "__main__":
    create_answer_key_pdf("CeregoQuizResults.json", "QuizSolutions.pdf")