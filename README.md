# brmh_hrs_metrics_save

2025년 2월 18일 보라매병원에서 발생한 랜섬웨어 공격으로 CDW(Clinical Data Warehouse) 데이터가 소실된 사건을 계기로, 동일한 상황의 재발을 대비하기 위해 개발한 프로그램입니다. HRS 지표 모니터 화면에서 사용되는 모든 쿼리를 수집하여 지정된 폴더에 백업합니다. 보라매병원의 HRS는 카카오헬스케어 시스템을 사용하고 있어 병원 내부적으로 쿼리를 자동 저장하는 기능이 없어, 본 프로그램은 웹 스크래핑 방식을 활용하여 쿼리를 저장합니다.

보라매병원 보안 정책상 해당 시스템은 사내 IP에서만 접근이 가능하므로, 외부 환경 또는 다른 기관에서 사용할 경우 접근 방식 및 일부 설정을 수정해야 합니다. 현재 프로그램은 Windows 운영체제에서만 지원됩니다.

보라매병원 HRS: http://hrs-metrics.brmh.org/

실행 프로그램 위치: dist\hrs_metrics_save.exe

# 배포방법

STEP 1
```
python -m pip install pyinstaller
```

STEP 2-1 (without icon)
```
python -m PyInstaller --onefile --windowed hrs_metrics_save.py
```

STEP 2-2 (with icon)
```
python -m PyInstaller --onefile --windowed --icon=icn_metrics.ico hrs_metrics_save.py
```
