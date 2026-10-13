"""노선 관점 버스 하차 분석 (가상 더미 데이터).

실행:
    PYTHONIOENCODING=utf-8 python scripts/analysis_route.py
결과는 콘솔 출력과 reports/analysis_route.md 로 저장됩니다.
"""

from pathlib import Path

import pandas as pd

from read_bus_data import read_alighting, read_routes

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "reports" / "analysis_route.md"


def build_route_table(alighting: pd.DataFrame, route_info: pd.DataFrame) -> pd.DataFrame:
    """노선별 하차 건수/요금/운행 차량 수/정류장당 밀도 등을 계산합니다."""
    agg = (
        alighting.groupby("노선ID")
        .agg(
            하차건수=("하차번호", "count"),
            요금합계=("요금(원)", "sum"),
            평균요금=("요금(원)", "mean"),
            차량수=("차량번호", "nunique"),
        )
        .reset_index()
    )
    t = route_info.merge(agg, on="노선ID", how="left").fillna({"하차건수": 0, "요금합계": 0, "차량수": 0})
    t["차량당_하차건수"] = (t["하차건수"] / t["차량수"].where(t["차량수"] > 0)).round(1)
    t["정류장당_하차밀도"] = (t["하차건수"] / t["정류장수"]).round(2)
    t["평균요금"] = t["평균요금"].round(1)
    return t.sort_values("하차건수", ascending=False).reset_index(drop=True)


def build_type_table(t: pd.DataFrame) -> pd.DataFrame:
    g = (
        t.groupby("노선유형")
        .agg(
            노선수=("노선ID", "count"),
            하차건수=("하차건수", "sum"),
            요금합계=("요금합계", "sum"),
            차량수=("차량수", "sum"),
            평균정류장수=("정류장수", "mean"),
            평균배차간격=("배차간격(분)", "mean"),
        )
        .reset_index()
    )
    g["노선당_평균하차"] = (g["하차건수"] / g["노선수"]).round(1)
    g["차량당_하차건수"] = (g["하차건수"] / g["차량수"]).round(1)
    g["건당_평균요금"] = (g["요금합계"] / g["하차건수"]).round(1)
    g["하차비중(%)"] = (g["하차건수"] / g["하차건수"].sum() * 100).round(1)
    g[["평균정류장수", "평균배차간격"]] = g[["평균정류장수", "평균배차간격"]].round(1)
    return g.sort_values("하차건수", ascending=False).reset_index(drop=True)


def build_corr(t: pd.DataFrame) -> pd.DataFrame:
    cols = ["배차간격(분)", "정류장수", "차량수"]
    rows = []
    for c in cols:
        rows.append({"변수": c, "대 하차건수": t[c].corr(t["하차건수"]), "대 정류장당_하차밀도": t[c].corr(t["정류장당_하차밀도"])})
    return pd.DataFrame(rows).round(3)


def to_md(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False) if _has_tabulate() else _simple_md(df)


def _has_tabulate() -> bool:
    try:
        import tabulate  # noqa: F401
        return True
    except ImportError:
        return False


def _simple_md(df: pd.DataFrame) -> str:
    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "|".join("---" for _ in df.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def main() -> None:
    route_info, _ = read_routes()
    alighting = read_alighting()
    t = build_route_table(alighting, route_info)
    types = build_type_table(t)
    corr = build_corr(t)

    cols = ["노선ID", "노선번호", "노선유형", "정류장수", "배차간격(분)", "하차건수", "요금합계", "평균요금", "차량수", "차량당_하차건수", "정류장당_하차밀도"]
    top = t[cols].head(10)
    bottom = t[cols].tail(5)

    summary = pd.DataFrame(
        {
            "항목": ["총 하차 건수", "총 요금(원)", "노선 수", "운행 차량 수(합)", "노선당 평균 하차", "차량당 평균 하차"],
            "값": [
                f"{len(alighting):,}",
                f"{alighting['요금(원)'].sum():,}",
                len(t),
                f"{int(t['차량수'].sum()):,}",
                round(t["하차건수"].mean(), 1),
                round(t["하차건수"].sum() / t["차량수"].sum(), 1),
            ],
        }
    )

    sections = [
        ("전체 요약", summary),
        ("노선유형별 비교", types),
        ("하차 건수 상위 10개 노선", top),
        ("하차 건수 하위 5개 노선", bottom),
        ("상관계수 (피어슨, 노선 단위)", corr),
    ]
    lines = ["# 노선별 하차 분석", "", "- 기준일: 2026-10-12 (가상 더미 데이터)", ""]
    for title, df in sections:
        lines += [f"## {title}", "", to_md(df), ""]
    lines += ["## 한계", "", "가상으로 생성한 더미 데이터이므로 수치를 실제 현상으로 해석하면 안 됩니다.", ""]
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    for title, df in sections:
        print(f"\n## {title}")
        print(df.to_string(index=False))


if __name__ == "__main__":
    main()
