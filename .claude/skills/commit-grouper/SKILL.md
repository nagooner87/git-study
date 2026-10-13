---
name: commit-grouper
description: 작업 디렉터리의 변경 사항(수정/추가/삭제 파일)을 분석해 목적이 비슷한 파일끼리 묶고, Conventional Commits 기반 컨벤션(저장소의 기존 커밋 스타일 우선)에 맞춰 커밋 메시지를 작성한 뒤 묶음별로 커밋하는 스킬. 사용자가 "커밋해줘", "커밋 메시지 써줘", "변경사항 정리해서 커밋", "커밋 나눠줘", "git commit", "변경 파일 묶어서 커밋" 등을 말하거나, 작업을 마치고 커밋을 언급하면 명시적으로 스킬 이름을 부르지 않아도 반드시 이 스킬을 사용할 것.
---

# commit-grouper

변경 사항을 한꺼번에 커밋하면 이력이 읽기 어렵고, 되돌리거나 리뷰하기도 힘들다.
이 스킬은 변경 파일을 **하나의 목적 단위**로 묶어 각각 적절한 커밋 메시지와 함께 커밋한다.

## 1. 변경 사항 수집

```bash
git status --porcelain=v1 -uall
git diff HEAD --stat
git diff HEAD            # 내용이 큰 경우 파일별로 나눠 확인
git log --format='%s' -n 30
```

- 새로 추가된(untracked) 파일은 diff에 나오지 않으므로 직접 열어 내용을 확인한다.
- 변경 사항이 없으면 그렇게 알리고 끝낸다.
- `.env`, 키/토큰, 대용량 바이너리, 빌드 산출물처럼 커밋하면 안 될 듯한 파일은 묶음에서 제외하고 사용자에게 알린다.

## 2. 저장소 컨벤션 파악 (가장 먼저)

`git log`의 기존 메시지를 보고 **그 저장소의 스타일을 따른다.** 팀이 이미 쓰는 형식을 깨면 이력이 오히려 어지러워지기 때문이다.
확인할 것: type 목록, 구분자(`type: ` / `type : `), scope 사용 여부, 언어(한글/영어), 문장 끝맺음(`~추가`, `~하였습니다`), 본문/푸터 관례.
CLAUDE.md나 README, CONTRIBUTING에 규칙이 적혀 있으면 그것이 최우선이다.

기존 이력이 없거나 규칙을 알 수 없으면 아래 기본 컨벤션을 쓴다.

### 기본 컨벤션 (Conventional Commits 1.0)

```
<type>(<scope>): <subject>

<body>            # 선택: 무엇을/왜 (어떻게는 코드가 말해 준다)

<footer>          # 선택: BREAKING CHANGE, 이슈 번호 등
```

| type | 용도 |
|---|---|
| feat | 새 기능 추가 |
| fix | 버그 수정 |
| docs | 문서만 변경 (README, 주석, 리포트 문서) |
| style | 동작에 영향 없는 서식 변경 (공백, 세미콜론, 포맷터) |
| refactor | 기능/버그와 무관한 구조 개선 |
| perf | 성능 개선 |
| test | 테스트 추가/수정 |
| build | 빌드 시스템, 의존성 (requirements.txt, package.json) |
| ci | CI 설정 |
| chore | 그 외 잡무 (.gitignore, 설정 파일) |
| revert | 이전 커밋 되돌리기 |

작성 규칙: subject는 50자 안팎, 명령/명사형으로 간결하게, 마침표 없이. 영어일 때는 명령형 현재시제("add", not "added").
subject만 보고 변경 의도가 드러나야 한다. "수정", "update", "작업 내용 반영" 같은 메시지는 쓰지 않는다.

## 3. 묶는 기준

**파일 경로가 아니라 변경의 목적**으로 묶는다. 디렉터리가 달라도 같은 목적이면 한 커밋이다.

- 하나의 기능을 이루는 코드 + 그 기능의 테스트 + 그 기능의 문서/리포트 → 한 커밋 (예: `scripts/analysis_stop.py` + `reports/analysis_stop.md`)
- 서로 독립적인 기능/수정 → 각각 별도 커밋
- 포맷팅·리네임·리팩터링은 기능 변경과 섞지 않고 분리 (섞이면 diff 리뷰가 어렵다)
- 의존성/빌드/설정 변경은 별도 커밋 (`build`, `chore`)
- 문서만 바뀐 파일들은 `docs` 하나로
- 데이터/샘플 파일은 그것을 만들거나 쓰는 코드와 같은 커밋에 두되, 단독이면 따로

판단이 애매한 경우의 기준: "이 커밋 하나만 되돌려도 저장소가 말이 되는가?" 그렇다면 올바른 단위다.

한 파일에 서로 다른 목적의 변경이 섞여 있으면 억지로 쪼개지 말고(대화형 `git add -p`는 사용할 수 없다), 더 비중 있는 쪽 커밋에 넣고 사용자에게 섞여 있다고 알린다.

## 4. 계획을 먼저 보여주고 확인받기

커밋은 이력에 남는 행위이므로 실행 전에 계획을 표로 보여주고 승인받는다.

```
| # | 메시지 | 파일 |
|---|---|---|
| 1 | feat : 노선별 하차 분석 추가 | scripts/analysis_route.py, reports/analysis_route.md |
| 2 | docs : README 실행 방법 보완 | README.md |
```

제외한 파일이 있으면 이유와 함께 적는다. 사용자가 수정을 요청하면 계획을 고쳐 다시 보여준다.

## 5. 커밋 실행

승인 후 묶음마다 순서대로:

```bash
git add -- <파일들>
git commit -m "<subject>" -m "<body, 있을 때만>"
```

- `git add -A` / `git add .` 는 쓰지 않는다. 묶음 밖의 파일이 딸려 들어가기 때문이다. 삭제/이름 변경 파일도 경로를 명시한다.
- 의존 관계가 있으면 그 순서로 커밋한다 (설정/의존성 → 기능 → 문서).
- 훅 실패 시 `--no-verify`로 우회하지 말고 원인을 고쳐 새 커밋으로 만든다.
- push는 요청받았을 때만 한다.
- 환경에서 커밋 푸터(Co-Authored-By 등)를 요구하면 모든 커밋 끝에 붙인다.
- 마지막에 `git log --oneline -n <커밋 수>` 와 `git status`로 결과를 보여준다.

## 예시

**입력**: `scripts/analysis_hourly.py`, `reports/analysis_hourly.md` 추가, `README.md` 오타 수정, `requirements.txt`에 openpyxl 추가
**저장소 스타일**: `feat : ...` (한글, 콜론 앞 공백)

**출력**:
1. `build : openpyxl 의존성 추가` — requirements.txt
2. `feat : 시간대별 하차 분석 추가` — scripts/analysis_hourly.py, reports/analysis_hourly.md
3. `docs : README 오타 수정` — README.md
