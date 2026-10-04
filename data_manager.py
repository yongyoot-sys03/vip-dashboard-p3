import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # ดึงค่าจาก Secret บน Hugging Face Spaces
    google_creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    
    if google_creds_json:
        # หากอยู่บน HF Spaces ให้โหลดจาก Environment Variable
        creds_dict = json.loads(google_creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # หากรันทดสอบในเครื่องคอมพิวเตอร์ ให้ดึงจากไฟล์Local
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        
    return gspread.authorize(creds)

def fetch_and_process_data(user_id: str, year: str):
    """
    1. อ่านตาราง Users_Auth จากชีต Login
    2. เช็ก Role, ZIPCODE และ Department ของ User ที่เข้าใช้งาน
    3. รวมตารางรายได้ (2566-2569) เข้ากับตาราง 'รายชื่อ' Master List
    4. กรองข้อมูลเฉพาะสังกัดที่ User นั้นมีสิทธิ์มองเห็น
    """
    client = get_gsheet_client()
    
    # -------------------------------------------------------------
    # Step 1: ตรวจสอบสิทธิ์จากชีต Login (Users_Auth)
    # -------------------------------------------------------------
    login_spreadsheet = client.open("Login AIMKTReg03")
    df_users = pd.DataFrame(login_spreadsheet.worksheet("Users_Auth").get_all_records())
    
    # ดึงข้อมูลของ User ที่กำลัง Login
    user_info = df_users[df_users['UserID'].astype(str) == str(user_id)]
    
    if user_info.empty:
        # กรณีไม่พบ User หรือเป็น Default ADMIN
        user_role = "Admin"
        user_zip = "admin"
        user_dept = "Admin"
    else:
        user_role = user_info.iloc[0]['Role']
        user_zip = str(user_info.iloc[0]['ZIPCODE'])
        user_dept = str(user_info.iloc[0]['Department'])

    # -------------------------------------------------------------
    # Step 2: ดึงข้อมูล Master List และ ข้อมูลรายได้ตามปีที่เลือก
    # -------------------------------------------------------------
    data_spreadsheet = client.open("รายได้ลูกค้ารายองค์กร/หน่วยงานราชการ/ห้างร้านต่างๆ ปย.3")
    
    # อ่าน Master List จากชีต 'รายชื่อ'
    df_master = pd.DataFrame(data_spreadsheet.worksheet("รายชื่อ").get_all_records())
    
    # อ่านข้อมูลยอดขายตามปีที่เลือก (เช่น '2569' หรือ '2568')
    if year == "2569":
        # ดึง Sheet รายเดือนของปี 2569 มารวมกัน
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
            df_sales = pd.DataFrame(data_spreadsheet.worksheet(year).get_all_records())
        except:
            df_sales = pd.DataFrame()

    if df_sales.empty:
        return pd.DataFrame()

    # -------------------------------------------------------------
    # Step 3: VLOOKUP (Merge) รวมตารางยอดขายเข้ากับ Master List
    # -------------------------------------------------------------
    df_merged = pd.merge(
        df_sales, 
        df_master[['รายชื่อลูกค้า', 'กลุ่ม ปจ.', 'สังกัด ปณ.']], 
        on='รายชื่อลูกค้า', 
        how='left'
    )

    # -------------------------------------------------------------
    # Step 4: กรองข้อมูลตาม Role-Based Access Control (RBAC)
    # -------------------------------------------------------------
    # ถ้าเป็น Admin หรือ Reg03 (ผู้บริหาร ปข.3) จะเห็นข้อมูลทั้งหมด
    if user_role in ["Admin", "Reg03", "admin"]:
        return df_merged
        
    # ถ้าเป็น MANAGER หรือ OFFICER ให้กรองตาม 'สังกัด ปณ.' หรือ 'กลุ่ม ปจ.'
    else:
        # ตัดคำว่า 'ปจ.' ออกเพื่อจับคู่กับ 'สังกัด ปณ.' (เช่น 'ปจ.นครราชสีมา' -> 'นครราชสีมา')
        clean_dept = user_dept.replace("ปจ.", "").replace("ปณ.", "").strip()
        
        # กรองข้อมูลที่ 'สังกัด ปณ.' หรือ 'กลุ่ม ปจ.' ตรงกับสังกัดของ User
        filtered_df = df_merged[
            (df_merged['สังกัด ปณ.'].str.contains(clean_dept, na=False)) |
            (df_merged['กลุ่ม ปจ.'].str.contains(clean_dept, na=False)) |
            (df_merged['สังกัด ปณ.'].str.contains(user_zip, na=False))
        ]
        return filtered_df
