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

def get_user_profile_by_phone(phone_input: str):
    """ ค้นหาข้อมูล User จากคอลัมน์ PhoneNumber """
    client = get_gsheet_client()
    login_spreadsheet = client.open("Login AIMKTReg03")
    df_users = pd.DataFrame(login_spreadsheet.worksheet("Users_Auth").get_all_records())
    
    # แปลงเป็น string เพื่อป้องกันปัญหา 0 หายหน้าเบอร์โทรศัพท์
    df_users['PhoneNumber'] = df_users['PhoneNumber'].astype(str).str.strip()
    target_phone = str(phone_input).strip() if phone_input else "admin"
    
    user_match = df_users[df_users['PhoneNumber'] == target_phone]
    
    if user_match.empty:
        # ค่า Default หากไม่พบเบอร์ในระบบ (แสดงผลเป็น Admin)
        return {
            "phone": "admin",
            "department": "ผู้บริหาร ปข.3",
            "role": "Admin",
            "zipcode": "admin"
        }
    
    row = user_match.iloc[0]
    return {
        "phone": str(row['PhoneNumber']),
        "department": str(row['Department']), # แสดงผลฝั่ง UI
        "role": str(row['Role']),              # ใช้คุมสิทธิ์
        "zipcode": str(row['ZIPCODE'])          # ใช้คุมพื้นที่
    }

def fetch_and_process_data(phone_number: str, year: str):
    """ ดึงและกรองข้อมูลตามสิทธิ์ Role และสังกัดที่ผูกกับ PhoneNumber """
    client = get_gsheet_client()
    user_info = get_user_profile_by_phone(phone_number)
    
    data_spreadsheet = client.open("รายได้ลูกค้ารายองค์กร/หน่วยงานราชการ/ห้างร้านต่างๆ ปย.3")
    
    # 1. อ่าน Master List ชีต 'รายชื่อ'
    df_master = pd.DataFrame(data_spreadsheet.worksheet("รายชื่อ").get_all_records())
    
    # 2. อ่านข้อมูลยอดขาย
    if str(year) == "2569":
        monthly_dfs = []
        for m in range(1, 13):
            month_str = f"2569_{m:02d}"
            try:
                ws = data_spreadsheet.worksheet(month_str)
                monthly_dfs.append(pd.DataFrame(ws.get_all_records()))
            except:
                continue
        df_sales = pd.concat(monthly_dfs, ignore_index=True) if monthly_dfs else pd.DataFrame()
    else:
        try:
            df_sales = pd.DataFrame(data_spreadsheet.worksheet(str(year)).get_all_records())
        except:
            df_sales = pd.DataFrame()

    if df_sales.empty:
        return pd.DataFrame()

    # 3. Merge ข้อมูลเพื่อดึงคอลัมน์สังกัด ปณ.
    df_merged = pd.merge(
        df_sales, 
        df_master[['รายชื่อลูกค้า', 'กลุ่ม ปจ.', 'สังกัด ปณ.']], 
        on='รายชื่อลูกค้า', 
        how='left'
    )

    # 4. กรองข้อมูลตามสิทธิ์ Role
    role = user_info['role'].upper()
    dept = user_info['department'].replace("ปจ.", "").replace("ปณ.", "").strip()
    zipcode = user_info['zipcode']

    # ถ้าเป็น Admin หรือ Reg03 ให้เห็นทั้งหมด
    if role in ["ADMIN", "REG03"]:
        return df_merged
    
    # สิทธิ์ MANAGER / OFFICER / CUSTOMER ให้กรองเฉพาะพื้นที่ตนเอง
    else:
        filtered_df = df_merged[
            (df_merged['สังกัด ปณ.'].astype(str).str.contains(dept, na=False)) |
            (df_merged['กลุ่ม ปจ.'].astype(str).str.contains(dept, na=False)) |
            (df_merged['สังกัด ปณ.'].astype(str).str.contains(zipcode, na=False))
        ]
        return filtered_df
