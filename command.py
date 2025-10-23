import os
import sys
import subprocess
import shutil
import xml.etree.ElementTree as ET
import json

with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 設定
seeds = [32, 64, 128, 256, 512]
net_name = "re-manhattan"
#net_name = "other"
#net_name = "other2"
network_file = f"{net_name}.net.xml"
#network_file = f"{net_name}.net.xml"
#network_file = f"{net_name}.net.xml"
sumocfg_file = "re-manhattan.sumocfg"
flw_dir = "./flw"
cfg_dir = "./cfg"
fcd_dir = "./fcd"
csv_dir = "./csv"
vehicle_count = 100  # 最初から走らせる台数

# ディレクトリ作成
for d in [flw_dir, cfg_dir, fcd_dir, csv_dir]:
    os.makedirs(d, exist_ok=True)

for seed_val in seeds:
    print(f"\nProcessing seed={seed_val} ...")

    # --- 1. randomTrips.py でトリップ生成 ---
    trips_file_tmp = f"{flw_dir}/trips_tmp_{seed_val}.xml"
    period = 1 / vehicle_count  # 台数固定のために period を調整
    try:
        subprocess.run([
            "python", "randomTrips.py",
            "-n", network_file,
            "--begin", "0",
            "--end", "1",  # 一瞬で生成
            "--period", str(period),
            "--seed", str(seed_val),
            "--trip-attributes", "type='type1'",
            "-o", trips_file_tmp
        ], check=True)
    except subprocess.CalledProcessError:
        print(f"Error at randomTrips.py on seed={seed_val}.")
        sys.exit(1)

    # --- 2. トリップ depart をすべて 0 に変更 ---
    trips_file = f"{flw_dir}/trips_{seed_val}.xml"
    tree = ET.parse(trips_file_tmp)
    root = tree.getroot()

    vtype = ET.Element("vType", attrib=config["vType"])
    root.insert(0, vtype)  # trips の先頭に追加

    for trip in root.findall("trip"):
        trip.set("depart", "0")
        trip.set("type", "car1")  # 全車両に適用
    tree.write(trips_file)

    net_tree = ET.parse(network_file)
    net_root = net_tree.getroot()
    for t in net_root.findall("type"):
        # すべての type に width を統一して付与（既存があれば上書き）
        t.set("width", "200.0")   # 1車線あたり 4.0 m
    net_tree.write(network_file)

    # --- 3. sumocfg をコピー & 編集 ---
    cfg_file = f"{cfg_dir}/re-manhattan_by{seed_val}.sumocfg"
    try:
        shutil.copy(sumocfg_file, cfg_file)
        with open(cfg_file, "r") as f:
            content = f.read()
        # <route-files>と<seed>の置換
        content = content.replace(
            '<route-files value="../flw/re-manhattan_by<seed_val>.flw.xml" />',
            f'<route-files value="../flw/trips_{seed_val}.xml" />'
        ).replace(
            "<seed value='<seed_val>' />",
            f"<seed value='{seed_val}' />"
        )
        # <net-file>の置換
        import re
        netfile_pattern = r'<net-file value="[^"]*" />'
        netfile_replacement = f'<net-file value="../{network_file}" />'
        content = re.sub(netfile_pattern, netfile_replacement, content)
        with open(cfg_file, "w") as f:
            f.write(content)
    except Exception as e:
        print(f"Error at sumocfg handling on seed={seed_val}: {e}")
        sys.exit(1)

    # --- 4. SUMO 実行して FCD 出力 ---
    fcd_file = f"{fcd_dir}/re-manhattan_by{seed_val}.fcd.xml"
    try:
        subprocess.run([
            "sumo",
            "-c", cfg_file,
            "--fcd-output", fcd_file
        ], check=True)
    except subprocess.CalledProcessError:
        print(f"Error at SUMO simulation on seed={seed_val}.")
        sys.exit(1)

    # --- 5. FCD XML → CSV変換 ---
    csv_file = f"{csv_dir}/{net_name}_seed{seed_val}_n{vehicle_count}.csv"
    try:
        tree = ET.parse(fcd_file)
        root = tree.getroot()
        with open(csv_file, "w", newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(["time", "id", "x", "y", "angle", "speed"])
            for timestep in root.findall("timestep"):
                time = timestep.get("time")
                for vehicle in timestep.findall("vehicle"):
                    vid = vehicle.get("id")
                    x = vehicle.get("x")
                    y = vehicle.get("y")
                    angle = vehicle.get("angle")
                    speed = vehicle.get("speed")
                    writer.writerow([time, vid, x, y, angle, speed])
    except Exception as e:
        print(f"Error at converting FCD to CSV on seed={seed_val}: {e}")
        sys.exit(1)

    print(f"Seed {seed_val} finished successfully!")
