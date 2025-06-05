#QuiestionCollector

import time
import json
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Load .env variables
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
dashboard_url = os.getenv("DASHBOARD_URL")

options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Edge(options=options)
wait = WebDriverWait(driver, 20)

results = []

# Login
driver.get(dashboard_url)
wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/form/div[1]/input"))).send_keys(EMAIL)
driver.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/form/div[2]/input").send_keys(PASSWORD)
driver.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/form/button/span").click()
time.sleep(5)

# Quiz list
wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody")))
rows = driver.find_elements(By.XPATH, "//table/tbody/tr")

for i in range(len(rows)):
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody")))
        rows = driver.find_elements(By.XPATH, "//table/tbody/tr")
        row = rows[i]
        button = row.find_element(By.TAG_NAME, "button")
        button_text = button.text.strip()
        print(f"\n▶️ Starting quiz: {button_text}")
        driver.execute_script("arguments[0].click();", button)
        time.sleep(2)

        # Click "Study Anyway" or "Let's do this!" if present
        for study_xpath in [
            "//button[span[text()='Study Anyway']]",
            "//button[span[text()=\"Let's do this!\"]]",
            "//button[span[text()='Review']]"
        ]:
            try:
                btn = driver.find_element(By.XPATH, study_xpath)
                btn.click()
                time.sleep(1)
            except: pass

        quiz_title = wait.until(EC.presence_of_element_located((By.XPATH, "//nav/div[2]/h4"))).text.strip()
        questions = []

        while True:
            # Show question button
            try:
                show_btn = wait.until(
                    EC.presence_of_element_located((By.XPATH, "/html/body/div/div[2]/div/div/div[2]/button"))
                )
                if show_btn.is_displayed() and show_btn.is_enabled():
                    driver.execute_script("arguments[0].click();", show_btn)
                    time.sleep(1)
            except Exception:
                pass

            # Question text
            try:
                question_el = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[1]/div[2]/div/div/div[1]/div/div/h3")))
                question_text = question_el.text.strip()
                if question_text in ["PRACTICE IT", "PRACTICE COMPLETED", "YOU'VE COMPLETED THIS ASSIGNMENT!", "Let's review!"]:
                    print(f"Quiz finished: {question_text}")
                    break
                print(f"\n❓ Question: {question_text}")
            except Exception as e:
                print("No question found or quiz finished:", e)
                break

            # Ordering question check
            is_ordering = False
            try:
                ordering_header = driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/h3")
                if ordering_header.text.strip() == "Move the blocks into the right order":
                    is_ordering = True
            except:
                is_ordering = False

            if is_ordering:
                try:
                    # Click eye icon and correct answer
                    driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/span/div/button/span").click()
                    time.sleep(1)
                    driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[3]/div/div/button[2]").click()
                    time.sleep(1)

                    correct_order = []
                    for k in range(1, 20):
                        try:
                            el = driver.find_element(
                                By.XPATH,
                                f"/html/body/div[1]/div[2]/div/div/div[3]/ul/div[1]/div[{k}]/li/div/div"
                            )
                            t = el.text.strip()
                            if t:
                                correct_order.append(t)
                        except:
                            break
                    print(f"📋 Correct order: {correct_order}")

                    questions.append({
                        "question": question_text,
                        "type": "ordering",
                        "correct_order": correct_order
                    })

                    # Try both next buttons
                    next_clicked = False
                    for next_xpath in [
                        "/html/body/div[1]/div[2]/div/div/div[4]/button/span",
                        "/html/body/div[1]/div[2]/div/div/div[3]/button/span"
                    ]:
                        try:
                            next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, next_xpath)))
                            driver.execute_script("arguments[0].click();", next_btn)
                            next_clicked = True
                            time.sleep(1.5)
                            break
                        except:
                            continue
                    if not next_clicked:
                        print("⚠️ Next button not found, quiz may be over.")
                        break
                    continue

                except Exception as e:
                    print("⚠️ Ordering question could not be processed:", e)
                    break

            # ----- NORMAL QUESTION BLOCK -----
            choices = []
            for j in range(1, 10):
                try:
                    choice = driver.find_element(
                        By.XPATH,
                        f"/html/body/div[1]/div[2]/div/div/div[2]/button[{j}]/div/div/div[1]/div/div/div"
                    ).text.strip()
                    choices.append(choice)
                except:
                    break

            # Randomly select the first choice
            try:
                checkbox = driver.find_element(
                    By.XPATH,
                    "/html/body/div[1]/div[2]/div/div/div[2]/button[1]/div/div/div[1]/div/div/span/span[1]/input"
                )
                driver.execute_script("arguments[0].click();", checkbox)
            except: pass

            # Show answer (eye icon)
            try:
                driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/span/div/button/span").click()
            except: pass

            time.sleep(2)

            # Correct answers
            correct_answers = []
            correct_elements = driver.find_elements(By.XPATH, "//button[contains(@style,'rgb(122, 183, 45)')]")
            for el in correct_elements:
                try:
                    correct_text = el.find_element(By.XPATH, ".//div[@aria-hidden='true' or @data-testid]").text.strip()
                    if correct_text:
                        correct_answers.append(correct_text)
                except: pass

            questions.append({
                "question": question_text,
                "choices": choices,
                "correct_answers": correct_answers
            })

            # Try both next buttons
            next_clicked = False
            for next_xpath in [
                "/html/body/div[1]/div[2]/div/div/div[3]/button/span",
                "/html/body/div[1]/div[2]/div/div/div[4]/button/span"
            ]:
                try:
                    next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, next_xpath)))
                    driver.execute_script("arguments[0].click();", next_btn)
                    next_clicked = True
                    time.sleep(1.5)
                    break
                except:
                    continue
            if not next_clicked:
                print("⚠️ Next button not found, quiz may be over.")
                break

        results.append({
            "quiz_title": quiz_title,
            "questions": questions
        })

        # Exit after quiz if necessary
        try:
            if "REVIEW IT" in driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div/div[1]/div/div[1]/h3").text:
                driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/nav/div[3]/div/button").click()
                time.sleep(1)
                driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div/div[1]/button/span").click()
        except: pass

        driver.get(dashboard_url)
        time.sleep(2)

    except Exception as e:
        print(f"Error in quiz {i+1}: {e}")
        driver.get(dashboard_url)
        time.sleep(2)

# JSON output
with open("CeregoQuizResults.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

driver.quit()
print("\n✅ All quizzes completed successfully. Results: CeregoQuizResults.json")