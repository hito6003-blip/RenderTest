import os
import streamlit as st
from supabase import create_client, Client

# Renderに登録した環境変数を安全に読み込む
url: str = os.environ.get("SUPABASE_URL", "")
key: str = os.environ.get("SUPABASE_KEY", "")

st.title("Hello Streamlit & Supabase!")

# 接続テスト
if url and key:
    try:
        supabase: Client = create_client(url, key)
        st.success("Supabaseへの接続設定が完了しました！")
        
        # 例：'profiles'というテーブルからデータを取得してみるテスト
        # response = supabase.table("profiles").select("*").execute()
        # st.write(response.data)
        
    except Exception as e:
        st.error(f"接続エラーが発生しました: {e}")
else:
    st.warning("環境変数が設定されていません。")
