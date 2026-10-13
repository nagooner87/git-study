"""생성된 버스 노선/하차 xlsx 파일을 pandas로 읽어 확인하는 예제입니다.

실행 (먼저 generate_dummy_data.py 를 실행해 data/ 폴더를 만들어 주세요):
    python scripts/read_bus_data.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

ROUTES_FILE = DATA_DIR / "bus_routes.xlsx"
ALIGHTING_FILE = DATA_DIR / "bus_alighting.xlsx"

ROUTE_INFO_COLUMNS = ["노선ID", "노선번호", "노선유형", "기점정류장ID", "종점정류장ID", "정류장수", "배차간격(분)"]
ROUTE_STOP_COLUMNS = ["노선ID", "순번", "정류장ID", "정류장명", "위도", "경도"]
ALIGHTING_COLUMNS = ["하차번호", "하차일시", "노선ID", "차량번호", "하차정류장ID", "승객유형", "결제수단", "요금(원)"]


def read_routes(path: Path = ROUTES_FILE) -> tuple[pd.DataFrame, pd.DataFrame]:
    """노선 파일의 두 시트(노선정보, 노선정류장)를 읽습니다."""
    route_info = pd.read_excel(path, sheet_name="노선정보", dtype={"노선ID": str})
    route_stops = pd.read_excel(path, sheet_name="노선정류장", dtype={"노선ID": str, "정류장ID": str})
    _check_columns(route_info, ROUTE_INFO_COLUMNS, "노선정보")
    _check_columns(route_stops, ROUTE_STOP_COLUMNS, "노선정류장")
    return route_info, route_stops


def read_alighting(path: Path = ALIGHTING_FILE) -> pd.DataFrame:
    """하차 데이터 시트를 읽습니다. 하차일시는 datetime 으로 변환됩니다."""
    df = pd.read_excel(
        path,
        sheet_name="하차데이터",
        dtype={"노선ID": str, "하차정류장ID": str, "차량번호": str},
        parse_dates=["하차일시"],
    )
    _check_columns(df, ALIGHTING_COLUMNS, "하차데이터")
    return df


def _check_columns(df: pd.DataFrame, expected: list[str], sheet: str) -> None:
    """파일 규칙(컬럼명)을 지키는지 확인합니다. 빠진 컬럼이 있으면 바로 알려 줍니다."""
    missing = [c for c in expected if c not in df.columns]
    if missing:
        raise ValueError(f"[{sheet}] 시트에 필요한 컬럼이 없습니다: {missing}")


def summarize_by_route(alighting: pd.DataFrame, route_info: pd.DataFrame) -> pd.DataFrame:
    """노선별 하차 건수, 총 요금, 평균 요금을 집계합니다."""
    summary = (
        alighting.groupby("노선ID")
        .agg(하차건수=("하차번호", "count"), 총요금=("요금(원)", "sum"), 평균요금=("요금(원)", "mean"))
        .reset_index()
    )
    summary = route_info[["노선ID", "노선번호", "노선유형"]].merge(summary, on="노선ID", how="left")
    summary["평균요금"] = summary["평균요금"].round(1)
    return summary.sort_values("하차건수", ascending=False).reset_index(drop=True)


def top_alighting_stops(alighting: pd.DataFrame, route_stops: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """하차가 많이 발생한 정류장 상위 n개를 정류장명과 함께 반환합니다."""
    stop_names = route_stops.drop_duplicates("정류장ID")[["정류장ID", "정류장명"]]
    counts = (
        alighting.groupby("하차정류장ID").size().rename("하차건수").reset_index()
        .rename(columns={"하차정류장ID": "정류장ID"})
    )
    return counts.merge(stop_names, on="정류장ID", how="left").nlargest(n, "하차건수")


def hourly_alighting(alighting: pd.DataFrame) -> pd.Series:
    """시간대(0~23시)별 하차 건수를 집계합니다."""
    return alighting.groupby(alighting["하차일시"].dt.hour).size().rename("하차건수")


def main() -> None:
    route_info, route_stops = read_routes()
    alighting = read_alighting()

    print("=== 노선 정보 (앞 5행) ===")
    print(route_info.head())

    print("\n=== 하차 데이터 (앞 5행) ===")
    print(alighting.head())
    print(f"\n하차 데이터 전체 {len(alighting):,}건")

    print("\n=== 노선별 하차 요약 ===")
    print(summarize_by_route(alighting, route_info).to_string(index=False))

    print("\n=== 하차 상위 정류장 TOP 5 ===")
    print(top_alighting_stops(alighting, route_stops).to_string(index=False))

    print("\n=== 시간대별 하차 건수 ===")
    print(hourly_alighting(alighting).to_string())


if __name__ == "__main__":
    main()
