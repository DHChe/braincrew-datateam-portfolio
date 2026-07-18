# Issue tracker: GitHub

이 저장소의 명세서와 작업 티켓은 GitHub Issues에서 관리한다. 모든 작업은 저장소 안에서 `gh` 명령어를 사용한다.

## 기본 명령

- 생성: `gh issue create`
- 조회: `gh issue view <번호> --comments`
- 목록: `gh issue list`
- 댓글: `gh issue comment <번호>`
- 라벨 변경: `gh issue edit <번호> --add-label <라벨>` 또는 `--remove-label <라벨>`
- 종료: `gh issue close <번호>`

GitHub 저장소는 현재 작업 디렉터리의 `origin` 원격에서 자동으로 판별한다.

## 스킬 연결

- 스킬에서 "작업 관리 시스템에 게시한다"고 하면 GitHub Issue를 생성한다.
- 관련 티켓을 읽을 때는 본문, 댓글, 라벨을 함께 확인한다.
- `to-spec`은 상위 구현 명세 이슈를 만든다.
- `to-tickets`는 구현 티켓을 선행 순서대로 만든다.
- `to-spec`과 `to-tickets`가 만든 구현 가능 작업에는 `ready-for-agent` 라벨을 적용한다.

## 선행 관계

가능하면 GitHub의 작업 의존 관계 기능을 사용한다. 지원되지 않으면 티켓 본문에 `Blocked by: #번호`를 기록한다.

선행 티켓이 모두 닫힌 작업만 구현 가능한 상태로 판단한다. 선행 조건이 없거나 모든 선행 조건이 닫힌 작업이 현재 구현 가능한 작업 집합(frontier)이다.

## Pull requests as a triage surface

**PRs as a request surface: no.**

PR은 새로운 작업 요청을 접수하는 창구로 사용하지 않는다. PR은 이미 승인된 티켓의 구현 결과를 검토하고 병합하는 용도로 사용한다.

GitHub Issues와 PR은 번호 공간을 공유하므로 `#42`가 어느 종류인지 불분명하면 먼저 `gh pr view 42`를 실행하고, PR이 아니면 `gh issue view 42`로 확인한다.
