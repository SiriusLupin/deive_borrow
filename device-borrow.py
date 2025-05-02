import streamlit as st
st.set_page_config(page_title="設備借用系統", layout="centered")

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.title("\U0001F4E6 設備借用管理系統")

# 初始化 Google Sheets
try:
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    gcp_secrets = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(gcp_secrets, scope)
    client = gspread.authorize(creds)
    sheet = client.open("北榮設備借用紀錄表").sheet1
    sheet_ready = True
except Exception as e:
    sheet_ready = False
    sheet_error = str(e)

# 設備用途對照
專用用途對照 = {
    'NB04': '院內網路連線',
    'NB07': '院內網路連線',
    'NB11': '院內網路連線',
    'NB10': '影像剪輯或照片編輯',
    'NB12': 'OBS直播',
}

建議設備 = {
    "一般用途": "NB04、NB07、NB10、NB11 等皆可用",
    "院內網路連線": "建議使用 NB04、NB07、NB11",
    "影像剪輯或照片編輯": "建議使用 NB10（已安裝影像處理軟體）",
    "OBS直播": "限用 NB12（OBS 專用設備）",
}

# 分頁設計
tabs = st.tabs(["設備借用", "設備歸還", "查詢借用狀態", "狀態檢測"])



# 設備借用
with tabs[0]:
    st.subheader("📥 設備借用")
    name = st.text_input("借用人姓名", key="borrow_name")
    user_purpose = st.selectbox("選擇用途", list(建議設備.keys()), key="borrow_purpose")
    st.caption(f"💡 {user_purpose}：{建議設備[user_purpose]}")
    device_id = st.text_input("請輸入設備編號", key="borrow_device")

    if st.button("借用") and sheet_ready:
        if not name or not device_id:
            st.error("⚠️ 請填寫完整資料")
        else:
            device_key = device_id.upper()
            專用用途 = 專用用途對照.get(device_key, None)

            if device_key == 'NB12' and user_purpose != 'OBS直播':
                st.warning(f"⚠️ {device_key} 為 OBS直播 專用，不能用於 {user_purpose}")
            elif user_purpose != "一般用途" and 專用用途 != user_purpose:
                st.warning(f"⚠️ {device_key} 不支援 {user_purpose}，請選擇對應設備")
            else:
                try:
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    sheet.append_row([now, name, user_purpose, device_key, "借出", ""])
                    st.success("✅ 借用成功並寫入 Google Sheets")
                except Exception as e:
                    st.error(f"❌ 借用紀錄寫入失敗：{e}")

# 設備歸還
with tabs[1]:
    st.subheader("📤 設備歸還")
    device_id = st.text_input("請輸入設備編號", key="return_device")

    if st.button("歸還") and sheet_ready:
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

# 查詢借用狀態
with tabs[2]:
    st.subheader("🔍 查詢目前借出狀態")
    if sheet_ready:
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

# 狀態檢測
with tabs[3]:
    st.subheader("🔎 系統狀態檢查")
    if "gcp_service_account" not in st.secrets:
        st.error("❌ st.secrets 中找不到 gcp_service_account")
    else:
        st.success("✅ 成功載入 gcp_service_account")
        st.code(st.secrets["gcp_service_account"].get("client_email", "未找到 Email"))

    st.subheader("🔑 Google Sheets API 初始化")
    if sheet_ready:
        st.success("✅ 成功連線 Google Sheets 並取得工作表")
    else:
        st.error(f"❌ Google Sheets 初始化失敗：{sheet_error}")
