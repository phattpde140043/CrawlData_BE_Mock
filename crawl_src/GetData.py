from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request  # thêm import này ở đầu file
from fastapi.responses import JSONResponse

import requests
import pandas as pd
import os
import csv

# --- Khởi tạo ứng dụng FastAPI ---
app = FastAPI(title="Country Info API", version="1.0")

# --- Thêm phần này ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# --- Cấu hình API ---
COUNTRY_INFO_API = "https://restcountries.com/v3.1/all?fields=name,latlng,cca3,cca2,region"
HEADER = {"User-Agent": "Mozilla/5.0"}

# --- Hàm lấy danh sách quốc gia ---
def get_country_list():
    response = requests.get(COUNTRY_INFO_API, headers=HEADER)
    
    if response.status_code != 200:
        raise Exception(f"Lỗi khi gọi API: {response.status_code}")
    
    data = response.json()
    records = []

    for country in data:
        if "name" in country and "latlng" in country:
            name = country["name"]["common"]
            lat, lon = country["latlng"]
            code = country.get("cca3", "")
            iso_2 = country.get("cca2", "")
            region = country.get("region", "")
            records.append({
                "country": name,
                "latitude": lat,
                "longitude": lon,
                "code": code,
                "iso_2": iso_2,
                "region": region
            })
    
    return records


# --- API Endpoint: Lấy danh sách quốc gia ---
@app.get("/countries")
def get_countries():
    """
    Gọi API RestCountries, xử lý dữ liệu và trả kết quả JSON.
    """
    try:
        countries = get_country_list()
        df = pd.DataFrame(countries)
        json_data = df.to_dict(orient="records")
        return JSONResponse(content=json_data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)




@app.post("/contact")
async def contact_form(request: Request):
    data = await request.json()
    print("📩 New contact form submission:")
    print(data)

    # --- Tên file ---
    file_path = "customer_data.csv"

    # --- Kiểm tra file có tồn tại hay chưa ---
    file_exists = os.path.isfile(file_path)

    # --- Ghi dữ liệu vào file CSV (append mode) ---
    with open(file_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["name", "phone", "email", "message"])
        
        # Nếu file mới -> ghi header
        if not file_exists:
            writer.writeheader()

        # Ghi dòng dữ liệu mới
        writer.writerow({
            "name": data.get("name", ""),
            "phone": data.get("phone", ""),
            "email": data.get("email", ""),
            "message": data.get("message", "")
        })

    return {"message": "✅ Dữ liệu đã được lưu vào customer_data.csv!"}

@app.get("/indicator")
async def get_gdp(country: str):
    """
    Lấy dữ liệu GDP 20 năm gần nhất từ World Bank API theo mã ISO3.
    Trả về:
    - status: "success" | "nodata" | "error"
    - message: mô tả ngắn
    - records: danh sách GDP nếu có
    """
    try:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/NY.GDP.MKTP.CD?format=json&per_page=500"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()

        # 🧩 1️⃣ Trường hợp API trả về message lỗi
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "message" in data[0]:
            msg = data[0]["message"][0].get("value", "Invalid request")
            print(f"⚠️ [LOG] Không có dữ liệu cho quốc gia: {country} ({msg})")
            return JSONResponse(
                content={
                    "status": "nodata",
                    "country": country.upper(),
                    "message": f"Không có dữ liệu GDP cho quốc gia: {country.upper()}",
                    "records": []
                },
                status_code=200
            )

        # 🧩 2️⃣ Trường hợp không có mảng dữ liệu hợp lệ
        if len(data) < 2 or not isinstance(data[1], list) or len(data[1]) == 0:
            print(f"⚠️ [LOG] Không có dữ liệu GDP cho quốc gia: {country}")
            return JSONResponse(
                content={
                    "status": "nodata",
                    "country": country.upper(),
                    "message": f"Không có dữ liệu GDP cho quốc gia: {country.upper()}",
                    "records": []
                },
                status_code=200
            )

        # 🧩 3️⃣ Có dữ liệu GDP
        records = [
            {
                "year": item["date"],
                "gdp_usd": item["value"]
            }
            for item in data[1]
            if item["value"] is not None
        ][:20]

        print(f"📊 [LOG] Nhận yêu cầu GDP cho {country}: {len(records)} năm dữ liệu")

        return JSONResponse(
            content={
                "status": "success",
                "country": country.upper(),
                "message": f"Tìm thấy {len(records)} năm dữ liệu GDP cho {country.upper()}",
                "records": records
            },
            status_code=200
        )

    except Exception as e:
        print(f"❌ [ERROR] {e}")
        return JSONResponse(
            content={
                "status": "error",
                "country": country.upper(),
                "message": str(e),
                "records": []
            },
            status_code=500
        )


# --- API Gốc ---
@app.get("/")
def root():
    return {"message": "Welcome to Country Info API! Use /countries to get data."}
