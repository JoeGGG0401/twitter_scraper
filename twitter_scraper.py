import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from datetime import datetime


# 初始化浏览器
def init_driver(proxy=None):
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # 如果需要无头浏览器模式，请取消注释
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')
    try:
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        print("Initialized Chrome driver")
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
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
        print("Username entered, moving to password step")

        time.sleep(2)  # 等待页面加载

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
        print("Password entered and logged into Twitter")
        time.sleep(5)  # 等待登录完成
    except Exception as e:
        print(f"Error logging into Twitter: {e}")
        return "login_required"


def check_login_status(driver):
    driver.get('https://twitter.com/home')
    time.sleep(5)  # 等待页面加载
    return 'login' not in driver.current_url


def get_tweet_comments(driver):
    comments = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        comment_elements = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        for comment in comment_elements:
            try:
                comment_text = comment.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                comment_user = comment.find_element(By.XPATH, './/div[@dir="ltr"]/span').text
                comment_user_profile = comment.find_element(By.XPATH, './/a[@role="link"]').get_attribute('href')
                comments.append({
                    'comment_user': comment_user,
                    'comment_user_profile': comment_user_profile,
                    'comment_text': comment_text
                })
            except Exception as e:
                print(f"Error retrieving comment: {e}")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return comments


def search_twitter(query, driver, max_tweets):
    print(f"Searching for tweets with query: {query}")
    search_url = f"https://twitter.com/search?q={query}&src=typed_query"
    driver.get(search_url)
    time.sleep(5)  # 等待搜索结果加载

    # 滚动页面以加载更多推文
    tweets_data = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    print(f"Initial page height: {last_height}")
    while len(tweets_data) < max_tweets:
        tweets = driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        print(f"Found {len(tweets)} tweets on the page")

        for tweet in tweets:
            try:
                tweet_text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                username = tweet.find_element(By.XPATH, './/div[@dir="ltr"]/span').text
                user_profile = tweet.find_element(By.XPATH, './/a[@role="link"]').get_attribute('href')
                tweet_link = tweet.find_element(By.XPATH, './/a[@role="link" and @aria-label]').get_attribute('href')

                # 打印推文的 HTML 内容
                print(tweet.get_attribute('outerHTML'))

                # 进入推文详情页面
                original_window = driver.current_window_handle
                driver.execute_script("window.open(arguments[0], '_blank');", tweet_link)
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(3)  # 等待页面加载评论
                comments = get_tweet_comments(driver)
                driver.close()
                driver.switch_to.window(original_window)
                time.sleep(3)  # 确保页面切换回搜索结果页面
                tweets_data.append({
                    'username': username,
                    'user_profile': user_profile,
                    'tweet_text': tweet_text,
                    'tweet_url': tweet_link,
                    'comments': comments
                })
                print(f"Retrieved tweet from {username} with {len(comments)} comments")
                if len(tweets_data) >= max_tweets:
                    break
            except Exception as e:
                print(f"Error retrieving tweet: {e}")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        print(f"New page height: {new_height}")
        if new_height == last_height:
            print("Reached the end of the page")
            break
        last_height = new_height

    print(f"Total tweets retrieved: {len(tweets_data)}")
    return tweets_data


def save_to_csv(data, filename):
    flattened_data = []
    for tweet in data:
        for comment in tweet['comments']:
            flattened_data.append({
                'username': tweet['username'],
                'user_profile': tweet['user_profile'],
                'tweet_text': tweet['tweet_text'],
                'tweet_url': tweet['tweet_url'],
                'comment_user': comment['comment_user'],
                'comment_user_profile': comment['comment_user_profile'],
                'comment_text': comment['comment_text']
            })
    df = pd.DataFrame(flattened_data)
    with open(filename, 'w', encoding='utf-8-sig') as f:
        df.to_csv(f, index=False)
    print(f"Data saved to {filename}")


# 新增的部分

def main(username, password, query, max_tweets):
    driver = init_driver()
    cookies_path = 'twitter_cookies.json'

    # 尝试加载Cookies
    driver.get('https://twitter.com')
    load_cookies(driver, cookies_path)

    # 检查是否已经登录
    if not check_login_status(driver):
        login_result = login_twitter(driver, username, password)
        if login_result == "login_required":
            driver.quit()
            return "login_required"
        save_cookies(driver, cookies_path)
    else:
        print("Already logged in using cookies")

    tweets_data = search_twitter(query, driver, max_tweets)
    driver.quit()

    # 保存到CSV文件
    current_time = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"爬取-{query}-Twitter-{current_time}.csv"
    save_to_csv(tweets_data, filename)
    return filename