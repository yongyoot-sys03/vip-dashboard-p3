import os
import json
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 🔑 ตั้งค่า ID ของ Google Sheets (เปิดด้วย ID ชัวร์ 100%)
# ==========================================
LOGIN_SHEET_ID = "1zzjuRoDoQPrPZqe4AiXi-hDSPt4WcH7SVHaFu1o7wHk"
DATA_SHEET_ID = "1Y4PnvNiE57rt6MzpmXS1ZKS-oMsGi1iQw6pcfKhFAII"

def get_gsheet_client():
    """ ฟังก์ชันเชื่อมต่อ Google Sheets API ด้วย Service Account """
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    
    if google_creds_json:
        try:
            creds_dict = json.loads(google_creds_json)
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        except Exception as e:
            print(f"⚠️ JSON Parse Error in GOOGLE_CREDENTIALS: {e}")
            raise e
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        
    return gspread.authorize(creds)

def clean_numeric(val):
    """ ฟังก์ชันทำความสะอาดตัวเลข (ลบลูกน้ำ และแปลงเป็น Float) """
    if pd.isna(val) or val == '' or val is None:
        return 0.0
    val_str = str(val).replace(',', '').replace(' ', '').strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def get_user_profile_by_phone(phone_input: str):
    """ ค้นหาข้อมูลสิทธิ์ผู้ใช้งานจากชีต Login AIMKTReg03 """
    try:
        client = get_gsheet_client()
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

    # Default หากไม่พบข้อมูล
    return {
        "phone": "admin",
        "department": "ผู้บริหาร ปข.3",
        "role": "Admin",
        "zipcode": "admin"
    }

def fetch_and_process_data(phone_number: str, year: str):
    """ ดึงและประมวลผลข้อมูลยอดขาย พร้อมคำนวณ ชิ้น/บาท ของแต่ละบริการ """
    try:
        client = get_gsheet_client()
        user_info = get_user_profile_by_phone(phone_number)
        
        data_spreadsheet = client.open_by_key(DATA_SHEET_ID)
        
        # 1. ดึง Master List ชีต 'รายชื่อ' (ถ้ามี)
        try:
            df_master = pd.DataFrame(data_spreadsheet.worksheet("รายชื่อ").get_all_records())
            df_master.columns = [str(c) for c in df_master.columns]
        except Exception as e:
            df_master = pd.DataFrame()

        # 2. อ่านข้อมูลรายปี
        ws = data_spreadsheet.worksheet(str(year))
        raw_values = ws.get_all_values()
        
        if len(raw_values) > 8:
            # ข้ามหัวตาราง 8 บรรทัดแรก ดึงเฉพาะข้อมูลแถวที่ 9 เป็นต้นไป
            data_rows = raw_values[8:]
            df_sales = pd.DataFrame(data_rows)
            
            # ตัดแถว 'รวม' ด้านล่างสุดออก เพื่อป้องกันการคำนวณเบิ้ล
            df_sales = df_sales[~df_sales[1].astype(str).str.contains("รวม", na=False)]
            df_sales = df_sales[~df_sales[0].astype(str).str.contains("รวม", na=False)]

            # ตั้งชื่อคอลัมน์หลัก 4 คอลัมน์แรกให้สวยงาม
            df_sales.rename(columns={
                1: 'รายชื่อลูกค้า',
                2: 'กลุ่ม',
                3: 'หมวดธุรกิจ',
                4: 'ประเภทธุรกิจ'
            }, inplace=True)
            
            # ==========================================
            # 📊 ส่วนดึงข้อมูลตัวเลขตาม Index (ชิ้น และ บาท)
            # ==========================================
            
            # 1. ยอดเงินรวม (ดึงคอลัมน์สุดท้ายของตารางเสมอ)
            last_col_idx = df_sales.columns[-1]
            df_sales['ยอดเงินรวม'] = df_sales[last_col_idx].apply(clean_numeric)

            # 2. ไปรษณียภัณฑ์ (ชิ้น Index 5 / บาท Index 6)
            if 5 in df_sales.columns: 
                df_sales['ไปรษณียภัณฑ์_ชิ้น'] = df_sales[5].apply(clean_numeric)
            else: 
                df_sales['ไปรษณียภัณฑ์_ชิ้น'] = 0.0
                
            if 6 in df_sales.columns: 
                df_sales['ไปรษณียภัณฑ์_บาท'] = df_sales[6].apply(clean_numeric)
            else: 
                df_sales['ไปรษณียภัณฑ์_บาท'] = 0.0

            # 3. ขนส่งและโลจิสติกส์ (ชิ้น Index 15, 17, 19, 21, 23, 25, 27)
            logis_pcs_idx = [idx for idx in [15, 17, 19, 21, 23, 25, 27] if idx in df_sales.columns]
            logis_baht_idx = [idx + 1 for idx in logis_pcs_idx] # ยอดเงินบาทจะอยู่ถัดจากจำนวนชิ้น 1 ช่องเสมอ
            
            if logis_pcs_idx:
                df_sales['ขนส่งโลจิสติกส์_ชิ้น'] = df_sales[logis_pcs_idx].apply(lambda col: col.map(clean_numeric)).sum(axis=1)
            else:
                df_sales['ขนส่งโลจิสติกส์_ชิ้น'] = 0.0
                
            if logis_baht_idx:
                df_sales['ขนส่งโลจิสติกส์_บาท'] = df_sales[logis_baht_idx].apply(lambda col: col.map(clean_numeric)).sum(axis=1)
            else:
                df_sales['ขนส่งโลจิสติกส์_บาท'] = 0.0

            # 4. ระหว่างประเทศ (ชิ้น Index 31, 33, 35, 37, 39, 41, 43, 45)
            inter_pcs_idx = [idx for idx in [31, 33, 35, 37, 39, 41, 43, 45] if idx in df_sales.columns]
            inter_baht_idx = [idx + 1 for idx in inter_pcs_idx] # ยอดเงินบาทจะอยู่ถัดจากจำนวนชิ้น 1 ช่องเสมอ
            
            if inter_pcs_idx:
                df_sales['ระหว่างประเทศ_ชิ้น'] = df_sales[inter_pcs_idx].apply(lambda col: col.map(clean_numeric)).sum(axis=1)
            else:
                df_sales['ระหว่างประเทศ_ชิ้น'] = 0.0
                
            if inter_baht_idx:
                df_sales['ระหว่างประเทศ_บาท'] = df_sales[inter_baht_idx].apply(lambda col: col.map(clean_numeric)).sum(axis=1)
            else:
                df_sales['ระหว่างประเทศ_บาท'] = 0.0

        else:
            df_sales = pd.DataFrame(raw_values)

        # หากไม่มีข้อมูลเลย
        if df_sales.empty:
            return pd.DataFrame()

        # ==========================================
        # 🔐 ส่วนที่ 3-4: การ Merge สังกัด และกรองสิทธิ์ (RBAC)
        # ==========================================
        if not df_master.empty and 'รายชื่อลูกค้า' in df_sales.columns and 'รายชื่อลูกค้า' in df_master.columns:
            df_merged = pd.merge(
                df_sales, 
                df_master[['รายชื่อลูกค้า', 'กลุ่ม ปจ.', 'สังกัด ปณ.']], 
                on='รายชื่อลูกค้า', 
                how='left'
            )
        else:
            df_merged = df_sales

        role = user_info['role'].upper()
        dept = user_info['department'].replace("ปจ.", "").replace("ปณ.", "").strip()
        zipcode = user_info['zipcode']

        # คัดกรองข้อมูลเฉพาะพื้นที่รับผิดชอบ (ถ้าไม่ใช่ Admin)
        if role not in ["ADMIN", "REG03"]:
            if 'สังกัด ปณ.' in df_merged.columns:
                df_merged = df_merged[
                    (df_merged['สังกัด ปณ.'].astype(str).str.contains(dept, na=False)) |
                    (df_merged['กลุ่ม ปจ.'].astype(str).str.contains(dept, na=False)) |
                    (df_merged['สังกัด ปณ.'].astype(str).str.contains(zipcode, na=False))
                ]

        # 🎯 [สำคัญ] บังคับให้ชื่อ Header ทุกคอลัมน์เป็น String เพื่อป้องกัน Gradio Error
        df_merged.columns = [str(c) for c in df_merged.columns]

        return df_merged

    except Exception as e:
        print(f"❌ Detailed Fetch Data Error: {type(e).__name__} - {e}")
        return pd.DataFrame()
