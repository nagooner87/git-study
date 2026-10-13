"""버스 노선 데이터와 하차 데이터를 가상으로 생성해 xlsx 파일로 저장합니다.

실행:
    python scripts/generate_dummy_data.py

생성 결과:
    data/bus_routes.xlsx    - 시트 "노선정보", "노선정류장"
    data/bus_alighting.xlsx - 시트 "하차데이터"
"""

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
N_ROUTES = 10
N_STOPS = 60
N_ALIGHTING = 5000
BASE_DATE = datetime(2026, 10, 12)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

ROUTE_TYPES = ["간선", "지선", "순환", "광역"]
PASSENGER_TYPES = ["일반", "청소년", "어린이", "경로우대", "장애인"]
PASSENGER_WEIGHTS = [0.55, 0.12, 0.08, 0.18, 0.07]
PAY_TYPES = ["교통카드", "모바일", "현금"]
PAY_WEIGHTS = [0.75, 0.20, 0.05]
FARE = {"일반": 1400, "청소년": 720, "어린이": 450, "경로우대": 0, "장애인": 0}

PLACE_PREFIX = ["가온", "새별", "푸른", "하늘", "은빛", "단풍", "햇살", "맑은", "바람", "구름"]
PLACE_SUFFIX = ["시청앞", "사거리", "공원", "아파트", "역입구", "종합병원", "대학교", "시장", "행정센터", "체육관"]


def make_stops(rng: random.Random) -> pd.DataFrame:
    """가상 정류장 목록을 만듭니다. 좌표는 대략 서울 부근 범위에서 무작위로 잡습니다."""
    names = set()
    while len(names) < N_STOPS:
        names.add(f"{rng.choice(PLACE_PREFIX)}{rng.choice(PLACE_SUFFIX)}")
    rows = []
    for i, name in enumerate(sorted(names), start=1):
        rows.append(
            {
                "정류장ID": f"ST{i:04d}",
                "정류장명": name,
                "위도": round(37.45 + rng.random() * 0.12, 6),
                "경도": round(126.90 + rng.random() * 0.14, 6),
            }
        )
    return pd.DataFrame(rows)


def make_routes(rng: random.Random, stops: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """노선 기본 정보(노선정보)와 노선별 정류장 순서(노선정류장)를 만듭니다."""
    route_rows, route_stop_rows = [], []
    stop_ids = stops["정류장ID"].tolist()

    for i in range(1, N_ROUTES + 1):
        route_id = f"R{i:03d}"
        route_no = f"{rng.randint(1, 9)}{rng.randint(0, 9)}{rng.choice(['', '-1', '-2'])}"
        route_type = rng.choice(ROUTE_TYPES)
        n_stops = rng.randint(15, 25)
        picked = rng.sample(stop_ids, n_stops)

        route_rows.append(
            {
                "노선ID": route_id,
                "노선번호": route_no,
                "노선유형": route_type,
                "기점정류장ID": picked[0],
                "종점정류장ID": picked[-1],
                "정류장수": n_stops,
                "배차간격(분)": rng.choice([5, 8, 10, 12, 15, 20]),
            }
        )
        for seq, stop_id in enumerate(picked, start=1):
            route_stop_rows.append({"노선ID": route_id, "순번": seq, "정류장ID": stop_id})

    routes = pd.DataFrame(route_rows)
    route_stops = pd.DataFrame(route_stop_rows).merge(stops, on="정류장ID", how="left")
    return routes, route_stops


def make_alighting(rng: random.Random, routes: pd.DataFrame, route_stops: pd.DataFrame) -> pd.DataFrame:
    """하차 기록을 만듭니다. 각 기록은 실제 노선의 정류장에서 발생한 것으로 가정합니다."""
    # 노선별 정류장 목록(순번 순) 미리 준비
    stops_by_route = {
        rid: g.sort_values("순번")["정류장ID"].tolist() for rid, g in route_stops.groupby("노선ID")
    }
    # 노선별 차량 번호 (노선마다 차량 5~8대)
    vehicles_by_route = {
        rid: [f"{rid}-V{v:02d}" for v in range(1, rng.randint(5, 8) + 1)] for rid in routes["노선ID"]
    }

    rows = []
    for n in range(1, N_ALIGHTING + 1):
        route_id = rng.choice(routes["노선ID"].tolist())
        stop_list = stops_by_route[route_id]
        # 기점(0번째)에서는 하차하지 않도록 두 번째 정류장 이후에서 선택
        stop_id = rng.choice(stop_list[1:])
        passenger = rng.choices(PASSENGER_TYPES, weights=PASSENGER_WEIGHTS)[0]
        pay = rng.choices(PAY_TYPES, weights=PAY_WEIGHTS)[0]

        # 하루 중 출근(07~09시), 퇴근(17~19시) 시간대에 몰리도록 가중치 부여
        hour = rng.choices(range(5, 24), weights=[1, 2, 5, 9, 7, 4, 3, 3, 4, 4, 3, 3, 3, 4, 6, 8, 7, 4, 2])[0]
        ts = BASE_DATE + timedelta(hours=hour, minutes=rng.randint(0, 59), seconds=rng.randint(0, 59))

        rows.append(
            {
                "하차번호": f"AL{n:06d}",
                "하차일시": ts,
                "노선ID": route_id,
                "차량번호": rng.choice(vehicles_by_route[route_id]),
                "하차정류장ID": stop_id,
                "승객유형": passenger,
                "결제수단": pay,
                "요금(원)": FARE[passenger],
            }
        )

    df = pd.DataFrame(rows).sort_values("하차일시").reset_index(drop=True)
    df["하차번호"] = [f"AL{i:06d}" for i in range(1, len(df) + 1)]
    return df


def main() -> None:
    rng = random.Random(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    stops = make_stops(rng)
    routes, route_stops = make_routes(rng, stops)
    alighting = make_alighting(rng, routes, route_stops)

    routes_path = DATA_DIR / "bus_routes.xlsx"
    with pd.ExcelWriter(routes_path, engine="openpyxl") as writer:
        routes.to_excel(writer, sheet_name="노선정보", index=False)
        route_stops.to_excel(writer, sheet_name="노선정류장", index=False)

    alighting_path = DATA_DIR / "bus_alighting.xlsx"
    alighting.to_excel(alighting_path, sheet_name="하차데이터", index=False)

    print(f"저장: {routes_path} (노선 {len(routes)}개, 노선정류장 {len(route_stops)}행)")
    print(f"저장: {alighting_path} (하차 {len(alighting)}건)")


if __name__ == "__main__":
    main()
