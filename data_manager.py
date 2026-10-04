import os
import json
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def get_gsheet_client():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    
    if google_creds_json:
        # กรณีรันบน Hugging Face Spaces (อ่านจาก Secret)
        try:
            creds_dict = json.loads(google_creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        except Exception as e:
            # กรณี Secret โดนครอบด้วย String หรือฟอร์แมตหลุด
            print(f"⚠️ JSON Parse Error in GOOGLE_CREDENTIALS: {e}")
            raise e
    else:
        # กรณีรันทดสอบบนเครื่องคอมพิวเตอร์ Local
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        
    return gspread.authorize(creds)

def clean_numeric(val):
    if pd.isna(val) or val == '' or val is None:
        return 0.0
    val_str = str(val).replace(',', '').replace(' ', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

# คัดลอก ID จาก URL ของ Google Sheets มาใส่ที่นี่ (ดูได้จากแถบ Address Bar ของ Browser)
# ตัวอย่าง URL: https://docs.google.com/spreadsheets/d/1y4PnvNiE57rt6MzpmXS1ZKS.../edit
LOGIN_SHEET_ID = "1zzjuRoDoQPrPZqe4AiXi-hDSPt4WcH7SVHaFu1o7wHk"  # ID ของไฟล์ Login AIMKTReg03
DATA_SHEET_ID = "1Y4PnvNiE57rt6MzpmXS1ZKS-oMsGi1iQw6pcfKhFAII"   # ID ของไฟล์ รายได้ลูกค้า ปย.3

def get_user_profile_by_phone(phone_input: str):
    try:
        client = get_gsheet_client()
        # เปิดด้วย ID แทนชื่อไฟล์ (ป้องกันปัญหาชื่อไฟล์ไม่ตรง หรือ SpreadsheetNotFound)
        login_spreadsheet = client.open_by_key(LOGIN_SHEET_ID)
        df_users = pd.DataFrame(login_spreadsheet.worksheet("Users_Auth").get_all_records())
        
        df_users['PhoneNumber'] = df_users['PhoneNumber'].astype(str).str.strip()
        target_phone = str(phone_input).strip() if phone_input else "admin"
        
        user_match = df_users[df_users['PhoneNumber'] == target_phone]
        if not user_match.empty:
            row = user_match.iloc[0]
            return {
                "phone": str(row['PhoneNumber']),
                "department": str(row['Department']),
                "role": str(row['Role']),
                "zipcode": str(row['ZIPCODE'])
            }
    except Exception as e:
        print(f"⚠️ User Auth Exception: {e}")

    return {
        "phone": "admin",
        "department": "ผู้บริหาร ปข.3",
        "role": "Admin",
        "zipcode": "admin"
    }

def fetch_and_process_data(phone_number: str, year: str):
    try:
        client = get_gsheet_client()
        user_info = get_user_profile_by_phone(phone_number)
        
        # เปิดไฟล์ข้อมูลด้วย ID
        data_spreadsheet = client.open_by_key(DATA_SHEET_ID)
        
        # 1. ดึง Master List ชีต 'รายชื่อ'
        try:
            df_master = pd.DataFrame(data_spreadsheet.worksheet("รายชื่อ").get_all_records())
            df_master.columns = [str(c) for c in df_master.columns]
        except Exception as e:
            df_master = pd.DataFrame()

        # 2. อ่านข้อมูลรายปี
        ws = data_spreadsheet.worksheet(str(year))
        raw_values = ws.get_all_values()
        
        if len(raw_values) > 8:
            data_rows = raw_values[8:]
            df_sales = pd.DataFrame(data_rows)
            
            df_sales = df_sales[~df_sales[1].astype(str).str.contains("รวม", na=False)]
            df_sales = df_sales[~df_sales[0].astype(str).str.contains("รวม", na=False)]

            df_sales.rename(columns={
                1: 'รายชื่อลูกค้า',
                2: 'กลุ่ม',
                3: 'หมวดธุรกิจ',
                4: 'ประเภทธุรกิจ'
            }, inplace=True)
            
            last_col_idx = df_sales.columns[-1]
            df_sales['ยอดเงินรวม'] = df_sales[last_col_idx].apply(clean_numeric)

            if 5 in df_sales.columns:
                df_sales['ไปรษณียภัณฑ์_ชิ้น'] = df_sales[5].apply(clean_numeric)

        else:
            df_sales = pd.DataFrame(raw_values)

        if df_sales.empty:
            return pd.DataFrame()

        # 3. Merge ข้อมูล
        if not df_master.empty and 'รายชื่อลูกค้า' in df_sales.columns and 'รายชื่อลูกค้า' in df_master.columns:
            df_merged = pd.merge(
                df_sales, 
                df_master[['รายชื่อลูกค้า', 'กลุ่ม ปจ.', 'สังกัด ปณ.']], 
                on='รายชื่อลูกค้า', 
                how='left'
            )
        else:
            df_merged = df_sales

        # 4. กรองสิทธิ์
        role = user_info['role'].upper()
        dept = user_info['department'].replace("ปจ.", "").replace("ปณ.", "").strip()
        zipcode = user_info['zipcode']

        if role not in ["ADMIN", "REG03"]:
            if 'สังกัด ปณ.' in df_merged.columns:
                df_merged = df_merged[
                    (df_merged['สังกัด ปณ.'].astype(str).str.contains(dept, na=False)) |
                    (df_merged['กลุ่ม ปจ.'].astype(str).str.contains(dept, na=False)) |
                    (df_merged['สังกัด ปณ.'].astype(str).str.contains(zipcode, na=False))
                ]

        df_merged.columns = [str(c) for c in df_merged.columns]
        return df_merged

    except Exception as e:
        print(f"❌ Detailed Fetch Data Error: {type(e).__name__} - {e}")
        return pd.DataFrame()
