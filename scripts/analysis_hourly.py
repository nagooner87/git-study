"""시간대 관점 버스 하차 분석 (가상 더미 데이터).

실행:
    PYTHONIOENCODING=utf-8 python scripts/analysis_hourly.py
결과는 콘솔에 출력되고 reports/analysis_hourly.md 로도 저장됩니다.
"""

from pathlib import Path

import pandas as pd

from read_bus_data import read_alighting, read_routes

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / "analysis_hourly.md"


def period_of(hour: int) -> str:
    if 7 <= hour <= 9:
        return "출근(7~9시)"
    if 17 <= hour <= 21:
        return "퇴근(17~21시)"
    return "그 외"


def md(df: pd.DataFrame) -> str:
    """DataFrame 을 마크다운 표로 변환합니다 (tabulate 불필요)."""
    cols = [df.index.name or ""] + [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for idx, row in df.astype(object).iterrows():
        lines.append("| " + " | ".join([str(idx)] + [str(v) for v in row]) + " |")
    return "\n".join(lines)


def main() -> None:
    route_info, _ = read_routes()
    df = read_alighting()
    total = len(df)
    df["시"] = df["하차일시"].dt.hour
    df["구간"] = df["시"].map(period_of)
    df["30분"] = df["하차일시"].dt.floor("30min").dt.strftime("%H:%M")
    sections: list[str] = []

    def add(title: str, body: str) -> None:
        sections.append(f"## {title}\n\n{body}\n")

    # 1. 시간대별 하차 건수
    hourly = df.groupby("시").agg(하차건수=("하차번호", "count"), 평균요금=("요금(원)", "mean"))
    hourly["비중(%)"] = (hourly["하차건수"] / total * 100).round(1)
    hourly["평균요금"] = hourly["평균요금"].round(0).astype(int)
    hourly.index = [f"{h:02d}시" for h in hourly.index]
    hourly.index.name = "시간대"
    add("1. 시간대별 하차 건수 및 평균 요금", f"전체 {total:,}건\n\n" + md(hourly))

    # 2. 피크 TOP3
    top3 = hourly.nlargest(3, "하차건수")[["하차건수", "비중(%)"]]
    add("2. 피크 시간대 TOP 3", md(top3) + f"\n\nTOP3 합계 비중: {top3['비중(%)'].sum():.1f}%")

    # 3. 구간 비교
    seg = df.groupby("구간").agg(하차건수=("하차번호", "count"), 평균요금=("요금(원)", "mean"),
                              무료비율=("요금(원)", lambda s: (s == 0).mean() * 100))
    hours_in = df.groupby("구간")["시"].nunique()
    seg["시간당건수"] = (seg["하차건수"] / hours_in).round(1)
    seg["비중(%)"] = (seg["하차건수"] / total * 100).round(1)
    seg["평균요금"] = seg["평균요금"].round(0).astype(int)
    seg["무료비율"] = seg["무료비율"].round(1)
    seg = seg.rename(columns={"무료비율": "무료(0원)비율(%)"}).reindex(["출근(7~9시)", "퇴근(17~21시)", "그 외"])
    seg.index.name = "구간"
    add("3. 출근/퇴근/그 외 구간 비교", "시간당건수는 데이터에 존재하는 시간대 수로 나눈 값입니다.\n\n" + md(seg))

    # 4. 30분 단위 추이
    half = df.groupby("30분").size().rename("하차건수").to_frame()
    half["그래프"] = half["하차건수"].map(lambda n: "#" * round(n / half["하차건수"].max() * 30))
    half.index.name = "30분 구간"
    add("4. 30분 단위 추이", md(half))

    # 5. 노선별 피크 시간대
    rows = []
    for rid, g in df.groupby("노선ID"):
        h = g.groupby("시").size()
        rows.append({"노선ID": rid, "하차건수": len(g), "피크시간대": f"{h.idxmax():02d}시",
                     "피크건수": int(h.max()), "피크비중(%)": round(h.max() / len(g) * 100, 1)})
    rt = pd.DataFrame(rows).merge(route_info[["노선ID", "노선번호", "노선유형"]], on="노선ID", how="left")
    rt = rt[["노선ID", "노선번호", "노선유형", "하차건수", "피크시간대", "피크건수", "피크비중(%)"]].set_index("노선ID")
    add("5. 노선별 피크 시간대", md(rt))

    # 6. 구간 x 승객유형 / 결제수단
    pt = pd.crosstab(df["구간"], df["승객유형"], normalize="index").mul(100).round(1)
    pt = pt.reindex(["출근(7~9시)", "퇴근(17~21시)", "그 외"])
    add("6. 구간별 승객유형 구성 (%)", md(pt))

    out = "# 시간대별 하차 분석 (가상 더미 데이터, 2026-10-12)\n\n" + "\n".join(sections)
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(out, encoding="utf-8")
    print(out)
    print(f"\n저장: {REPORT}")


if __name__ == "__main__":
    main()
