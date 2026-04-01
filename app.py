from flask import Flask, render_template, request
from dataclasses import dataclass
from typing import List, Dict

app = Flask(__name__)


# =========================================================
# DATA SENSOR
# =========================================================
@dataclass
class SensorData:
    ph: float
    ec: float
    suhu: float
    kelembapan: float
    umur_tanaman: int


# =========================================================
# TARGET EC BERDASARKAN UMUR TANAMAN
# =========================================================
def get_target_ec(umur_tanaman: int):
    if umur_tanaman <= 7:
        return 0.8, 1.2
    elif umur_tanaman <= 21:
        return 1.2, 1.8
    else:
        return 1.8, 2.4


# =========================================================
# AI SMART HYDRONITY
# =========================================================
def smart_hydronity_ai(data: SensorData) -> Dict:
    ph_min, ph_max = 5.5, 6.5
    suhu_min, suhu_max = 20, 30
    hum_min, hum_max = 50, 80

    ec_min, ec_max = get_target_ec(data.umur_tanaman)

    aksi: List[str] = []
    catatan: List[str] = []

    rekomendasi_nutrisi_ml = 0
    rekomendasi_air_ml = 0
    rekomendasi_ph_up_ml = 0
    rekomendasi_ph_down_ml = 0

    jumlah_masalah = 0

    # Cek pH
    if data.ph < ph_min:
        selisih = ph_min - data.ph
        rekomendasi_ph_up_ml = round(5 * selisih, 2)
        aksi.append("Tambahkan larutan pH Up")
        catatan.append(f"pH terlalu rendah ({data.ph})")
        jumlah_masalah += 1
    elif data.ph > ph_max:
        selisih = data.ph - ph_max
        rekomendasi_ph_down_ml = round(5 * selisih, 2)
        aksi.append("Tambahkan larutan pH Down")
        catatan.append(f"pH terlalu tinggi ({data.ph})")
        jumlah_masalah += 1
    else:
        catatan.append(f"pH normal ({data.ph})")

    # Cek EC
    if data.ec < ec_min:
        selisih = ec_min - data.ec
        rekomendasi_nutrisi_ml = round(100 + 100 * selisih, 2)
        aksi.append("Aktifkan pompa nutrisi AB mix")
        catatan.append(f"EC terlalu rendah ({data.ec}), target {ec_min}-{ec_max}")
        jumlah_masalah += 1
    elif data.ec > ec_max:
        selisih = data.ec - ec_max
        rekomendasi_air_ml = round(150 + 100 * selisih, 2)
        aksi.append("Aktifkan pompa air bersih untuk pengenceran")
        catatan.append(f"EC terlalu tinggi ({data.ec}), target {ec_min}-{ec_max}")
        jumlah_masalah += 1
    else:
        catatan.append(f"EC normal ({data.ec})")

    # Cek suhu
    if data.suhu < suhu_min:
        aksi.append("Suhu rendah, cek lingkungan atau pencahayaan")
        catatan.append(f"Suhu terlalu rendah ({data.suhu}°C)")
        jumlah_masalah += 1
    elif data.suhu > suhu_max:
        aksi.append("Suhu tinggi, lakukan ventilasi atau pendinginan")
        catatan.append(f"Suhu terlalu tinggi ({data.suhu}°C)")
        jumlah_masalah += 1
    else:
        catatan.append(f"Suhu normal ({data.suhu}°C)")

    # Cek kelembapan
    if data.kelembapan < hum_min:
        aksi.append("Kelembapan rendah, pertimbangkan misting")
        catatan.append(f"Kelembapan terlalu rendah ({data.kelembapan}%)")
        jumlah_masalah += 1
    elif data.kelembapan > hum_max:
        aksi.append("Kelembapan tinggi, tingkatkan sirkulasi udara")
        catatan.append(f"Kelembapan terlalu tinggi ({data.kelembapan}%)")
        jumlah_masalah += 1
    else:
        catatan.append(f"Kelembapan normal ({data.kelembapan}%)")

    # Menentukan status
    if jumlah_masalah == 0:
        status = "AMAN"
        aksi.append("Tidak perlu koreksi")
    elif jumlah_masalah <= 2:
        status = "PERLU KOREKSI"
    else:
        status = "KRITIS"

    return {
        "status": status,
        "target_ec": {"min": ec_min, "max": ec_max},
        "rekomendasi": {
            "nutrisi_ml": rekomendasi_nutrisi_ml,
            "air_ml": rekomendasi_air_ml,
            "ph_up_ml": rekomendasi_ph_up_ml,
            "ph_down_ml": rekomendasi_ph_down_ml
        },
        "aksi": aksi,
        "catatan": catatan
    }


# =========================================================
# ROUTE WEB
# =========================================================
@app.route("/", methods=["GET", "POST"])
def index():
    hasil = None

    if request.method == "POST":
        try:
            data = SensorData(
                ph=float(request.form["ph"]),
                ec=float(request.form["ec"]),
                suhu=float(request.form["suhu"]),
                kelembapan=float(request.form["kelembapan"]),
                umur_tanaman=int(request.form["umur_tanaman"])
            )
            hasil = smart_hydronity_ai(data)
        except ValueError:
            hasil = {
                "status": "ERROR",
                "aksi": ["Input tidak valid"],
                "catatan": ["Pastikan semua data diisi dengan angka"]
            }

    return render_template("index.html", hasil=hasil)


if __name__ == "__main__":
    app.run(debug=True)