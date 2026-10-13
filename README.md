# git-study

Git 기본 사용법을 익히기 위한 학습용 저장소입니다.

## 목차

1. [Git이란?](#git이란)
2. [설치 및 초기 설정](#설치-및-초기-설정)
3. [저장소 만들기](#저장소-만들기)
4. [기본 작업 흐름](#기본-작업-흐름)
5. [브랜치](#브랜치)
6. [원격 저장소 (GitHub)](#원격-저장소-github)
7. [변경 사항 되돌리기](#변경-사항-되돌리기)
8. [자주 쓰는 명령어 요약](#자주-쓰는-명령어-요약)

---

## Git이란?

Git은 파일의 변경 이력을 기록하고 관리하는 **분산 버전 관리 시스템**입니다.

- 파일을 수정할 때마다 **커밋(commit)** 으로 스냅샷을 저장합니다.
- 언제든지 이전 커밋 상태로 돌아갈 수 있습니다.
- **브랜치(branch)** 로 작업을 나누어 독립적으로 진행할 수 있습니다.
- **원격 저장소(remote)** 를 통해 여러 사람과 코드를 공유합니다.

### 핵심 개념

| 용어 | 설명 |
| --- | --- |
| 작업 디렉터리 (Working Directory) | 실제로 파일을 수정하는 공간 |
| 스테이징 영역 (Staging Area) | 다음 커밋에 포함될 변경 사항을 모아 두는 공간 |
| 저장소 (Repository) | 커밋 이력이 저장되는 `.git` 폴더 |
| 커밋 (Commit) | 변경 사항을 하나의 기록으로 저장한 것 |
| 브랜치 (Branch) | 커밋을 가리키는 이동 가능한 포인터 |
| 원격 (Remote) | 인터넷이나 네트워크에 있는 저장소 (예: GitHub) |

```
작업 디렉터리 ──git add──▶ 스테이징 영역 ──git commit──▶ 저장소(.git)
                                                          │
                                                   git push ▼
                                                      원격 저장소
```

---

## 설치 및 초기 설정

### 1. 설치

- Windows: [git-scm.com](https://git-scm.com/)에서 설치 파일을 받아 설치합니다.
- macOS: `brew install git`
- Linux (Debian/Ubuntu): `sudo apt install git`

설치 확인:

```bash
git --version
```

### 2. 사용자 정보 설정

커밋에 기록될 이름과 이메일을 설정합니다. 최초 한 번만 하면 됩니다.

```bash
git config --global user.name "본인 이름"
git config --global user.email "본인 이메일"
```

설정 확인:

```bash
git config --list
```

### 3. 기본 브랜치 이름 설정 (선택)

```bash
git config --global init.defaultBranch main
```

---

## 저장소 만들기

### 새 저장소 만들기

```bash
mkdir my-project
cd my-project
git init
```

`git init`을 실행하면 현재 폴더에 `.git` 폴더가 생성되며 Git 저장소가 됩니다.

### 기존 저장소 복제하기

```bash
git clone https://github.com/사용자명/저장소명.git
```

### `.gitignore` 파일

Git이 추적하지 않을 파일이나 폴더를 지정합니다. 비밀번호, 빌드 결과물, 의존성 폴더 등을 제외할 때 사용합니다.

```gitignore
# 예시
node_modules/
.env
*.log
.DS_Store
```

---

## 기본 작업 흐름

Git을 사용하는 가장 기본적인 흐름입니다.

```bash
# 1. 현재 상태 확인
git status

# 2. 파일 수정 후 스테이징
git add 파일명        # 특정 파일만 추가
git add .             # 변경된 모든 파일 추가

# 3. 커밋
git commit -m "커밋 메시지"

# 4. 이력 확인
git log --oneline
```

### 커밋 메시지 작성 팁

- 한 커밋에는 **하나의 목적**만 담습니다.
- 제목은 간결하게, 무엇을 왜 바꿨는지 씁니다.

```
좋은 예: 로그인 폼 유효성 검사 추가
나쁜 예: 수정
```

### 변경 내용 확인

```bash
git diff              # 스테이징 전 변경 내용
git diff --staged     # 스테이징된 변경 내용
git show 커밋해시      # 특정 커밋의 내용
```

---

## 브랜치

브랜치는 기존 코드에 영향을 주지 않고 새로운 작업을 진행하기 위해 사용합니다.

```bash
git branch                  # 브랜치 목록 확인
git branch 새브랜치이름       # 브랜치 생성
git switch 브랜치이름         # 브랜치 이동
git switch -c 새브랜치이름    # 생성과 동시에 이동
```

### 브랜치 병합 (merge)

```bash
git switch main
git merge 작업브랜치이름
```

병합 충돌(conflict)이 발생하면 해당 파일을 열어 충돌 표시(`<<<<<<<`, `=======`, `>>>>>>>`)를 확인하고 내용을 정리한 뒤 다시 커밋합니다.

```bash
git add 충돌파일
git commit
```

### 브랜치 삭제

```bash
git branch -d 브랜치이름     # 병합된 브랜치 삭제
git branch -D 브랜치이름     # 강제 삭제
```

---

## 원격 저장소 (GitHub)

### 원격 저장소 연결

```bash
git remote add origin https://github.com/사용자명/저장소명.git
git remote -v                 # 연결 확인
```

### 올리기 (push)

```bash
git push -u origin main       # 최초 1회: 업스트림 설정
git push                      # 이후에는 이것만 입력
```

### 내려받기 (pull / fetch)

```bash
git fetch origin              # 원격 변경 내용만 가져오기 (병합 X)
git pull origin main          # 가져와서 현재 브랜치에 병합
```

### 협업 기본 흐름

1. `main`에서 작업 브랜치를 만든다: `git switch -c feature/기능명`
2. 작업하고 커밋한다.
3. 원격에 올린다: `git push -u origin feature/기능명`
4. GitHub에서 **Pull Request(PR)** 를 열어 리뷰를 받는다.
5. 승인되면 `main`에 병합한다.

---

## 변경 사항 되돌리기

### 아직 커밋하지 않은 변경 취소

```bash
git restore 파일명              # 작업 디렉터리의 변경 취소
git restore --staged 파일명     # 스테이징 취소 (파일 내용은 유지)
```

### 마지막 커밋 메시지 수정

```bash
git commit --amend -m "새 메시지"
```

> 이미 push한 커밋은 `--amend`나 `reset`으로 고치지 않는 것을 권장합니다.

### 특정 커밋을 되돌리는 새 커밋 만들기 (안전)

```bash
git revert 커밋해시
```

이력을 남기면서 해당 변경을 취소하므로 공유된 브랜치에서 사용하기 적합합니다.

### 커밋 자체를 되돌리기 (주의)

```bash
git reset --soft HEAD~1   # 커밋만 취소, 변경 사항은 스테이징 상태로 유지
git reset --mixed HEAD~1  # 커밋과 스테이징 취소, 변경 사항은 작업 디렉터리에 유지
git reset --hard HEAD~1   # 커밋과 변경 사항 모두 삭제 (복구 어려움, 주의)
```

---

## 자주 쓰는 명령어 요약

| 목적 | 명령어 |
| --- | --- |
| 저장소 생성 | `git init` |
| 저장소 복제 | `git clone <URL>` |
| 상태 확인 | `git status` |
| 스테이징 | `git add <파일>` |
| 커밋 | `git commit -m "메시지"` |
| 이력 보기 | `git log --oneline --graph` |
| 브랜치 생성 및 이동 | `git switch -c <브랜치>` |
| 브랜치 병합 | `git merge <브랜치>` |
| 원격 올리기 | `git push` |
| 원격 내려받기 | `git pull` |
| 변경 취소 | `git restore <파일>` |
| 커밋 되돌리기 (안전) | `git revert <커밋>` |
