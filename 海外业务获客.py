import streamlit as st
import twitter_scraper
import twitter_intent_analysis
import twitter_message
import pandas as pd
import os

# 初始化会话状态变量
if 'scraped_file' not in st.session_state:
    st.session_state.scraped_file = None
if 'analyzed_file' not in st.session_state:
    st.session_state.analyzed_file = None

def display_csv(file_path, header):
    if os.path.exists(file_path):
        st.header(header)
        df = pd.read_csv(file_path)
        st.dataframe(df)
        st.download_button(
            label="下载CSV文件",
            data=open(file_path, "rb").read(),
            file_name=os.path.basename(file_path),
            mime="text/csv"
        )

    else:
        st.error(f"文件 {file_path} 不存在")

def main():
    st.title("Twitter Scraper 和 意向分析")

    st.header("步骤1: 爬取推文")
    username = st.text_input("Twitter 用户名")
    password = st.text_input("Twitter 密码", type="password")
    query = st.text_input("搜索关键词")
    max_tweets = st.number_input("最大推文数", min_value=1, max_value=100, value=10)

    if st.button("开始爬取"):
        if not username or not password or not query:
            st.error("请填写所有字段")
        else:
            with st.spinner("爬取中..."):
                try:
                    filename = twitter_scraper.main(username, password, query, max_tweets)

                    if filename == "login_required":
                        st.warning("需要手动验证，请先在浏览器中完成验证，然后再重试。")
                    else:
                        st.success(f"爬取完成！文件已保存为 {filename}")
                        st.session_state.scraped_file = filename  # 保存文件名到会话状态

                except Exception as e:
                    st.error(f"发生错误: {e}")

    if st.session_state.scraped_file:
        display_csv(st.session_state.scraped_file, "爬取结果")

        st.header("步骤2: 意向客户分析")
        analyze_rule = st.text_input("分析意向客户规则", value="用户是否愿意付费实习")

        if st.button("开始分析"):
            if not analyze_rule:
                st.error("请填写分析规则")
            else:
                with st.spinner("分析中..."):
                    try:
                        output_csv = twitter_intent_analysis.analyze_comments(st.session_state.scraped_file, analyze_rule)
                        st.success(f"分析完成，结果已保存到 {output_csv}")
                        st.session_state.analyzed_file = output_csv

                    except Exception as e:
                        st.error(f"发生错误: {e}")

    if st.session_state.analyzed_file:
        display_csv(st.session_state.analyzed_file, "分析结果")

        st.header("步骤3: 发送私信")
        message_template = st.text_area("私信模板", "您好，{username}！我们注意到您对我们的内容感兴趣。请联系我们了解更多信息！")

        if st.button("发送私信"):
            if not message_template:
                st.error("请填写私信模板")
            else:
                with st.spinner("发送中..."):
                    try:
                        twitter_message.send_messages_to_intent_users(st.session_state.analyzed_file, message_template, username, password)
                        st.success("私信发送完成！")
                    except Exception as e:
                        st.error(f"发生错误: {e}")

if __name__ == "__main__":
    main()