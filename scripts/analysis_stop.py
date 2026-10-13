"""정류장 관점 버스 하차 분석.

실행:
    PYTHONIOENCODING=utf-8 python scripts/analysis_stop.py
결과는 콘솔에 출력되고 reports/analysis_stop.md 로도 저장됩니다.
"""

from pathlib import Path

import pandas as pd

from read_bus_data import read_alighting, read_routes

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / "analysis_stop.md"


def build_stop_table(alighting: pd.DataFrame, route_stops: pd.DataFrame) -> pd.DataFrame:
    """정류장 단위 마스터: 이름, 좌표, 경유 노선 수, 하차 건수(0 포함)."""
    stops = route_stops.groupby("정류장ID").agg(
        정류장명=("정류장명", "first"), 위도=("위도", "first"), 경도=("경도", "first"),
        경유노선수=("노선ID", "nunique"),
    )
    counts = alighting.groupby("하차정류장ID").size().rename("하차건수")
    stops = stops.join(counts).fillna({"하차건수": 0})
    stops["하차건수"] = stops["하차건수"].astype(int)
    stops["하차비율(%)"] = (stops["하차건수"] / stops["하차건수"].sum() * 100).round(2)
    return stops.reset_index()


def transfer_analysis(stops: pd.DataFrame) -> pd.DataFrame:
    """경유 노선 수별 정류장 수, 하차량 합/평균, 상관계수는 별도 계산."""
    g = stops.groupby("경유노선수").agg(
        정류장수=("정류장ID", "count"), 하차합계=("하차건수", "sum"), 정류장당평균하차=("하차건수", "mean"),
    )
    g["정류장당평균하차"] = g["정류장당평균하차"].round(1)
    return g.reset_index()


def position_analysis(alighting: pd.DataFrame, route_stops: pd.DataFrame) -> pd.DataFrame:
    """노선 내 순번을 앞/중간/뒤 3구간(상대 위치 기준)으로 나눠 하차 분포를 계산."""
    rs = route_stops.copy()
    n = rs.groupby("노선ID")["순번"].transform("max")
    rel = (rs["순번"] - 1) / (n - 1)
    rs["구간"] = pd.cut(rel, [-0.001, 1 / 3, 2 / 3, 1.001], labels=["앞", "중간", "뒤"])
    m = alighting.merge(rs[["노선ID", "정류장ID", "구간"]], left_on=["노선ID", "하차정류장ID"],
                        right_on=["노선ID", "정류장ID"], how="left")
    dist = m.groupby("구간", observed=True).size().rename("하차건수").to_frame()
    dist["비율(%)"] = (dist["하차건수"] / dist["하차건수"].sum() * 100).round(1)
    slots = rs.groupby("구간", observed=True).size().rename("정류장슬롯수")
    dist = dist.join(slots)
    dist["슬롯당평균하차"] = (dist["하차건수"] / dist["정류장슬롯수"]).round(1)
    return dist.reset_index()


def geo_analysis(stops: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """정류장 좌표를 위도/경도 3분위 구간(남-중-북, 서-중-동)으로 나눠 하차량 집계."""
    s = stops.copy()
    s["위도구간"] = pd.qcut(s["위도"], 3, labels=["남", "중", "북"])
    s["경도구간"] = pd.qcut(s["경도"], 3, labels=["서", "중", "동"])
    by_lat = s.groupby("위도구간", observed=True).agg(
        정류장수=("정류장ID", "count"), 위도범위=("위도", lambda x: f"{x.min():.3f}~{x.max():.3f}"), 하차건수=("하차건수", "sum"))
    by_lon = s.groupby("경도구간", observed=True).agg(
        정류장수=("정류장ID", "count"), 경도범위=("경도", lambda x: f"{x.min():.3f}~{x.max():.3f}"), 하차건수=("하차건수", "sum"))
    grid = s.pivot_table(index="위도구간", columns="경도구간", values="하차건수", aggfunc="sum", observed=True)
    grid = grid.iloc[::-1]  # 북쪽이 위
    grid.columns = [str(c) for c in grid.columns]
    return by_lat.reset_index(), by_lon.reset_index(), grid.reset_index()


def md(df: pd.DataFrame) -> str:
    """tabulate 없이 마크다운 표 문자열을 만듭니다."""
    df = df.copy()
    df.columns = [str(c) for c in df.columns]
    rows = [[str(v) for v in r] for r in df.itertuples(index=False)]
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "|".join(["---"] * len(df.columns)) + "|"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def main() -> None:
    route_info, route_stops = read_routes()
    alighting = read_alighting()
    stops = build_stop_table(alighting, route_stops)
    cols = ["정류장ID", "정류장명", "경유노선수", "하차건수", "하차비율(%)"]

    out: list[str] = ["# 정류장별 하차 분석", "",
                      f"- 대상일: {alighting['하차일시'].dt.date.min()} / 하차 {len(alighting):,}건 / 정류장 {len(stops)}개 / 노선 {len(route_info)}개",
                      "- 데이터는 가상 더미입니다.", ""]

    def section(title: str, df: pd.DataFrame, note: str = "") -> None:
        out.extend([f"## {title}", ""] + ([note, ""] if note else []) + [md(df), ""])

    section("1. 하차 상위 10개 정류장", stops.nlargest(10, "하차건수")[cols])
    section("2. 하차 하위 10개 정류장", stops.nsmallest(10, "하차건수")[cols])

    zero = stops[stops["하차건수"] == 0]
    stats = stops["하차건수"].describe().round(1)
    out.extend(["## 3. 하차가 한 번도 없는 정류장", "",
                f"{len(zero)}개" + (": " + ", ".join(zero["정류장명"] + "(" + zero["정류장ID"] + ")") if len(zero) else " (모든 정류장에서 하차 발생)"), "",
                f"정류장당 하차 건수: 평균 {stats['mean']}, 중앙값 {stats['50%']}, 최소 {stats['min']:.0f}, 최대 {stats['max']:.0f}", ""])

    corr = stops["경유노선수"].corr(stops["하차건수"])
    section("4. 환승 정류장(경유 노선 수)과 하차량", transfer_analysis(stops),
            f"경유 노선 수와 하차 건수의 피어슨 상관계수: {corr:.3f}")
    multi = stops[stops["경유노선수"] >= 2]
    out.extend([f"환승 정류장(2개 이상 노선 경유) {len(multi)}개가 전체 하차의 {multi['하차건수'].sum() / len(alighting) * 100:.1f}% 차지", ""])
    section("환승 정류장 상위 10 (경유 노선 수 기준)", stops.nlargest(10, ["경유노선수", "하차건수"])[cols])

    section("5. 노선 내 순번 구간별 하차 분포", position_analysis(alighting, route_stops),
            "구간: 노선 내 상대 위치 3등분(앞/중간/뒤). 슬롯 = 노선-정류장 조합 수.")

    by_lat, by_lon, grid = geo_analysis(stops)
    out.extend(["## 6. 좌표 기반 지리적 분포", ""])
    section("위도 3분위 구간별 하차", by_lat)
    section("경도 3분위 구간별 하차", by_lon)
    section("위도 x 경도 격자별 하차 (북쪽이 위)", grid)

    text = "\n".join(out)
    print(text)
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(f"\n[저장] {REPORT}")


if __name__ == "__main__":
    main()
