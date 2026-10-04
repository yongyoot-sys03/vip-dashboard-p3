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
    """ ฟังก์ชันแปลงข้อความตัวเลขที่มีเครื่องหมาย comma ให้เป็น float """
    if pd.isna(val) or val == '' or val is None:
        return 0.0
    val_str = str(val).replace(',', '').replace(' ', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def get_user_profile_by_phone(phone_input: str):
    """ ดึงข้อมูลสิทธิ์จากชีต Login AIMKTReg03 """
    client = get_gsheet_client()
    try:
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
        pass

    return {
        "phone": "admin",
        "department": "ผู้บริหาร ปข.3",
        "role": "Admin",
        "zipcode": "admin"
    }

def fetch_and_process_data(phone_number: str, year: str):
    client = get_gsheet_client()
    user_info = get_user_profile_by_phone(phone_number)
    
    data_spreadsheet = client.open("รายได้ลูกค้าองค์กร/หน่วยงานราชการ/ห้างร้านต่างๆ ปข.3")
    
    # 1. ดึง Master List ชีต 'รายชื่อ'
    try:
        df_master = pd.DataFrame(data_spreadsheet.worksheet("รายชื่อ").get_all_records())
    except:
        df_master = pd.DataFrame()

    # 2. อ่านข้อมูลรายปี แบบข้ามหัวตารางซับซ้อน (Skip Header 8 แถวแรก)
    try:
        ws = data_spreadsheet.worksheet(str(year))
        raw_values = ws.get_all_values()
        
        # ถ้ารายงานมีหัวตารางซ้อนหลายชั้นแบบในภาพ ให้เริ่มอ่านตั้งแต่แถวที่มีข้อมูลจริง (แถวที่ 9 เป็นต้นไป)
        if len(raw_values) > 8:
            # ใช้แถวข้อมูลจริง
            data_rows = raw_values[8:] 
            
            # สร้าง Dataframe เบื้องต้น
            df_sales = pd.DataFrame(data_rows)
            
            # ลบแถวรวมด้านล่างสุดออก (ถ้ามีคำว่า 'รวม' ในคอลัมน์แรกๆ) เพื่อไม่ให้คำนวณซ้ำ
            df_sales = df_sales[~df_sales[1].astype(str).str.contains("รวม", na=False)]
            df_sales = df_sales[~df_sales[0].astype(str).str.contains("รวม", na=False)]

            # ตั้งชื่อคอลัมน์หลักตามตำแหน่ง Index จริงใน Google Sheet
            # Index 1 = รายชื่อลูกค้า, Index 2 = กลุ่ม, Index 3 = หมวดธุรกิจ, Index 4 = ประเภทธุรกิจ
            df_sales.rename(columns={
                1: 'รายชื่อลูกค้า',
                2: 'กลุ่ม',
                3: 'หมวดธุรกิจ',
                4: 'ประเภทธุรกิจ'
            }, inplace=True)
            
            # ดึงคอลัมน์ยอดเงินรวมทั้งหมด (คอลัมน์สุดท้ายของตาราง)
            last_col_idx = df_sales.columns[-1]
            df_sales['ยอดเงินรวม'] = df_sales[last_col_idx].apply(clean_numeric)

            # แปลงคอลัมน์ตัวเลขสำคัญต่างๆ ให้เป็น Float
            # คอลัมน์ F(5), G(6) = จดหมายในประเทศ ชิ้น, บาท
            if 6 in df_sales.columns:
                df_sales['ไปรษณียภัณฑ์_บาท'] = df_sales[6].apply(clean_numeric)
            if 5 in df_sales.columns:
                df_sales['ไปรษณียภัณฑ์_ชิ้น'] = df_sales[5].apply(clean_numeric)

        else:
            df_sales = pd.DataFrame(raw_values)
            
    except Exception as e:
        df_sales = pd.DataFrame()

    if df_sales.empty:
        return pd.DataFrame()

    # 3. Merge ข้อมูลกับ Master List เพื่อดึงคอลัมน์สังกัด ปณ.
    if not df_master.empty and 'รายชื่อลูกค้า' in df_sales.columns and 'รายชื่อลูกค้า' in df_master.columns:
        df_merged = pd.merge(
            df_sales, 
            df_master[['รายชื่อลูกค้า', 'กลุ่ม ปจ.', 'สังกัด ปณ.']], 
            on='รายชื่อลูกค้า', 
            how='left'
        )
    else:
        df_merged = df_sales

    # 4. กรองข้อมูลตามสิทธิ์ Role
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
