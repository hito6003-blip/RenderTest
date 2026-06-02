# settings.py
# UI表示文字列を集中管理する辞書をここに置きます。
# 必要に応じてこのファイルだけ編集すれば表示文言を一括変更できます。

LABELS = {
    # ログイン
    "login_title": "## 🔐 採点者ログイン画面",
    "input_id_placeholder": "採点者IDを入力してください",
    "input_pass_placeholder": "パスワードを入力",
    "login_button": "ログイン",

    # タブラベル
    "tab1_label": "採点画面（採点者）",
    "tab2_group_label": "採点管理（グループリーダー用）",
    "tab3_label": "CSVデータ取り込み",
    "tab4_label": "ファイルのアップロード & ダウンロード",

    # Tab1
    "tab1_header": "1. 採点画面",
    "tab2_group_header": "1. 採点管理（グループリーダー用）",
    "refresh_button": "最新の情報に更新",
    "col_grader": "採点者ID",
    "col_response": "問題ID",
    "col_count": "総採点問題数",
    "col_ungraded": "未採点問題数",
    "col_graded": "採点済問題数",
    "col_action": "採点開始",
    "col_grader_name": "採点担当者",
    "start_success": "🎉 選択されたレスポンス識別子 {resp} の採点を開始します！",

    # Tab2
    "tab2_header": "2. CSVファイルのアップロード",
    "csv_uploader": "CSVファイルを選択してください",
    "csv_preview": "・取り込みデータプレビュー（CSV内の全データ: 計 {n} 件）",
    "db_insert_btn": "DBへ登録を実行",
    "db_success": "正常に {n} 件のデータを登録しました！",

    # Tab3
    "tab3_title": "3:ファイルの UL&DL",
    "tab3_upload_section": "## 1. ファイルのアップロード",
    "file_uploader": "ファイルを選択してください",
    "download_header": "2. ファイルのダウンロード",
    "download_btn": "サンプルテキストをダウンロード",
}
