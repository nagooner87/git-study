"""승객/요금 관점 버스 하차 데이터 분석.

실행:
    PYTHONIOENCODING=utf-8 python scripts/analysis_passenger.py
결과는 콘솔에 출력하고 reports/analysis_passenger.md 로도 저장합니다.
"""

from pathlib import Path

import pandas as pd

from read_bus_data import read_alighting, read_routes

ROOT = Path(__file__).resolve().parent.parent
REPORT_FILE = ROOT / "reports" / "analysis_passenger.md"

TYPE_ORDER = ["일반", "청소년", "어린이", "경로우대", "장애인"]
PAY_ORDER = ["교통카드", "모바일", "현금"]
ROUTE_TYPE_ORDER = ["간선", "지선", "광역", "순환"]
BASE_FARE = 1400  # 일반 요금 (무임 가정 환산 기준)


def by_passenger_type(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("승객유형").agg(건수=("하차번호", "count"), 요금합계=("요금(원)", "sum"), 건당요금=("요금(원)", "mean"))
    g["건수비중(%)"] = g["건수"] / g["건수"].sum() * 100
    g["요금비중(%)"] = g["요금합계"] / g["요금합계"].sum() * 100
    g = g.reindex(TYPE_ORDER)[["건수", "건수비중(%)", "요금합계", "요금비중(%)", "건당요금"]]
    g.loc["전체"] = [len(df), 100.0, df["요금(원)"].sum(), 100.0, df["요금(원)"].mean()]
    return g.round(1)


def by_payment(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("결제수단").agg(건수=("하차번호", "count"), 요금합계=("요금(원)", "sum"))
    g["건수비중(%)"] = g["건수"] / g["건수"].sum() * 100
    g["요금비중(%)"] = g["요금합계"] / g["요금합계"].sum() * 100
    return g.reindex(PAY_ORDER).round(1)


def crosstab_type_pay(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cnt = pd.crosstab(df["승객유형"], df["결제수단"]).reindex(index=TYPE_ORDER, columns=PAY_ORDER)
    pct = (cnt.div(cnt.sum(axis=1), axis=0) * 100).round(1)  # 승객유형별 행 비중
    return cnt, pct


def hourly_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """시간대별 승객유형 건수 및 경로우대 비중."""
    d = df.assign(시간대=df["하차일시"].dt.hour)
    cnt = pd.crosstab(d["시간대"], d["승객유형"]).reindex(columns=TYPE_ORDER, fill_value=0)
    cnt["합계"] = cnt.sum(axis=1)
    cnt["경로우대비중(%)"] = (cnt["경로우대"] / cnt["합계"] * 100).round(1)
    cnt["무임비중(%)"] = ((cnt["경로우대"] + cnt["장애인"]) / cnt["합계"] * 100).round(1)
    return cnt


def free_fare_impact(df: pd.DataFrame) -> pd.DataFrame:
    free = df["요금(원)"] == 0
    n_free = int(free.sum())
    actual = int(df["요금(원)"].sum())
    hypo = actual + n_free * BASE_FARE
    rows = {
        "전체 건수": len(df),
        "무임(0원) 건수": n_free,
        "무임 비율(%)": round(n_free / len(df) * 100, 1),
        "유임 건당 평균요금(원)": round(df.loc[~free, "요금(원)"].mean(), 1),
        "전체 건당 평균요금(원)": round(df["요금(원)"].mean(), 1),
        "실제 요금 수입(원)": actual,
        f"무임을 일반요금({BASE_FARE}원)으로 가정한 수입(원)": hypo,
        "무임으로 인한 수입 감소분(원)": hypo - actual,
        "감소율(%)": round((hypo - actual) / hypo * 100, 1),
    }
    return pd.DataFrame({"값": rows})


def route_type_mix(df: pd.DataFrame, route_info: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    m = df.merge(route_info[["노선ID", "노선유형"]], on="노선ID", how="left")
    cnt = pd.crosstab(m["노선유형"], m["승객유형"]).reindex(index=ROUTE_TYPE_ORDER, columns=TYPE_ORDER, fill_value=0)
    pct = (cnt.div(cnt.sum(axis=1), axis=0) * 100).round(1)
    rev = m.groupby("노선유형").agg(건수=("하차번호", "count"), 요금합계=("요금(원)", "sum"), 건당요금=("요금(원)", "mean"))
    rev["무임비율(%)"] = m.assign(f=m["요금(원)"] == 0).groupby("노선유형")["f"].mean() * 100
    return pct, rev.reindex(ROUTE_TYPE_ORDER).round(1)


def to_md(table: pd.DataFrame) -> str:
    """tabulate 없이 DataFrame 을 마크다운 표로 변환합니다."""
    t = table.rename_axis(table.index.name or "항목").reset_index()
    t.columns = [str(c) for c in t.columns]

    def fmt(v) -> str:
        if isinstance(v, float):
            return f"{v:,.0f}" if v.is_integer() else f"{v:,.1f}"
        if isinstance(v, (int,)) or hasattr(v, "item") and not isinstance(v, str):
            return f"{v:,}"
        return str(v)

    lines = ["| " + " | ".join(t.columns) + " |", "|" + "|".join("---" for _ in t.columns) + "|"]
    for row in t.itertuples(index=False):
        lines.append("| " + " | ".join(fmt(v) for v in row) + " |")
    return chr(10).join(lines)


def build_report(df: pd.DataFrame, route_info: pd.DataFrame) -> str:
    sections: list[tuple[str, pd.DataFrame]] = []
    sections.append(("1. 승객유형별 건수·비중·요금", by_passenger_type(df)))
    sections.append(("2. 결제수단별 건수·비중", by_payment(df)))
    cnt, pct = crosstab_type_pay(df)
    sections.append(("3-1. 승객유형 x 결제수단 (건수)", cnt))
    sections.append(("3-2. 승객유형 x 결제수단 (승객유형별 행 비중 %)", pct))
    hourly = hourly_pattern(df)
    sections.append(("4-1. 시간대별 승객유형 건수와 경로우대/무임 비중", hourly))
    busy = hourly[hourly["합계"] >= 100].sort_values("경로우대비중(%)", ascending=False).head(5)
    sections.append(("4-2. 경로우대 비중 상위 시간대 (하차 100건 이상)", busy[["합계", "경로우대", "경로우대비중(%)"]]))
    sections.append(("5. 무임(0원) 승객과 요금 수입 영향", free_fare_impact(df)))
    pct_rt, rev_rt = route_type_mix(df, route_info)
    sections.append(("6-1. 노선유형별 승객유형 구성 (%)", pct_rt))
    sections.append(("6-2. 노선유형별 요금 현황", rev_rt))

    out = ["# 승객/요금 관점 하차 분석", "", f"- 분석 대상: {len(df):,}건 (2026-10-12, 가상 더미 데이터)", ""]
    for title, table in sections:
        out += [f"## {title}", "", to_md(table), ""]
    return "\n".join(out)


def main() -> None:
    df = read_alighting()
    route_info, _ = read_routes()
    report = build_report(df, route_info)
    print(report)
    REPORT_FILE.parent.mkdir(exist_ok=True)
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"\n저장: {REPORT_FILE}")


if __name__ == "__main__":
    main()
