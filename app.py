import os  
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from settings import LABELS

# 1. Supabaseの接続設定
@st.cache_resource
def init_connection():
    # 💡 RenderやRailwayなどの有料サーバーの環境変数から直接読み込む
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    # もし有料サーバー上で空っぽだった場合、ローカルPC（secrets.toml）から読み込む
    if not url or not key:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]

    return create_client(url, key)

supabase = init_connection()

# ページ幅をさらに広げるカスタムCSS
st.markdown(
    """
    <style>
        .main .block-container {
            max-width: 1600px !important;
            width: 100% !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# UI 表示文字列は `setting.py` の `LABELS` から読み込んでいます。

# タブごとの表示許可ロールをカンマ区切り文字列で設定できます。
# 例: "1,3,4" や "2" など。空文字は未許可（表示なし）。
TAB_ROLE_CONFIG = {
    "tab1": "1,2,3,4",
    "tab2": "2,3,4",
    "tab3": "3,4",
    "tab4": "4"
}


def _parse_role_list(s: str):
    if not s:
        return []
    parts = [p.strip() for p in s.split(",")]
    out = []
    for p in parts:
        if p == "":
            continue
        try:
            out.append(int(p))
        except Exception:
            # 無効な値は無視
            continue
    return out

# 内部で整数リストへ変換して利用する
TAB_ACCESS = {k: _parse_role_list(v) for k, v in TAB_ROLE_CONFIG.items()}


# 2. セッション状態（ログイン状態）の初期化
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "user_name" not in st.session_state:
    st.session_state["user_name"] = None
if "role_id" not in st.session_state:
    st.session_state["role_id"] = None
if "group_id" not in st.session_state:
    st.session_state["group_id"] = None

# ==========================================
# 🔐 画面制御1: ログイン画面（マスタ参照版）
# ==========================================
if not st.session_state["logged_in"]:
    #st.title("🔐 採点者ログイン画面")
    st.markdown(LABELS["login_title"])
    with st.form("login_form"):
        input_id = st.text_input("採点者ID", placeholder=LABELS["input_id_placeholder"])
        input_pass = st.text_input("パスワード", type="password", placeholder=LABELS["input_pass_placeholder"])
        submit_button = st.form_submit_button(LABELS["login_button"])
        
        if submit_button:
            if not input_id or not input_pass:
                st.error("採点者IDとパスワードの両方を入力してください。")
            else:
                try:
                    # 【重要】解答テーブルではなく、採点者マスタ(graders)からアカウントを検索
                    response = supabase.table("graders") \
                        .select("grader_id, grader_name, role_id, group_id") \
                        .eq("grader_id", input_id) \
                        .eq("password", input_pass) \
                        .limit(1) \
                        .execute()
                    
                    if response.data:
                        # 認証成功
                        st.session_state["logged_in"] = True
                        st.session_state["user_id"] = input_id
                        st.session_state["user_name"] = response.data[0].get("grader_name", response.data[0].get("name", "未設定"))
                        st.session_state["group_id"] = response.data[0].get("group_id", None)
                        # role_id を安全に整数へ変換（DB側が文字列になっている可能性に対応）
                        raw_role = response.data[0].get("role_id", None)
                        parsed_role = None
                        if raw_role is not None:
                            try:
                                parsed_role = int(raw_role)
                            except Exception:
                                try:
                                    parsed_role = int(str(raw_role).strip())
                                except Exception:
                                    parsed_role = None
                        st.session_state["role_id"] = parsed_role
                        st.success("ログインに成功しました！")
                        st.rerun()
                    else:
                        st.error("採点者IDまたはパスワードが正しくありません。")
                except Exception as e:
                    st.error(f"認証エラーが発生しました: {e}")

# ==========================================
# 📊 画面制御2: ログイン後のメイン画面
# ==========================================
else:
    current_user_id = st.session_state["user_id"]
    current_user_name = st.session_state["user_name"]
    current_role_id = st.session_state.get("role_id", None)

    # 画面を横に2分割（左側を4倍広くする）
    col_title, col_logout = st.columns([4, 1])
    with col_title:
        st.markdown("## 📊 試験データ管理システム")
        st.caption(f"ログイン中: {current_user_name} (採点者ID: {current_user_id}) / Role: {current_role_id}")
    with col_logout:
        st.write("") 
        if st.button("ログアウト", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["user_id"] = None
            st.session_state["user_name"] = None
            st.session_state["role_id"] = None
            st.session_state["group_id"] = None
            st.rerun()

    # ------------------------------------------
    # タブ表示条件を role_id の一覧で管理
    # (TAB_ACCESS を編集して許可ロールを指定してください)
    # ------------------------------------------
    def role_allowed(tab_key, role):
        if role is None:
            return False
        allowed = TAB_ACCESS.get(tab_key, [])
        return role in allowed

    show_tab1 = role_allowed("tab1", current_role_id)
    show_tab2 = role_allowed("tab2", current_role_id)
    show_tab3 = role_allowed("tab3", current_role_id)
    show_tab4 = role_allowed("tab4", current_role_id)

    visible_tab_labels = []
    visible_tab_keys = []
    if show_tab1:
        visible_tab_labels.append(LABELS["tab1_label"])
        visible_tab_keys.append("tab1")
    if show_tab2:
        visible_tab_labels.append(LABELS["tab2_group_label"])
        visible_tab_keys.append("tab2")
    if show_tab3:
        visible_tab_labels.append(LABELS["tab3_label"])
        visible_tab_keys.append("tab3")
    if show_tab4:
        visible_tab_labels.append(LABELS["tab4_label"])
        visible_tab_keys.append("tab4")

    if visible_tab_labels:
        tab_objs = st.tabs(visible_tab_labels)
        tab_map = dict(zip(visible_tab_keys, tab_objs))
    else:
        st.warning(f"表示対象のタブがありません。管理者にお問い合わせください。(role_id: {current_role_id})")
        tab_map = {}

    # ------------------------------------------
    # タブ1: レスポンス識別子別集計(採点者画面)
    # -------------------------------------------
    if show_tab1 and "tab1" in tab_map:
        with tab_map["tab1"]:
            st.header(LABELS["tab1_header"])
            if st.button(LABELS["refresh_button"], key="refresh_btn"):
                st.rerun()

            try:
                with st.spinner("データを受信中..."):
                    response = supabase.table("exam_responses_main") \
                        .select("grader_id, response_id, final_result") \
                        .eq("grader_id", current_user_id) \
                        .execute()
                
                if response.data:
                    df_data = pd.DataFrame(response.data)
                    df_data["final_result_filled"] = df_data["final_result"].apply(
                        lambda x: pd.notna(x) and str(x).strip() != ""
                    )
                    
                    df_summary = (
                        df_data
                        .groupby(["grader_id", "response_id"], dropna=False)
                        .agg(
                            採点数=("response_id", "size"),
                            未採点問題数=("final_result_filled", lambda x: (~x).sum()),
                            採点済問題数=("final_result_filled", "sum"),
                        )
                        .reset_index()
                    )
                    df_summary.columns = ['採点者ID', '問題ID', '採点数', '未採点問題数', '採点済問題数']
                    df_summary = df_summary.sort_values(by=['採点数'], ascending=False)

                    st.metric("あなたの担当総集計パターン数", len(df_summary))
                    
                    h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns(6)
                    h_col1.markdown(f"**{LABELS['col_grader']}**")
                    h_col2.markdown(f"**{LABELS['col_response']}**")
                    h_col3.markdown(f"**{LABELS['col_count']}**")
                    h_col4.markdown(f"**{LABELS['col_ungraded']}**")
                    h_col5.markdown(f"**{LABELS['col_graded']}**")
                    h_col6.markdown(f"**{LABELS['col_action']}**")
                    st.divider()

                    for index, row in df_summary.iterrows():
                        col1, col2, col3, col4, col5, col6 = st.columns(6)
                        col1.write(f"{row['採点者ID']}")
                        col2.write(f"{row['問題ID']}")
                        col3.write(f"{row['採点数']}")
                        col4.write(f"{row['未採点問題数']}")
                        col5.write(f"{row['採点済問題数']}")
                        
                        if col6.button(LABELS['col_action'], key=f"start_btn_{index}", use_container_width=True):
                            st.success(LABELS['start_success'].format(resp=row['問題ID']))
                            st.session_state["selected_grader"] = row['採点者ID']
                            st.session_state["selected_response"] = row['問題ID']
                        
                        st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
                else:
                    st.info("あなたが担当するデータはまだ登録されていません。")

            except Exception as e:
                st.error(f"データ取得エラー: {e}")


    # ------------------------------------------
    # タブ2: 採点管理（グループリーダー用）
    # ------------------------------------------
    if show_tab2 and "tab2" in tab_map:
        with tab_map["tab2"]:
            st.header(LABELS["tab2_group_header"])
            current_group_id = st.session_state.get("group_id", None)
            if current_group_id is None:
                st.warning("あなたの所属グループ情報がありません。管理者にお問い合わせください。")
            else:
                if st.button(LABELS["refresh_button"], key="refresh_group_btn"):
                    st.rerun()

                try:
                    with st.spinner("データを受信中..."):
                        group_members = supabase.table("graders") \
                            .select("grader_id, grader_name") \
                            .eq("group_id", current_group_id) \
                            .execute()

                        group_member_map = {
                            m["grader_id"]: m.get("grader_name", "")
                            for m in (group_members.data or [])
                            if m.get("grader_id") is not None
                        }
                        member_ids = list(group_member_map.keys())

                        if not member_ids:
                            st.info("所属グループの採点者が見つかりません。")
                        else:
                            response = supabase.table("exam_responses_main") \
                                .select("grader_id, response_id, final_result") \
                                .in_("grader_id", member_ids) \
                                .execute()

                            if response.data:
                                df_data = pd.DataFrame(response.data)
                                df_data["final_result_filled"] = df_data["final_result"].apply(
                                    lambda x: pd.notna(x) and str(x).strip() != ""
                                )

                                df_summary = (
                                    df_data
                                    .groupby(["grader_id", "response_id"], dropna=False)
                                    .agg(
                                        採点数=("response_id", "size"),
                                        未採点問題数=("final_result_filled", lambda x: (~x).sum()),
                                        採点済問題数=("final_result_filled", "sum"),
                                    )
                                    .reset_index()
                                )
                                df_summary.columns = ['採点者ID', '問題ID', '採点数', '未採点問題数', '採点済問題数']
                                df_summary = df_summary.sort_values(by=['採点者ID', '問題ID'], ascending=[True, True])

                                st.metric("グループ内の担当総集計パターン数", len(df_summary))

                                grader_name_label = LABELS.get('col_grader_name', '採点者名')
                                h_col1, h_col2, h_col3, h_col4, h_col5, h_col6 = st.columns(6)
                                h_col1.markdown(f"**{LABELS['col_grader']}**")
                                h_col2.markdown(f"**{LABELS['col_response']}**")
                                h_col3.markdown(f"**{LABELS['col_count']}**")
                                h_col4.markdown(f"**{LABELS['col_ungraded']}**")
                                h_col5.markdown(f"**{LABELS['col_graded']}**")
                                h_col6.markdown(f"**{grader_name_label}**")
                                st.divider()

                                for index, row in df_summary.iterrows():
                                    col1, col2, col3, col4, col5, col6 = st.columns(6)
                                    col1.write(f"{row['採点者ID']}")
                                    col2.write(f"{row['問題ID']}")
                                    col3.write(f"{row['採点数']}")
                                    col4.write(f"{row['未採点問題数']}")
                                    col5.write(f"{row['採点済問題数']}")
                                    col6.write(group_member_map.get(row['採点者ID'], ""))
                                    st.markdown("<hr style='margin: 0.5em 0; border: 0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)
                            else:
                                st.info("所属グループのデータはまだ登録されていません。")

                except Exception as e:
                    st.error(f"データ取得エラー: {e}")


    # ------------------------------------------
    # タブ3: CSVデータ取り込み
    # ------------------------------------------
    if show_tab3 and "tab3" in tab_map:
        with tab_map["tab3"]:
            st.header(LABELS['tab2_header'])
            uploaded_file = st.file_uploader(LABELS['csv_uploader'], type=["csv"])

            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file, dtype={
                        'コンテンツID': str,
                        '受検者ID': str,
                        'レスポンス識別子': str,
                        '解答内容': str,
                        '解答内容（文字数）': 'Int32',
                        '採点リーダー：ID': str,
                        '採点者ID': str
                    })
                    
                    df['採点依頼日'] = pd.to_datetime(df['採点依頼日']).dt.strftime('%Y-%m-%d')
                    df['採点完了日'] = pd.to_datetime(df['採点完了日']).dt.strftime('%Y-%m-%d')

                    # 【修正ポイント】ログインIDでの絞り込みを無くし、CSVのデータをすべて対象にする
                    st.write(LABELS['csv_preview'].format(n=len(df)))
                    st.dataframe(df.head())

                    if df.empty:
                        st.warning("アップロードされたCSVにデータが含まれていません。")
                    else:
                        if st.button(LABELS['db_insert_btn']):
                            rename_dict = {
                                'コンテンツID': 'content_id',
                                '受検者ID': 'candidate_id',
                                'レスポンス識別子': 'response_id',
                                '解答内容': 'answer_text',
                                '解答内容（文字数）': 'answer_length',
                                '採点リーダー：ID': 'leader_id',
                                '採点者ID': 'grader_id',
                                '採点依頼日': 'request_date',
                                '採点完了日': 'completion_date'
                            }
                            # CSV全体のデータをマッピング
                            df_db = df.rename(columns=rename_dict)
                            
                            records = df_db.where(pd.notnull(df_db), None).to_dict(orient="records")

                            with st.spinner("データを登録中..."):
                                chunk_size = 1000
                                for i in range(0, len(records), chunk_size):
                                    chunk = records[i:i + chunk_size]
                                    supabase.table("exam_responses_main").insert(chunk).execute()
                            
                            st.success(LABELS['db_success'].format(n=len(records)))
                            st.rerun()

                except Exception as e:
                    st.error(f"エラーが発生しました: {e}")

    # ------------------------------------------
    # タブ4: ファイルDL＆UP
    # ------------------------------------------
    if show_tab4 and "tab4" in tab_map:
        with tab_map["tab4"]:
            st.title(LABELS['tab3_title'])

            # 1. ファイルのアップロード機能
            st.markdown(LABELS['tab3_upload_section'])
            uploaded_file = st.file_uploader(LABELS['file_uploader'], type=["csv", "txt", "xlsx"])

            if uploaded_file is not None:
                # アップロードされたファイルの情報を表示
                st.success(f"アップロード完了: {uploaded_file.name}")
                
                # ファイルの中身を読み込む場合（例: テキストファイルの場合）
                bytes_data = uploaded_file.getvalue()
                st.write("ファイルサイズ:", len(bytes_data), "bytes")

            # 2. ファイルのダウンロード機能
            st.header(LABELS['download_header'])

            # ダウンロードさせるサンプルデータを用意
            sample_text = "これはダウンロード用のサンプルテキストデータです。"

            st.download_button(
                label=LABELS['download_btn'],
                data=sample_text,
                file_name="sample_output.txt",
                mime="text/plain"
            )
        
