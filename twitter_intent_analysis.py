import requests
import json
import pandas as pd

# Dify API配置
api_url = "http://dify.laplacelab.ai/v1/workflows/run"
api_key = "app-Q7VH5d8ze1FveZYO0ypMQt8z"

def analyze_intent(comment, analyze_rule):
    url = "https://dify.laplacelab.ai/v1/workflows/run"
    payload = json.dumps({
        "inputs": {
            "comment": comment,
            "analyze_rule": analyze_rule
        },
        "response_mode": "blocking",
        "user": "测试用户"
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    response = requests.post(url, headers=headers, data=payload)
    try:
        outputs = response.json().get('data', {}).get('outputs', {}).get('output', '{}')
        result = json.loads(outputs)
        print(f"Analyzed intent for comment: {comment[:30]}... -> Result: {result}")
        return result
    except Exception as e:
        print(f"Error analyzing intent for comment: {comment[:30]}... -> {e}")
        return {"分析理由": "", "意向用户": "否"}




import streamlit as st

def analyze_comments(input_csv, analyze_rule):
    df = pd.read_csv(input_csv)

    # 添加新列
    df['分析理由'] = ""
    df['意向用户'] = ""

    total_comments = len(df)
    progress_bar = st.progress(0)

    for index, row in df.iterrows():
        comment = row['tweet_text']
        analysis_result = analyze_intent(comment, analyze_rule)
        df.at[index, '分析理由'] = analysis_result.get('分析理由', '')
        df.at[index, '意向用户'] = analysis_result.get('意向用户', '')

        # 更新进度条
        progress_bar.progress((index + 1) / total_comments)

    output_csv = input_csv.replace('.csv', '-分析.csv')
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    return output_csv


if __name__ == "__main__":
    input_csv = "分析-高达模型-Twitter-20240731174533.csv"  # 示例输入文件
    analyze_rule = "用户是否愿意买高达模型"  # 示例分析规则
    output_csv = analyze_comments(input_csv, analyze_rule)
    print(f"分析完成，结果已保存到 {output_csv}")