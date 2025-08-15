import time
import json
import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.edge.options import Options # FOR EDGE
# from selenium.webdriver.chrome.options import Options  # FOR CHROME
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# === USER SETTINGS ===
QUIZ_SELECTION = [5, 8]    # "all" or [2, 5, 8], 1-based quiz numbers
REPEAT_COUNT = 2           # How many times each quiz should be solved

# ENVIRONMENT VARIABLES
load_dotenv()
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
DASHBOARD_URL = os.getenv("DASHBOARD_URL")

with open("CeregoQuizResults.json", "r", encoding="utf-8") as f:
    all_answers = json.load(f)

options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Edge(options=options) # FOR EDGE
# driver = webdriver.Chrome(options=options)  # FOR CHROME
wait = WebDriverWait(driver, 20)

# Login
driver.get(DASHBOARD_URL)
time.sleep(3)
wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/form/div[1]/input"))).send_keys(EMAIL)
driver.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/form/div[2]/input").send_keys(PASSWORD)
driver.find_element(By.XPATH, "/html/body/div/div[2]/div[1]/div[2]/form/button/span").click()
time.sleep(5)

def get_quiz_rows():
    wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody")))
    return driver.find_elements(By.XPATH, "//table/tbody/tr")

def slow_drag_and_drop(driver, source_elem, target_elem):
    actions = ActionChains(driver)
    actions.move_to_element(source_elem)
    actions.click_and_hold(source_elem)
    actions.pause(1.2)
    src_location = source_elem.location_once_scrolled_into_view
    tgt_location = target_elem.location_once_scrolled_into_view
    total_y = tgt_location['y'] - src_location['y']
    steps = int(abs(total_y) / 15) + 1
    sign = 1 if total_y > 0 else -1
    for _ in range(steps):
        actions.move_by_offset(0, sign * 15)
        actions.pause(0.1)
    actions.release()
    actions.perform()
    time.sleep(1.3)

def solve_ordering_question(driver, wait, correct_order):
    def get_blocks():
        wait.until(EC.presence_of_all_elements_located((By.XPATH, "//ul[@data-rbd-droppable-id='main']/div")))
        blocks = []
        divs = driver.find_elements(By.XPATH, "//ul[@data-rbd-droppable-id='main']/div")
        for div in divs:
            li = div.find_element(By.TAG_NAME, "li")
            # Buradaki metin Research & Development gibi label'dır
            label_div = li.find_element(By.XPATH, ".//div[1]/div")
            label = label_div.text.strip()
            blocks.append({'label': label, 'li': li})
        return blocks

    while True:
        blocks = get_blocks()
        labels = [b['label'] for b in blocks]
        changed = False
        for target_idx, target_label in enumerate(correct_order):
            curr_idx = labels.index(target_label)
            if curr_idx > target_idx:
                print(f"[Ordering] Moving '{target_label}' from {curr_idx} → {target_idx} (step by step).")
                source_elem = blocks[curr_idx]['li']
                target_elem = blocks[target_idx]['li']
                slow_drag_and_drop(driver, source_elem, target_elem)
                changed = True
                break  # Only one move per cycle, then re-evaluate
        if not changed:
            break
        time.sleep(0.9)

# --- CALCULATE QUIZ INDICES ---
def get_quiz_indices(selection, total_quizzes):
    if selection == "all":
        return list(range(total_quizzes))
    elif isinstance(selection, list):
        # User numbers are 1-based, Python indices are 0-based
        return [i-1 for i in selection if 1 <= i <= total_quizzes]
    else:
        raise ValueError("QUIZ_SELECTION must be 'all' or a list of integers.")

# --- MAIN EXECUTION ---
rows = get_quiz_rows()
total_quizzes = len(rows)
quiz_indices = get_quiz_indices(QUIZ_SELECTION, total_quizzes)

for repeat in range(REPEAT_COUNT):
    print(f"\n=== Quiz Solve Round {repeat+1} of {REPEAT_COUNT} ===")
    for quiz_idx in quiz_indices:
        rows = get_quiz_rows()  # refresh each round
        if quiz_idx >= len(rows):
            print(f"Quiz index ({quiz_idx}) is out of range, skipping.")
            continue
        row = rows[quiz_idx]
        try:
            button = row.find_element(By.TAG_NAME, "button")
            button_text = button.text.strip()
            print(f"\n▶️ Starting quiz: {button_text} (Quiz {quiz_idx+1}) - Round {repeat+1}")
            driver.execute_script("arguments[0].click();", button)
            time.sleep(2)

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
            quiz_data = next((q for q in all_answers if q['quiz_title'].strip() == quiz_title), None)
            if not quiz_data:
                print(f"❌ Quiz title not found in JSON: {quiz_title}")
                driver.get(DASHBOARD_URL)
                time.sleep(3)
                continue

            solved_questions = set()
            while True:
                try:
                    show_btn = driver.find_element(By.XPATH, "/html/body/div/div[2]/div/div/div[2]/button")
                    if show_btn.is_displayed() and show_btn.is_enabled():
                        driver.execute_script("arguments[0].click();", show_btn)
                        print("Show Question clicked.")
                        time.sleep(1)
                except Exception:
                    pass

                try:
                    on_screen_q = wait.until(EC.presence_of_element_located(
                        (By.XPATH, "/html/body/div[1]/div[2]/div/div/div[1]/div/div/h3"))).text.strip()
                except Exception as e:
                    print("No question found or quiz finished:", e)
                    break

                norm_screen_q = on_screen_q.strip().lower()
                if norm_screen_q in solved_questions:
                    for next_xpath in [
                        "/html/body/div[1]/div[2]/div/div/div[3]/button/span",
                        "/html/body/div[1]/div[2]/div/div/div[4]/button/span"
                    ]:
                        try:
                            next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, next_xpath)))
                            driver.execute_script("arguments[0].click();", next_btn)
                            time.sleep(1.2)
                            break
                        except:
                            continue
                    continue

                match = None
                for q in quiz_data["questions"]:
                    qnorm = q["question"].strip().lower()
                    if qnorm == norm_screen_q:
                        match = q
                        break
                if not match:
                    for next_xpath in [
                        "/html/body/div[1]/div[2]/div/div/div[3]/button/span",
                        "/html/body/div[1]/div[2]/div/div/div[4]/button/span"
                    ]:
                        try:
                            next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, next_xpath)))
                            driver.execute_script("arguments[0].click();", next_btn)
                            time.sleep(1)
                            break
                        except:
                            continue
                    continue

                solved_questions.add(norm_screen_q)
                print(f"\n❓ {on_screen_q}")

                # --- ORDERING QUESTION ---
                if match.get("type") == "ordering":
                    print("Ordering question: Reordering using move_to_element(target).")
                    solve_ordering_question(driver, wait, match["correct_order"])
                    try:
                        submit_btn = driver.find_element(By.XPATH, "//button[span[text()='Submit answer']]")
                        if submit_btn.is_displayed() and submit_btn.is_enabled():
                            driver.execute_script("arguments[0].click();", submit_btn)
                            print("🟢 Submit Answer (Ordering) button clicked.")
                            time.sleep(1.2)
                    except Exception as e:
                        print(f"Ordering Submit Answer button not found: {e}")
                    for next_xpath in [
                        "/html/body/div[1]/div[2]/div/div/div[4]/button/span",
                        "/html/body/div[1]/div[2]/div/div/div[3]/button/span"
                    ]:
                        try:
                            next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, next_xpath)))
                            driver.execute_script("arguments[0].click();", next_btn)
                            time.sleep(1.2)
                            break
                        except:
                            continue
                    continue

                # --- NORMAL QUESTION ---
                correct_answers = [a.strip() for a in match.get("correct_answers", [])]
                found_count = 0
                for btn_idx in range(1, 15):
                    try:
                        btn_xpath = f"/html/body/div[1]/div[2]/div/div/div[2]/button[{btn_idx}]"
                        btn_elem = driver.find_element(By.XPATH, btn_xpath)
                        choice_text_el = btn_elem.find_element(By.XPATH, ".//div/div/div[1]/div/div/div")
                        choice_text = choice_text_el.text.strip()
                        if any(choice_text == ca or choice_text.lower() == ca.lower() for ca in correct_answers):
                            driver.execute_script("arguments[0].click();", btn_elem)
                            found_count += 1
                            print(f"  ✓ Selected: {choice_text}")
                    except Exception as e:
                        break

                if not found_count:
                    print("No correct choice found on screen!")

                try:
                    submit_btn = driver.find_element(By.XPATH, "/html/body/div/div[2]/div/div/span/div/button/span")
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        driver.execute_script("arguments[0].click();", submit_btn)
                        print("🟢 Submit Answer button clicked.")
                        time.sleep(1.2)
                except Exception as e:
                    print(f"Submit button not found: {e}")

                for next_xpath in [
                    "/html/body/div[1]/div[2]/div/div/div[3]/button/span",
                    "/html/body/div[1]/div[2]/div/div/div[4]/button/span"
                ]:
                    try:
                        next_btn = wait.until(EC.element_to_be_clickable((By.XPATH, next_xpath)))
                        driver.execute_script("arguments[0].click();", next_btn)
                        time.sleep(1.2)
                        break
                    except:
                        continue

            driver.get(DASHBOARD_URL)
            time.sleep(3)

        except Exception as e:
            print(f"Error in quiz {quiz_idx+1}: {e}")
            driver.get(DASHBOARD_URL)
            time.sleep(3)

driver.quit()
print("\n✅ All selected quizzes completed successfully!")