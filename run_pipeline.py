"""
run_pipeline.py
파이프라인 실행 진입점.

기본: daily_orchestrator.py 실행 (수집 + CSV 변환)
--publish: 수집 완료 후 publish_from_csv.py도 실행
"""
import sys
import subprocess


def run(cmd, label):
    print(f"\n[Pipeline] {label}")
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"  [FAIL] {label} 실패 (exit code {result.returncode})")
    else:
        print(f"  [OK] {label} 완료")
    return result.returncode


def main():
    publish = "--publish" in sys.argv

    print("=" * 52)
    print("  Antigravity Pipeline")
    if publish:
        print("  모드: 수집 + Notion 발행")
    else:
        print("  모드: 수집 (CSV 저장까지)")
        print("  Notion 발행: python3 run_pipeline.py --publish")
    print("=" * 52)

    # Step 1: 수집 + CSV 변환
    code = run(["python3", "execution/daily_orchestrator.py"], "수집 파이프라인 (tabelog → maps → CSV)")
    if code != 0:
        print("\n[Pipeline] 수집 단계 오류 — 파이프라인 중단")
        sys.exit(code)

    # Step 2 (선택): Notion 발행
    if publish:
        code = run(["python3", "execution/publish_from_csv.py"], "Notion 발행 (staged_restaurants.csv → Notion DB)")
        if code != 0:
            print("\n[Pipeline] Notion 발행 실패")
            sys.exit(code)

    print("\n[Pipeline] 완료")


if __name__ == "__main__":
    main()
