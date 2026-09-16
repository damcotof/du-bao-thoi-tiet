from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Trạm Giám Sát Thời Tiết", page_icon="🌤", layout="wide"
)

WEATHER_CODES = {
    0: "Trời quang",
    1: "Ít mây",
    2: "Mây rải rác",
    3: "Âm u",
    45: "Sương mù",
    48: "Sương mù đóng băng",
    51: "Mưa phùn nhẹ",
    53: "Mưa phùn vừa",
    55: "Mưa phùn dày",
    61: "Mưa nhỏ",
    63: "Mưa vừa",
    65: "Mưa to",
    71: "Tuyết nhẹ",
    73: "Tuyết vừa",
    75: "Tuyết dày",
    80: "Mưa rào nhẹ",
    81: "Mưa rào vừa",
    82: "Mưa rào to",
    95: "Dông sét",
    96: "Dông kèm mưa đá",
}

# --- Sidebar: Điều khiển tham số đầu vào ---
st.sidebar.header("⚙️ Cấu hình dữ liệu")

# Lựa chọn nhanh hoặc tự nhập
preset = st.sidebar.selectbox(
    "Địa điểm mẫu", ["Tùy chỉnh", "Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng"]
)

if preset == "Hà Nội":
    default_lat, default_lon = 21.0285, 105.8542
elif preset == "TP. Hồ Chí Minh":
    default_lat, default_lon = 10.8231, 106.6297
elif preset == "Đà Nẵng":
    default_lat, default_lon = 16.0544, 108.2022
else:
    default_lat, default_lon = 21.0285, 105.8542

lat = st.sidebar.number_input(
    "Vĩ độ (Latitude)",
    value=default_lat,
    format="%.4f",
    min_value=-90.0,
    max_value=90.0,
)
lon = st.sidebar.number_input(
    "Kinh độ (Longitude)",
    value=default_lon,
    format="%.4f",
    min_value=-180.0,
    max_value=180.0,
)

past_days = st.sidebar.slider(
    "Số ngày quá khứ", min_value=0, max_value=30, value=7
)
forecast_days = st.sidebar.slider(
    "Số ngày dự báo", min_value=1, max_value=16, value=7
)


# --- Hàm gọi API Open-Meteo ---
@st.cache_data(ttl=1800)
def fetch_weather_data(lat, lon, past_days, forecast_days):
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}&"
        f"daily=weathercode,temperature_2m_max,temperature_2m_min,"
        f"relative_humidity_2m_mean,shortwave_radiation_sum,precipitation_sum&"
        f"past_days={past_days}&forecast_days={forecast_days}&"
        f"timezone=auto"
    )
    res = requests.get(url, timeout=15)
    res.raise_for_status()
    return res.json().get("daily", {})


# --- Giao diện Web chính ---
st.title("🌤 Trạm Theo Dõi & Dự Báo Thời Tiết Đa Điểm")
st.caption(
    f"Tọa độ: [{lat}, {lon}] | Quá khứ: {past_days} ngày | Dự báo: {forecast_days} ngày | "
    f"Cập nhật: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
)

if st.button("🔄 Làm mới dữ liệu"):
    st.cache_data.clear()
    st.rerun()

try:
    data = fetch_weather_data(lat, lon, past_days, forecast_days)
    raw_dates = data.get("time", [])

    if not raw_dates:
        st.warning("Không có dữ liệu cho tọa độ đã chọn.")
        st.stop()

    dates = [
        datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m") for d in raw_dates
    ]
    t_max = data.get("temperature_2m_max", [])
    t_min = data.get("temperature_2m_min", [])
    humidity = data.get("relative_humidity_2m_mean", [])
    radiation = data.get("shortwave_radiation_sum", [])
    rain = data.get("precipitation_sum", [])
    codes = data.get("weathercode", [])

    # Xác định vị trí ngày hôm nay
    today_idx = past_days

    # 1. Chỉ số hôm nay
    st.subheader("📍 Tình hình hôm nay (Hiện tại)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Nhiệt độ (Cao/Thấp)", f"{t_max[today_idx]}°C / {t_min[today_idx]}°C")
    col2.metric(
        "Độ ẩm TB",
        f"{humidity[today_idx]}%" if humidity[today_idx] is not None else "N/A",
    )
    col3.metric(
        "Bức xạ mặt trời",
        (
            f"{radiation[today_idx]:.2f} MJ/m²"
            if radiation[today_idx] is not None
            else "N/A"
        ),
    )
    col4.metric(
        "Lượng mưa",
        f"{rain[today_idx]} mm" if rain[today_idx] is not None else "N/A",
    )

    st.markdown("---")

    # 2. Đồ thị Matplotlib
    st.subheader("📊 Biểu đồ trực quan hóa")
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(11, 9), sharex=True)

    # Đồ thị 1: Nhiệt độ
    ax1.plot(
        dates,
        t_max,
        color="#e74c3c",
        marker="o",
        linewidth=2,
        label="Nhiệt độ cao nhất (°C)",
    )
    ax1.plot(
        dates,
        t_min,
        color="#3498db",
        marker="s",
        linewidth=2,
        label="Nhiệt độ thấp nhất (°C)",
    )
    ax1.fill_between(dates, t_min, t_max, color="#bdc3c7", alpha=0.3)
    ax1.axvline(
        x=today_idx,
        color="black",
        linestyle=":",
        alpha=0.7,
        label="Hôm nay",
    )
    ax1.set_ylabel("Nhiệt độ (°C)", fontweight="bold")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right")

    # Đồ thị 2: Độ ẩm
    ax2.plot(
        dates,
        humidity,
        color="#16a085",
        marker="^",
        linewidth=2,
        label="Độ ẩm trung bình (%)",
    )
    ax2.axvline(x=today_idx, color="black", linestyle=":", alpha=0.7)
    ax2.set_ylabel("Độ ẩm (%)", fontweight="bold")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="lower right")

    # Đồ thị 3: Bức xạ mặt trời
    ax3.bar(
        dates,
        radiation,
        color="#f39c12",
        alpha=0.75,
        edgecolor="#d35400",
        label="Bức xạ mặt trời (MJ/m²)",
    )
    ax3.axvline(x=today_idx, color="black", linestyle=":", alpha=0.7)
    ax3.set_ylabel("Bức xạ (MJ/m²)", fontweight="bold")
    ax3.set_xlabel("Thời gian (Ngày/Tháng)", fontweight="bold")
    ax3.grid(True, linestyle="--", alpha=0.5)
    ax3.legend(loc="upper right")

    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("---")

    # 3. Bảng dữ liệu & Xuất CSV
    st.subheader("📋 Dữ liệu chi tiết & Tải về")

    df_export = pd.DataFrame(
        {
            "Ngay": raw_dates,
            "Tinh_trang": [
                WEATHER_CODES.get(c, "Không xác định") for c in codes
            ],
            "Nhiet_do_thap_nhat_C": t_min,
            "Nhiet_do_cao_nhat_C": t_max,
            "Do_am_trung_binh_pct": humidity,
            "Buc_xa_mat_troi_MJ_m2": radiation,
            "Luong_mua_mm": rain,
        }
    )

    # Nút bấm tải CSV
    csv_file = df_export.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="📥 Tải xuống dữ liệu (.CSV)",
        data=csv_file,
        file_name=f"thoi_tiet_{lat}_{lon}_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

    st.dataframe(df_export, use_container_width=True)

except Exception as e:
    st.error(f"Lỗi khi xử lý dữ liệu: {e}")