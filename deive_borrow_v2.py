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

#建議設備 = {
#    "一般用途": "NB04、NB07、NB10、NB11 等皆可用",
#    "院內網路連線": "建議使用 NB04、NB07、NB11",
#    "影像剪輯或照片編輯": "建議使用 NB10（已安裝影像處理軟體）",
#    "OBS直播": "限用 NB12（OBS 專用設備）",
#}



建議設備 = {
    "筆電":{"一般用途": "NB04、NB07、NB10、NB11 等皆可用",
    "院內網路連線": "建議使用 NB04、NB07、NB11",
    "影像剪輯或照片編輯": "建議使用 NB10（已安裝影像處理軟體）",
    "OBS直播": "限用 NB12（OBS 專用設備）",
    },
    "iPAD": {
        "會議用(含視訊會議)": "會議文件無紙化或視訊會議與會",
        "評鑑用": "請確認可連院內wifi:WPA2",
        "其他": "請於下方說明欄輸入具體用途"
    },
    "其他": {
        "其他": "請於下方說明欄輸入具體用途"
    }
}
# 分頁設計
tabs = st.tabs(["設備借用", "設備歸還", "查詢借用狀態","狀態檢測"])

# 設備借用

# 從網址讀取 device_types 參數
device_types_list = ["筆電", "iPAD", "視訊會議喇叭", "網美燈", "相機", "攝影機", "單槍投影機", "視訊鏡頭", "耳麥"]
if "device_type" not in st.session_state:
    query_type = st.query_params.get("device_types", None)
    if query_type in device_types_list:
        st.session_state.device_type = query_type
    else:
        st.session_state.device_type = "筆電"
with tabs[0]:
    st.subheader("📥 設備借用")

    # 已搬移至上方 device_types_list
    device_type = st.selectbox("設備種類", device_types_list, key="device_type")

    說明 = 建議用途說明.get(device_type, {}).get(user_purpose, "")
    if 說明:
        st.caption(f"💡 {user_purpose}：{說明}")

    
    #if device_type == "筆電":
    #    purposes = list(建議設備.keys())
    #elif device_type == "iPAD":
    #    purposes = ["會議用(含視訊會議)", "評鑑用","其他(請於備註說明)"]
    #else:
    #    purposes = ["一般用途", "持續教育用", "其他(請於備註說明)"]

    
    expected_duration = st.selectbox("預計借用時間", ["3天內", "3-7天", "7天以上"], key="borrow_duration")
    name = st.text_input("借用人姓名", key="borrow_name")
    user_purpose = st.selectbox("選擇用途", purposes, key="borrow_purpose")
    說明 = 建議設備.get(user_purpose, "") if device_type == "筆電" else ""
    if 說明:
        st.caption(f"💡 {user_purpose}：{說明}")
    device_id = st.text_input("請輸入設備編號", key="borrow_device")
    note = st.text_input("備註 (選填)", key="borrow_note")
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
                    sheet.append_row([now, name, device_type, user_purpose if user_purpose != "其他" else other_explanation, device_key, "借出", expected_duration, note])
                    st.success("✅ 借用成功並寫入 Google Sheets")
                except Exception as e:
                    st.error(f"❌ 借用紀錄寫入失敗：{e}")

# 設備歸還
with tabs[1]:
    st.subheader("📤 設備歸還")
    return_device_id = st.text_input("請輸入設備編號", key="return_device")

    if st.button("歸還", key="return_button") and sheet_ready:
        if not return_device_id:
            st.error("⚠️ 請輸入設備編號")
        else:
            try:
                records = sheet.get_all_values()
                found = False
                for i in range(len(records) - 1, 0, -1):
                    row = records[i]
                    if row[3].upper() == return_device_id.upper() and row[4] == "借出":
                        sheet.update_cell(i+1, 5, "已歸還")
                        sheet.update_cell(i+1, 6, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        sheet.update_cell(i+1, 7, "")  # 備註欄清空
                        st.success(f"✅ {return_device_id} 已成功歸還")
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
            categories = {}
            for row in all_records[1:]:
                if row[5] == "借出":
                    record = {
                    "借用人": row[1],
                    "用途": row[3],
                    "設備": row[4],
                    "借出時間": row[0],
                    "預計時長": row[6] if len(row) > 6 else "未填寫",
                    "備註": row[7] if len(row) > 7 else ""
                }
                # 逾期判定
                try:
                    借出時間 = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                    預計 = row[6] if len(row) > 6 else ""
                    if 預計 == "3天內":
                        到期日 = 借出時間 + timedelta(days=3)
                    elif 預計 == "3-7天":
                        到期日 = 借出時間 + timedelta(days=7)
                    elif 預計 == "7天以上":
                        到期日 = 借出時間 + timedelta(days=14)
                    else:
                        到期日 = 借出時間 + timedelta(days=7)
                    record["逾期"] = "⚠️ 已逾期" if datetime.now() > 到期日 else ""
                except:
                    record["逾期"] = ""
                    kind = row[2]
                    if kind not in categories:
                        categories[kind] = []
                    categories[kind].append(record)

            if categories:
                st.success("✅ 查詢成功")
                for kind, items in categories.items():
                    st.markdown(f"### 📂 {kind}")
                    st.table(items)
            else:
                st.info("📭 目前無設備借出中")
        except Exception as e:
            st.error(f"❌ 查詢錯誤：{e}")
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
