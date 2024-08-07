import json
import os
import re
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

def init_driver(proxy=None):
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver

def save_cookies(driver, path):
    with open(path, 'w') as file:
        json.dump(driver.get_cookies(), file)
    print(f"Cookies saved to {path}")

def load_cookies(driver, path):
    if os.path.exists(path):
        with open(path, 'r') as file:
            cookies = json.load(file)
            for cookie in cookies:
                driver.add_cookie(cookie)
        print(f"Cookies loaded from {path}")
    else:
        print(f"No cookies found at {path}")

def login_twitter(driver, username, password):
    driver.get('https://twitter.com/login')
    time.sleep(2)
    try:
        # 输入用户名
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "text"))
        )
        username_field.send_keys(username)
        next_button = driver.find_element(By.XPATH, '//span[text()="Next"]/..')
        next_button.click()
        time.sleep(2)

        # 检查是否需要手动验证
        if "login_verification" in driver.current_url:
            print("Login verification required")
            return "login_required"

        # 输入密码
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        password_field.send_keys(password)
        login_button = driver.find_element(By.XPATH, '//span[text()="Log in"]/..')
        login_button.click()
        time.sleep(5)
    except Exception as e:
        print(f"Error logging into Twitter: {e}")
        return "login_required"

def check_login_status(driver):
    driver.get('https://twitter.com/home')
    time.sleep(5)
    return 'login' not in driver.current_url

def send_message(driver, user_profile_url, message):
    driver.get(user_profile_url)
    wait = WebDriverWait(driver, 20)

    try:
        # 确保用户页面加载完成
        wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='UserProfileHeader_Items']")))
        print(f"Loaded user profile page: {user_profile_url}")

        # 定位并点击消息按钮
        message_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Message' and @data-testid='sendDMFromProfile']")))
        print(f"Found message button: {message_button.get_attribute('outerHTML')}")
        message_button.click()
        print("Message button clicked")

        # 等待消息输入框出现
        message_input = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-testid='dmComposerTextInput']")))
        message_input.send_keys(message)
        message_input.send_keys(Keys.RETURN)
        print(f"Message sent to {user_profile_url}")
    except Exception as e:
        print(f"Failed to send message to {user_profile_url}: {e}")
        try:
            surrounding_html = driver.execute_script("""
                return document.body.innerHTML;
            """)
            print(f"Surrounding HTML: {surrounding_html[:1000]}")  # 只打印前1000个字符
        except Exception as inner_e:
            print(f"Failed to retrieve surrounding HTML: {inner_e}")

def send_messages_to_intent_users(csv_file, message_template, username, password):
    csv_file = "分析-xxx测试.csv"  # 示例输入文件
    df = pd.read_csv(csv_file)
    intent_users = df[df['意向用户'] == '是']

    driver = init_driver()
    cookies_path = 'twitter_cookies.json'

    driver.get('https://twitter.com')
    load_cookies(driver, cookies_path)

    if not check_login_status(driver):
        login_result = login_twitter(driver, username, password)
        if login_result == "login_required":
            driver.quit()
            print("Manual login required")
            return "login_required"
        save_cookies(driver, cookies_path)
    else:
        print("Already logged in using cookies")

    total_users = len(intent_users)
    progress = 0

    for index, row in intent_users.iterrows():
        comment_user_profile = row['comment_user_profile']
        message = message_template.format(username=row['comment_user'])
        send_message(driver, comment_user_profile, message)
        progress = (index + 1) / total_users
    st.progress(progress)

    driver.quit()

if __name__ == "__main__":
    # 示例调用
    csv_file = "分析-xxx测试.csv"  # 示例输入文件
    message_template = "您好，{username}！我们注意到您对我们的内容感兴趣。请联系我们了解更多信息！"
    twitter_username = 'laplacebox1234@163.com'  # 替换为你的 Twitter 用户名
    twitter_password = 'laplace@2024'  # 替换为你的 Twitter 密码

    send_messages_to_intent_users(csv_file, message_template, twitter_username, twitter_password)