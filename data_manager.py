import os
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    
    if google_creds_json:
        creds_dict = json.loads(google_creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    return gspread.authorize(creds)

def clean_numeric(val):
    if pd.isna(val) or val == '' or val is None:
        return 0.0
    val_str = str(val).replace(',', '').replace(' ', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def get_user_profile_by_phone(phone_input: str):
    try:
        client = get_gsheet_client()
        login_spreadsheet = client.open("Login AIMKTReg03")
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
        print(f"⚠️ User Auth Error: {e}")

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
        
        # เปิดไฟล์ข้อมูล
        data_spreadsheet = client.open("รายได้ลูกค้าองค์กร/หน่วยงานราชการ/ห้างร้านต่างๆ ปข.3")
        
        # 1. ดึง Master List
        try:
            df_master = pd.DataFrame(data_spreadsheet.worksheet("รายชื่อ").get_all_records())
        except Exception as e:
            print(f"⚠️ Master List Read Error: {e}")
            df_master = pd.DataFrame()

        # 2. อ่านข้อมูลรายปี
        ws = data_spreadsheet.worksheet(str(year))
        raw_values = ws.get_all_values()
        
        if len(raw_values) > 8:
            # ข้ามหัวตาราง 8 บรรทัดแรก ดึงเฉพาะข้อมูลแถวที่ 9 เป็นต้นไป
            data_rows = raw_values[8:]
            df_sales = pd.DataFrame(data_rows)
            
            # ตัดแถว 'รวมทั้งสิ้น' ด้านล่างออก เพื่อป้องกันคำนวณซ้ำ
            df_sales = df_sales[~df_sales[1].astype(str).str.contains("รวม", na=False)]
            df_sales = df_sales[~df_sales[0].astype(str).str.contains("รวม", na=False)]

            # ตั้งชื่อคอลัมน์พื้นฐาน
            df_sales.rename(columns={
                1: 'รายชื่อลูกค้า',
                2: 'กลุ่ม',
                3: 'หมวดธุรกิจ',
                4: 'ประเภทธุรกิจ'
            }, inplace=True)
            
            # ดึงคอลัมน์รวมยอดเงินทั้งหมด (คอลัมน์สุดท้าย)
            last_col_idx = df_sales.columns[-1]
            df_sales['ยอดเงินรวม'] = df_sales[last_col_idx].apply(clean_numeric)

            # คอลัมน์ 5 = ชิ้น, 6 = บาท (ไปรษณียภัณฑ์)
            if 5 in df_sales.columns:
                df_sales['ไปรษณียภัณฑ์_ชิ้น'] = df_sales[5].apply(clean_numeric)

        else:
            df_sales = pd.DataFrame(raw_values)

        if df_sales.empty:
            return pd.DataFrame()

        # 3. Merge ข้อมูลกับ Master List
        if not df_master.empty and 'รายชื่อลูกค้า' in df_sales.columns and 'รายชื่อลูกค้า' in df_master.columns:
            df_merged = pd.merge(
                df_sales, 
                df_master[['รายชื่อลูกค้า', 'กลุ่ม ปจ.', 'สังกัด ปณ.']], 
                on='รายชื่อลูกค้า', 
                how='left'
            )
        else:
            df_merged = df_sales

        # 4. กรองสิทธิ์ตาม Role
        role = user_info['role'].upper()
        dept = user_info['department'].replace("ปจ.", "").replace("ปณ.", "").strip()
        zipcode = user_info['zipcode']

        if role in ["ADMIN", "REG03"]:
            return df_merged
        else:
            if 'สังกัด ปณ.' in df_merged.columns:
                filtered_df = df_merged[
                    (df_merged['สังกัด ปณ.'].astype(str).str.contains(dept, na=False)) |
                    (df_merged['กลุ่ม ปจ.'].astype(str).str.contains(dept, na=False)) |
                    (df_merged['สังกัด ปณ.'].astype(str).str.contains(zipcode, na=False))
                ]
                return filtered_df
            return df_merged

    except Exception as e:
        print(f"❌ Fetch Data Critical Error: {e}")
        return pd.DataFrame()
