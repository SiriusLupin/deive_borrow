import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# ========== 狀態檢測分頁 ==========
with st.sidebar:
    selected_tab = st.radio("\U0001F5FA️ 功能選單", ["狀態檢測", "設備借用", "設備歸還", "查詢借用狀態"], index=1)

st.set_page_config(page_title="設備借用系統", layout="centered")

st.title("\U0001F4E6 設備借用管理系統")

# ========== Google Sheets 初始化 ==========
if selected_tab == "狀態檢測":
    st.subheader("🔑 Secrets 測試")
    if "gcp_service_account" not in st.secrets:
        st.error("❌ st.secrets 中找不到 gcp_service_account")
    else:
        st.success("✅ 成功載入 gcp_service_account")
        st.code(st.secrets["gcp_service_account"].get("client_email", "未找到 Email"))

    st.subheader("🔑 Google Sheets API 初始化")
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        gcp_secrets = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(gcp_secrets, scope)
        client = gspread.authorize(creds)
        sheet = client.open("北榮設備借用紀錄表").sheet1
        st.success("✅ 成功連線 Google Sheets 並取得工作表")
    except Exception as e:
        st.error(f"❌ Google Sheets 初始化失敗：{e}")

# ========== 設備用途設定 ==========
用途對照 = {
    'NB04': '院內網路連線',
    'NB07': '院內網路連線',
    'NB11': '院內網路連線',
    'NB10': '影像剪輯或照片編輯',
    'NB12': 'OBS直播',
}

# ========== 設備借用 ==========
if selected_tab == "設備借用":
    st.subheader("📥 設備借用")
    name = st.text_input("借用人姓名")
    user_purpose = st.selectbox("選擇用途", ["一般用途", "院內網路連線", "影像剪輯或照片編輯", "OBS直播"])
    device_id = st.text_input("請輸入設備編號")

    if st.button("借用"):
        if not name or not device_id:
            st.error("⚠️ 請填寫完整資料")
        else:
            actual_purpose = 用途對照.get(device_id.upper(), "一般用途")
            if actual_purpose != user_purpose and actual_purpose != "一般用途":
                st.warning(f"⚠️ {device_id} 為 {actual_purpose} 專用，不能用於 {user_purpose}")
            else:
                try:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sheet.append_row([now, name, user_purpose, device_id.upper(), "借出", ""])
                    st.success("✅ 借用成功並寫入 Google Sheets")
                except Exception as e:
                    st.error(f"❌ 借用紀錄寫入失敗：{e}")

# ========== 設備歸還 ==========
elif selected_tab == "設備歸還":
    st.subheader("📤 設備歸還")
    device_id = st.text_input("請輸入設備編號")

    if st.button("歸還"):
        if not device_id:
            st.error("⚠️ 請輸入設備編號")
        else:
            try:
                records = sheet.get_all_values()
                found = False
                for i in range(len(records) - 1, 0, -1):
                    row = records[i]
                    if row[3].upper() == device_id.upper() and row[4] == "借出":
                        sheet.update_cell(i+1, 5, "已歸還")
                        sheet.update_cell(i+1, 6, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        st.success(f"✅ {device_id} 已成功歸還")
                        found = True
                        break
                if not found:
                    st.warning("⚠️ 查無此設備的借出紀錄")
            except Exception as e:
                st.error(f"❌ 歸還過程錯誤：{e}")

# ========== 查詢設備狀態 ==========
elif selected_tab == "查詢借用狀態":
    st.subheader("🔍 查詢目前借出狀態")
    try:
        all_records = sheet.get_all_values()
        data = []
        for row in all_records[1:]:
            if row[4] == "借出":
                data.append({
                    "借用人": row[1],
                    "用途": row[2],
                    "設備": row[3],
                    "借出時間": row[0]
                })
        if data:
            st.success("✅ 查詢成功")
            st.write("以下為目前借出中的設備：")
            st.table(data)
        else:
            st.info("📭 目前無設備借出中")
    except Exception as e:
        st.error(f"❌ 查詢錯誤：{e}")
