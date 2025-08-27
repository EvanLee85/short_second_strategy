# 项目结构文档

**生成时间:** 2025-08-27 17:57:36
**项目根目录:** `/home/evan/short_second_strategy`

## 项目概览

### 整体统计

- **总文件数:** 287
- **Python文件:** 72
- **配置文件:** 12
- **子目录数:** 9
- **总大小:** 1.4 MB

## 目录结构

```
└── short_second_strategy (287 files, 1.4 MB)
    ├── .env.example (671.0 B)
    ├── README.md (11.8 KB)
    ├── create_init_files.py (2.3 KB)
    ├── dependency_scanner.py (3.2 KB)
    ├── example.html (51.8 KB)
    ├── package.json (0.0 B)
    ├── pip_freeze.txt (1.5 KB)
    ├── project_structure_scanner.py (15.0 KB)
    ├── 工程进度.md (26.8 KB)
    ├── backend (48 files, 226.6 KB)
    │   ├── __init__.py (24.0 B)
    │   ├── app.py (606.0 B)
    │   ├── analysis (4 files, 640.0 B)
    │   │   ├── capital_flow.py (0.0 B)
    │   │   ├── correlation.py (0.0 B)
    │   │   ├── sentiment.py (0.0 B)
    │   │   └── technical.py (640.0 B)
    │   ├── api (3 files, 5.6 KB)
    │   │   ├── auth.py (0.0 B)
    │   │   ├── routes.py (5.6 KB)
    │   │   └── websocket.py (0.0 B)
    │   ├── backtest (6 files, 24.4 KB)
    │   │   ├── engine.py (0.0 B)
    │   │   ├── metrics.py (0.0 B)
    │   │   ├── optimizer.py (0.0 B)
    │   │   ├── zipline_csv_bundle.py (5.4 KB)
    │   │   ├── zipline_export.py (17.4 KB)
    │   │   └── zipline_integration.py (1.5 KB)
    │   ├── config (2 files, 5.7 KB)
    │   │   ├── settings.py (243.0 B)
    │   │   └── thresholds.yaml (5.5 KB)
    │   ├── core (9 files, 51.7 KB)
    │   │   ├── backtester.py (7.1 KB)
    │   │   ├── entry_signals.py (9.3 KB)
    │   │   ├── executor.py (0.0 B)
    │   │   ├── indicators.py (4.3 KB)
    │   │   ├── macro_filter.py (2.4 KB)
    │   │   ├── risk_manager.py (15.2 KB)
    │   │   ├── sector_rotation.py (3.0 KB)
    │   │   ├── sentry.py (3.9 KB)
    │   │   └── stock_selector.py (6.6 KB)
    │   ├── data (12 files, 120.1 KB)
    │   │   ├── __init__.py (24.0 B)
    │   │   ├── cache.py (4.5 KB)
    │   │   ├── exceptions.py (14.4 KB)
    │   │   ├── fetcher copy.py (11.3 KB)
    │   │   ├── fetcher.py (21.3 KB)
    │   │   ├── merge.py (11.1 KB)
    │   │   ├── normalize.py (16.7 KB)
    │   │   └── providers (5 files, 40.8 KB)
    │   │       ├── __init__.py (24.0 B)
    │   │       ├── akshare_provider.py (11.2 KB)
    │   │       ├── base.py (4.7 KB)
    │   │       ├── csv_provider.py (13.3 KB)
    │   │       └── tushare_provider.py (11.6 KB)
    │   ├── tests (3 files, 0.0 B)
    │   │   ├── test_macro.py (0.0 B)
    │   │   ├── test_rotation.py (0.0 B)
    │   │   └── test_signals.py (0.0 B)
    │   ├── utils (4 files, 0.0 B)
    │   │   ├── __init__.py (0.0 B)
    │   │   ├── helpers.py (0.0 B)
    │   │   ├── logger.py (0.0 B)
    │   │   └── validators.py (0.0 B)
    │   └── zipline (3 files, 17.8 KB)
    │       ├── algo_breakout_min.py (5.7 KB)
    │       ├── algo_sss_strategy.py (5.2 KB)
    │       └── algo_sss_strategy_relaxed.py (6.9 KB)
    ├── config (7 files, 6.2 KB)
    │   ├── data_providers.yaml (347.0 B)
    │   ├── development.env (0.0 B)
    │   ├── docker-compose.yml (0.0 B)
    │   ├── logging.yaml (4.5 KB)
    │   ├── production.env (0.0 B)
    │   ├── security.yaml (1.2 KB)
    │   └── thresholds.yaml (157.0 B)
    ├── data (17 files, 13.7 KB)
    │   ├── cache (8 files, 5.7 KB)
    │   │   └── ohlcv (8 files, 5.7 KB)
    │   │       ├── ohlcv_akshare_000001.XSHE_2024-01-01_2024-01-31_1d.csv (957.0 B)
    │   │       ├── ohlcv_akshare_000002.XSHE_2024-01-01_2024-01-31_1d.csv (964.0 B)
    │   │       ├── ohlcv_akshare_002415.XSHE_2024-01-01_2024-01-31_1d.csv (1.0 KB)
    │   │       ├── ohlcv_akshare_600000.XSHG_2024-01-01_2024-01-31_1d.csv (943.0 B)
    │   │       ├── ohlcv_akshare_600519.XSHG_2024-01-01_2024-01-31_1d.csv (1.2 KB)
    │   │       ├── ohlcv_csv_002415.XSHE_2024-01-02_2024-01-05_1d.csv (191.0 B)
    │   │       ├── ohlcv_csv_002415.XSHE_2024-01-02_2024-01-10_1d.csv (314.0 B)
    │   │       └── ohlcv_csv_002415_2024-01-01_2024-01-05_1d.csv (210.0 B)
    │   ├── export (0 files, 0.0 B)
    │   ├── market (0 files, 0.0 B)
    │   ├── ohlcv (1 files, 193.0 B)
    │   │   └── 002415.csv (193.0 B)
    │   ├── stocks (0 files, 0.0 B)
    │   ├── zipline_csv (7 files, 7.5 KB)
    │   │   ├── .gitkeep (0.0 B)
    │   │   ├── 000001.csv (1.1 KB)
    │   │   ├── 000002.csv (1.1 KB)
    │   │   ├── 002415.csv (303.0 B)
    │   │   ├── 600000.csv (1.1 KB)
    │   │   ├── 600519.csv (1.3 KB)
    │   │   └── TEST.csv (2.7 KB)
    │   └── zipline_csv_out (1 files, 317.0 B)
    │       └── 002415.csv (317.0 B)
    ├── database (2 files, 0.0 B)
    │   ├── init.sql (0.0 B)
    │   ├── schema.sql (0.0 B)
    │   └── migrations (0 files, 0.0 B)
    ├── docs (3 files, 0.0 B)
    │   ├── api.md (0.0 B)
    │   ├── deployment.md (0.0 B)
    │   └── strategy.md (0.0 B)
    ├── frontend (8 files, 0.0 B)
    │   ├── index.html (0.0 B)
    │   ├── assets (0 files, 0.0 B)
    │   │   ├── fonts (0 files, 0.0 B)
    │   │   └── images (0 files, 0.0 B)
    │   ├── css (2 files, 0.0 B)
    │   │   ├── components.css (0.0 B)
    │   │   └── style.css (0.0 B)
    │   └── js (5 files, 0.0 B)
    │       ├── app.js (0.0 B)
    │       ├── charts.js (0.0 B)
    │       ├── dashboard.js (0.0 B)
    │       ├── utils.js (0.0 B)
    │       └── websocket.js (0.0 B)
    ├── scripts (4 files, 25.5 KB)
    │   ├── backup.sh (0.0 B)
    │   ├── deploy.sh (0.0 B)
    │   ├── manage.sh (25.5 KB)
    │   └── monitor.py (0.0 B)
    ├── tests (21 files, 119.8 KB)
    │   ├── debug_data.py (2.6 KB)
    │   ├── debug_sss.py (8.0 KB)
    │   ├── diagnostic.py (10.7 KB)
    │   ├── optimize_parallel.py (17.9 KB)
    │   ├── optimize_params.py (14.1 KB)
    │   ├── optimize_params_parallel_description.md (4.1 KB)
    │   ├── requirements_list.py (3.2 KB)
    │   ├── run_all_tests.py (5.8 KB)
    │   ├── run_backtest_demo.py (899.0 B)
    │   ├── run_cache_tests.py (16.5 KB)
    │   ├── run_data_tests.py (2.9 KB)
    │   ├── run_fetcher_step12_tests.py (6.0 KB)
    │   ├── run_indicator_tests.py (4.0 KB)
    │   ├── run_merge_tests.py (6.3 KB)
    │   ├── run_provider_akshare_smoke.py (857.0 B)
    │   ├── run_sentry_tests.py (2.4 KB)
    │   ├── run_sentry_yaml_tests.py (3.9 KB)
    │   ├── run_zipline_step1_check.py (634.0 B)
    │   ├── run_zipline_step2_bundle.py (1.0 KB)
    │   ├── run_zipline_step3_algo.py (4.3 KB)
    │   └── run_zipline_step4_strategy.py (3.7 KB)
    └── var (168 files, 907.6 KB)
        └── zipline (168 files, 907.6 KB)
            ├── extension.py (527.0 B)
            ├── min_algo_perf.pkl (17.5 KB)
            ├── sss_strategy_perf.pkl (15.6 KB)
            └── data (165 files, 874.0 KB)
                └── sss_csv (165 files, 874.0 KB)
                    ├── 2025-08-23T12;03;49.690233 (33 files, 174.8 KB)
                    │   ├── adjustments.sqlite (84.0 KB)
                    │   ├── assets-7.sqlite (88.0 KB)
                    │   ├── daily_equities.bcolz (30 files, 2.6 KB)
                    │   │   ├── __attrs__ (217.0 B)
                    │   │   ├── __rootdirs__ (67.0 B)
                    │   │   ├── close (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── day (4 files, 368.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 178.0 B)
                    │   │   │   │   └── __0.blp (178.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── high (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── id (4 files, 241.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 51.0 B)
                    │   │   │   │   └── __0.blp (51.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── low (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── open (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   └── volume (4 files, 355.0 B)
                    │   │       ├── __attrs__ (3.0 B)
                    │   │       ├── data (1 files, 165.0 B)
                    │   │       │   └── __0.blp (165.0 B)
                    │   │       └── meta (2 files, 187.0 B)
                    │   │           ├── sizes (48.0 B)
                    │   │           └── storage (139.0 B)
                    │   └── minute_equities.bcolz (1 files, 172.0 B)
                    │       └── metadata.json (172.0 B)
                    ├── 2025-08-23T12;03;51.743590 (33 files, 174.8 KB)
                    │   ├── adjustments.sqlite (84.0 KB)
                    │   ├── assets-7.sqlite (88.0 KB)
                    │   ├── daily_equities.bcolz (30 files, 2.6 KB)
                    │   │   ├── __attrs__ (217.0 B)
                    │   │   ├── __rootdirs__ (67.0 B)
                    │   │   ├── close (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── day (4 files, 368.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 178.0 B)
                    │   │   │   │   └── __0.blp (178.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── high (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── id (4 files, 241.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 51.0 B)
                    │   │   │   │   └── __0.blp (51.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── low (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── open (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   └── volume (4 files, 355.0 B)
                    │   │       ├── __attrs__ (3.0 B)
                    │   │       ├── data (1 files, 165.0 B)
                    │   │       │   └── __0.blp (165.0 B)
                    │   │       └── meta (2 files, 187.0 B)
                    │   │           ├── sizes (48.0 B)
                    │   │           └── storage (139.0 B)
                    │   └── minute_equities.bcolz (1 files, 172.0 B)
                    │       └── metadata.json (172.0 B)
                    ├── 2025-08-23T12;13;41.242635 (33 files, 174.8 KB)
                    │   ├── adjustments.sqlite (84.0 KB)
                    │   ├── assets-7.sqlite (88.0 KB)
                    │   ├── daily_equities.bcolz (30 files, 2.6 KB)
                    │   │   ├── __attrs__ (217.0 B)
                    │   │   ├── __rootdirs__ (67.0 B)
                    │   │   ├── close (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── day (4 files, 368.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 178.0 B)
                    │   │   │   │   └── __0.blp (178.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── high (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── id (4 files, 241.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 51.0 B)
                    │   │   │   │   └── __0.blp (51.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── low (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── open (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   └── volume (4 files, 355.0 B)
                    │   │       ├── __attrs__ (3.0 B)
                    │   │       ├── data (1 files, 165.0 B)
                    │   │       │   └── __0.blp (165.0 B)
                    │   │       └── meta (2 files, 187.0 B)
                    │   │           ├── sizes (48.0 B)
                    │   │           └── storage (139.0 B)
                    │   └── minute_equities.bcolz (1 files, 172.0 B)
                    │       └── metadata.json (172.0 B)
                    ├── 2025-08-23T12;19;01.144144 (33 files, 174.8 KB)
                    │   ├── adjustments.sqlite (84.0 KB)
                    │   ├── assets-7.sqlite (88.0 KB)
                    │   ├── daily_equities.bcolz (30 files, 2.6 KB)
                    │   │   ├── __attrs__ (217.0 B)
                    │   │   ├── __rootdirs__ (67.0 B)
                    │   │   ├── close (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── day (4 files, 368.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 178.0 B)
                    │   │   │   │   └── __0.blp (178.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── high (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── id (4 files, 241.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 51.0 B)
                    │   │   │   │   └── __0.blp (51.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── low (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   ├── open (4 files, 362.0 B)
                    │   │   │   ├── __attrs__ (3.0 B)
                    │   │   │   ├── data (1 files, 172.0 B)
                    │   │   │   │   └── __0.blp (172.0 B)
                    │   │   │   └── meta (2 files, 187.0 B)
                    │   │   │       ├── sizes (48.0 B)
                    │   │   │       └── storage (139.0 B)
                    │   │   └── volume (4 files, 355.0 B)
                    │   │       ├── __attrs__ (3.0 B)
                    │   │       ├── data (1 files, 165.0 B)
                    │   │       │   └── __0.blp (165.0 B)
                    │   │       └── meta (2 files, 187.0 B)
                    │   │           ├── sizes (48.0 B)
                    │   │           └── storage (139.0 B)
                    │   └── minute_equities.bcolz (1 files, 172.0 B)
                    │       └── metadata.json (172.0 B)
                    └── 2025-08-23T12;29;12.987217 (33 files, 174.8 KB)
                        ├── adjustments.sqlite (84.0 KB)
                        ├── assets-7.sqlite (88.0 KB)
                        ├── daily_equities.bcolz (30 files, 2.6 KB)
                        │   ├── __attrs__ (217.0 B)
                        │   ├── __rootdirs__ (67.0 B)
                        │   ├── close (4 files, 362.0 B)
                        │   │   ├── __attrs__ (3.0 B)
                        │   │   ├── data (1 files, 172.0 B)
                        │   │   │   └── __0.blp (172.0 B)
                        │   │   └── meta (2 files, 187.0 B)
                        │   │       ├── sizes (48.0 B)
                        │   │       └── storage (139.0 B)
                        │   ├── day (4 files, 368.0 B)
                        │   │   ├── __attrs__ (3.0 B)
                        │   │   ├── data (1 files, 178.0 B)
                        │   │   │   └── __0.blp (178.0 B)
                        │   │   └── meta (2 files, 187.0 B)
                        │   │       ├── sizes (48.0 B)
                        │   │       └── storage (139.0 B)
                        │   ├── high (4 files, 362.0 B)
                        │   │   ├── __attrs__ (3.0 B)
                        │   │   ├── data (1 files, 172.0 B)
                        │   │   │   └── __0.blp (172.0 B)
                        │   │   └── meta (2 files, 187.0 B)
                        │   │       ├── sizes (48.0 B)
                        │   │       └── storage (139.0 B)
                        │   ├── id (4 files, 241.0 B)
                        │   │   ├── __attrs__ (3.0 B)
                        │   │   ├── data (1 files, 51.0 B)
                        │   │   │   └── __0.blp (51.0 B)
                        │   │   └── meta (2 files, 187.0 B)
                        │   │       ├── sizes (48.0 B)
                        │   │       └── storage (139.0 B)
                        │   ├── low (4 files, 362.0 B)
                        │   │   ├── __attrs__ (3.0 B)
                        │   │   ├── data (1 files, 172.0 B)
                        │   │   │   └── __0.blp (172.0 B)
                        │   │   └── meta (2 files, 187.0 B)
                        │   │       ├── sizes (48.0 B)
                        │   │       └── storage (139.0 B)
                        │   ├── open (4 files, 362.0 B)
                        │   │   ├── __attrs__ (3.0 B)
                        │   │   ├── data (1 files, 172.0 B)
                        │   │   │   └── __0.blp (172.0 B)
                        │   │   └── meta (2 files, 187.0 B)
                        │   │       ├── sizes (48.0 B)
                        │   │       └── storage (139.0 B)
                        │   └── volume (4 files, 355.0 B)
                        │       ├── __attrs__ (3.0 B)
                        │       ├── data (1 files, 165.0 B)
                        │       │   └── __0.blp (165.0 B)
                        │       └── meta (2 files, 187.0 B)
                        │           ├── sizes (48.0 B)
                        │           └── storage (139.0 B)
                        └── minute_equities.bcolz (1 files, 172.0 B)
                            └── metadata.json (172.0 B)
```

## 详细文件信息

### short_second_strategy

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| .env.example | 671.0 B | 2025-08-27 17:52:13 | .example |
| README.md | 11.8 KB | 2025-08-23 22:03:47 | .md |
| create_init_files.py | 2.3 KB | 2025-08-27 17:17:39 | .py |
| dependency_scanner.py | 3.2 KB | 2025-08-27 17:56:56 | .py |
| example.html | 51.8 KB | 2025-08-20 17:25:03 | .html |
| package.json | 0.0 B | 2025-08-20 16:03:29 | .json |
| pip_freeze.txt | 1.5 KB | 2025-08-23 22:16:23 | .txt |
| project_structure_scanner.py | 15.0 KB | 2025-08-27 17:21:34 | .py |
| 工程进度.md | 26.8 KB | 2025-08-25 19:28:47 | .md |

### short_second_strategy/backend

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __init__.py | 24.0 B | 2025-08-27 17:03:55 | .py |
| app.py | 606.0 B | 2025-08-20 18:00:57 | .py |

### short_second_strategy/backend/analysis

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| capital_flow.py | 0.0 B | 2025-08-20 15:47:31 | .py |
| correlation.py | 0.0 B | 2025-08-20 15:47:45 | .py |
| sentiment.py | 0.0 B | 2025-08-20 15:47:37 | .py |
| technical.py | 640.0 B | 2025-08-20 20:04:47 | .py |

### short_second_strategy/backend/api

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| auth.py | 0.0 B | 2025-08-20 15:49:41 | .py |
| routes.py | 5.6 KB | 2025-08-22 23:12:48 | .py |
| websocket.py | 0.0 B | 2025-08-20 15:49:32 | .py |

### short_second_strategy/backend/backtest

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| engine.py | 0.0 B | 2025-08-20 15:48:38 | .py |
| metrics.py | 0.0 B | 2025-08-20 15:48:47 | .py |
| optimizer.py | 0.0 B | 2025-08-20 15:48:56 | .py |
| zipline_csv_bundle.py | 5.4 KB | 2025-08-23 20:03:28 | .py |
| zipline_export.py | 17.4 KB | 2025-08-26 18:36:36 | .py |
| zipline_integration.py | 1.5 KB | 2025-08-23 14:27:03 | .py |

### short_second_strategy/backend/config

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| settings.py | 243.0 B | 2025-08-20 18:00:04 | .py |
| thresholds.yaml | 5.5 KB | 2025-08-22 23:19:22 | .yaml |

### short_second_strategy/backend/core

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| backtester.py | 7.1 KB | 2025-08-22 22:59:17 | .py |
| entry_signals.py | 9.3 KB | 2025-08-22 16:23:24 | .py |
| executor.py | 0.0 B | 2025-08-20 15:45:21 | .py |
| indicators.py | 4.3 KB | 2025-08-23 14:19:46 | .py |
| macro_filter.py | 2.4 KB | 2025-08-20 18:00:19 | .py |
| risk_manager.py | 15.2 KB | 2025-08-22 15:30:53 | .py |
| sector_rotation.py | 3.0 KB | 2025-08-20 18:39:31 | .py |
| sentry.py | 3.9 KB | 2025-08-22 23:11:38 | .py |
| stock_selector.py | 6.6 KB | 2025-08-20 20:01:24 | .py |

### short_second_strategy/backend/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __init__.py | 24.0 B | 2025-08-27 17:03:55 | .py |
| cache.py | 4.5 KB | 2025-08-25 20:27:31 | .py |
| exceptions.py | 14.4 KB | 2025-08-26 19:04:20 | .py |
| fetcher copy.py | 11.3 KB | 2025-08-25 20:44:38 | .py |
| fetcher.py | 21.3 KB | 2025-08-26 20:01:02 | .py |
| merge.py | 11.1 KB | 2025-08-25 20:10:58 | .py |
| normalize.py | 16.7 KB | 2025-08-24 21:37:26 | .py |

### short_second_strategy/backend/data/providers

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __init__.py | 24.0 B | 2025-08-27 17:46:04 | .py |
| akshare_provider.py | 11.2 KB | 2025-08-27 17:43:55 | .py |
| base.py | 4.7 KB | 2025-08-26 18:43:29 | .py |
| csv_provider.py | 13.3 KB | 2025-08-27 17:07:47 | .py |
| tushare_provider.py | 11.6 KB | 2025-08-27 17:43:46 | .py |

### short_second_strategy/backend/tests

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| test_macro.py | 0.0 B | 2025-08-20 15:51:03 | .py |
| test_rotation.py | 0.0 B | 2025-08-20 15:51:18 | .py |
| test_signals.py | 0.0 B | 2025-08-20 15:51:27 | .py |

### short_second_strategy/backend/utils

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __init__.py | 0.0 B | 2025-08-20 15:50:04 | .py |
| helpers.py | 0.0 B | 2025-08-20 15:50:36 | .py |
| logger.py | 0.0 B | 2025-08-20 15:50:19 | .py |
| validators.py | 0.0 B | 2025-08-20 15:50:43 | .py |

### short_second_strategy/backend/zipline

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| algo_breakout_min.py | 5.7 KB | 2025-08-23 20:03:15 | .py |
| algo_sss_strategy.py | 5.2 KB | 2025-08-23 20:18:30 | .py |
| algo_sss_strategy_relaxed.py | 6.9 KB | 2025-08-23 20:28:23 | .py |

### short_second_strategy/config

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| data_providers.yaml | 347.0 B | 2025-08-27 17:08:00 | .yaml |
| development.env | 0.0 B | 2025-08-20 16:02:10 | .env |
| docker-compose.yml | 0.0 B | 2025-08-20 16:02:26 | .yml |
| logging.yaml | 4.5 KB | 2025-08-26 19:04:50 | .yaml |
| production.env | 0.0 B | 2025-08-20 16:02:04 | .env |
| security.yaml | 1.2 KB | 2025-08-27 17:52:59 | .yaml |
| thresholds.yaml | 157.0 B | 2025-08-22 23:20:15 | .yaml |

### short_second_strategy/data

### short_second_strategy/data/cache

### short_second_strategy/data/cache/ohlcv

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| ohlcv_akshare_000001.XSHE_2024-01-01_2024-01-31_1d.csv | 957.0 B | 2025-08-26 18:43:43 | .csv |
| ohlcv_akshare_000002.XSHE_2024-01-01_2024-01-31_1d.csv | 964.0 B | 2025-08-26 18:43:43 | .csv |
| ohlcv_akshare_002415.XSHE_2024-01-01_2024-01-31_1d.csv | 1.0 KB | 2025-08-26 18:43:43 | .csv |
| ohlcv_akshare_600000.XSHG_2024-01-01_2024-01-31_1d.csv | 943.0 B | 2025-08-26 18:43:44 | .csv |
| ohlcv_akshare_600519.XSHG_2024-01-01_2024-01-31_1d.csv | 1.2 KB | 2025-08-26 18:43:44 | .csv |
| ohlcv_csv_002415.XSHE_2024-01-02_2024-01-05_1d.csv | 191.0 B | 2025-08-27 17:47:03 | .csv |
| ohlcv_csv_002415.XSHE_2024-01-02_2024-01-10_1d.csv | 314.0 B | 2025-08-27 17:08:00 | .csv |
| ohlcv_csv_002415_2024-01-01_2024-01-05_1d.csv | 210.0 B | 2025-08-23 10:23:05 | .csv |

### short_second_strategy/data/export

### short_second_strategy/data/market

### short_second_strategy/data/ohlcv

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| 002415.csv | 193.0 B | 2025-08-23 10:23:05 | .csv |

### short_second_strategy/data/stocks

### short_second_strategy/data/zipline_csv

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| .gitkeep | 0.0 B | 2025-08-23 21:18:07 |  |
| 000001.csv | 1.1 KB | 2025-08-26 18:43:43 | .csv |
| 000002.csv | 1.1 KB | 2025-08-26 18:43:43 | .csv |
| 002415.csv | 303.0 B | 2025-08-27 17:08:00 | .csv |
| 600000.csv | 1.1 KB | 2025-08-26 18:43:44 | .csv |
| 600519.csv | 1.3 KB | 2025-08-26 18:43:44 | .csv |
| TEST.csv | 2.7 KB | 2025-08-23 20:03:47 | .csv |

### short_second_strategy/data/zipline_csv_out

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| 002415.csv | 317.0 B | 2025-08-27 17:08:00 | .csv |

### short_second_strategy/database

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| init.sql | 0.0 B | 2025-08-20 15:58:11 | .sql |
| schema.sql | 0.0 B | 2025-08-20 15:58:18 | .sql |

### short_second_strategy/database/migrations

### short_second_strategy/docs

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| api.md | 0.0 B | 2025-08-20 16:03:02 | .md |
| deployment.md | 0.0 B | 2025-08-20 16:03:10 | .md |
| strategy.md | 0.0 B | 2025-08-20 16:02:55 | .md |

### short_second_strategy/frontend

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| index.html | 0.0 B | 2025-08-20 15:54:27 | .html |

### short_second_strategy/frontend/assets

### short_second_strategy/frontend/assets/fonts

### short_second_strategy/frontend/assets/images

### short_second_strategy/frontend/css

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| components.css | 0.0 B | 2025-08-20 15:54:55 | .css |
| style.css | 0.0 B | 2025-08-20 15:54:48 | .css |

### short_second_strategy/frontend/js

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| app.js | 0.0 B | 2025-08-20 15:56:46 | .js |
| charts.js | 0.0 B | 2025-08-20 15:56:56 | .js |
| dashboard.js | 0.0 B | 2025-08-20 15:56:52 | .js |
| utils.js | 0.0 B | 2025-08-20 15:57:11 | .js |
| websocket.js | 0.0 B | 2025-08-20 15:57:05 | .js |

### short_second_strategy/scripts

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| backup.sh | 0.0 B | 2025-08-20 16:01:14 | .sh |
| deploy.sh | 0.0 B | 2025-08-20 16:01:08 | .sh |
| manage.sh | 25.5 KB | 2025-08-20 16:17:21 | .sh |
| monitor.py | 0.0 B | 2025-08-20 16:01:20 | .py |

### short_second_strategy/tests

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| debug_data.py | 2.6 KB | 2025-08-23 20:02:25 | .py |
| debug_sss.py | 8.0 KB | 2025-08-23 20:25:35 | .py |
| diagnostic.py | 10.7 KB | 2025-08-27 17:03:24 | .py |
| optimize_parallel.py | 17.9 KB | 2025-08-24 21:58:40 | .py |
| optimize_params.py | 14.1 KB | 2025-08-24 22:01:52 | .py |
| optimize_params_parallel_description.md | 4.1 KB | 2025-08-24 22:01:45 | .md |
| requirements_list.py | 3.2 KB | 2025-08-27 17:15:14 | .py |
| run_all_tests.py | 5.8 KB | 2025-08-22 16:15:26 | .py |
| run_backtest_demo.py | 899.0 B | 2025-08-22 22:44:43 | .py |
| run_cache_tests.py | 16.5 KB | 2025-08-25 20:33:11 | .py |
| run_data_tests.py | 2.9 KB | 2025-08-23 10:16:28 | .py |
| run_fetcher_step12_tests.py | 6.0 KB | 2025-08-26 20:06:34 | .py |
| run_indicator_tests.py | 4.0 KB | 2025-08-23 14:21:20 | .py |
| run_merge_tests.py | 6.3 KB | 2025-08-25 20:04:50 | .py |
| run_provider_akshare_smoke.py | 857.0 B | 2025-08-24 21:39:57 | .py |
| run_sentry_tests.py | 2.4 KB | 2025-08-22 23:13:25 | .py |
| run_sentry_yaml_tests.py | 3.9 KB | 2025-08-22 23:51:33 | .py |
| run_zipline_step1_check.py | 634.0 B | 2025-08-23 14:27:44 | .py |
| run_zipline_step2_bundle.py | 1.0 KB | 2025-08-23 14:43:45 | .py |
| run_zipline_step3_algo.py | 4.3 KB | 2025-08-23 19:57:41 | .py |
| run_zipline_step4_strategy.py | 3.7 KB | 2025-08-23 20:29:00 | .py |

### short_second_strategy/var

### short_second_strategy/var/zipline

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| extension.py | 527.0 B | 2025-08-23 20:29:14 | .py |
| min_algo_perf.pkl | 17.5 KB | 2025-08-23 20:03:53 | .pkl |
| sss_strategy_perf.pkl | 15.6 KB | 2025-08-23 20:29:15 | .pkl |

### short_second_strategy/var/zipline/data

### short_second_strategy/var/zipline/data/sss_csv

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| adjustments.sqlite | 84.0 KB | 2025-08-23 20:03:50 | .sqlite |
| assets-7.sqlite | 88.0 KB | 2025-08-23 20:03:49 | .sqlite |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 217.0 B | 2025-08-23 20:03:49 |  |
| __rootdirs__ | 67.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/close

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/close/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:03:49 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/close/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:49 |  |
| storage | 139.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/day

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/day/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 178.0 B | 2025-08-23 20:03:49 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/day/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:49 |  |
| storage | 139.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/high

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/high/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:03:49 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/high/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:49 |  |
| storage | 139.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/id

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/id/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 51.0 B | 2025-08-23 20:03:49 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/id/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:49 |  |
| storage | 139.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/low

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/low/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:03:49 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/low/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:49 |  |
| storage | 139.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/open

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/open/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:03:49 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/open/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:49 |  |
| storage | 139.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/volume

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/volume/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 165.0 B | 2025-08-23 20:03:49 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/daily_equities.bcolz/volume/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:49 |  |
| storage | 139.0 B | 2025-08-23 20:03:49 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;49.690233/minute_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| metadata.json | 172.0 B | 2025-08-23 20:03:49 | .json |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| adjustments.sqlite | 84.0 KB | 2025-08-23 20:03:52 | .sqlite |
| assets-7.sqlite | 88.0 KB | 2025-08-23 20:03:51 | .sqlite |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 217.0 B | 2025-08-23 20:03:51 |  |
| __rootdirs__ | 67.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/close

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/close/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:03:51 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/close/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:51 |  |
| storage | 139.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/day

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/day/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 178.0 B | 2025-08-23 20:03:51 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/day/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:51 |  |
| storage | 139.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/high

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/high/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:03:51 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/high/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:51 |  |
| storage | 139.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/id

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/id/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 51.0 B | 2025-08-23 20:03:51 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/id/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:51 |  |
| storage | 139.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/low

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/low/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:03:51 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/low/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:51 |  |
| storage | 139.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/open

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/open/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:03:51 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/open/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:51 |  |
| storage | 139.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/volume

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/volume/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 165.0 B | 2025-08-23 20:03:51 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/daily_equities.bcolz/volume/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:03:51 |  |
| storage | 139.0 B | 2025-08-23 20:03:51 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;03;51.743590/minute_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| metadata.json | 172.0 B | 2025-08-23 20:03:51 | .json |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| adjustments.sqlite | 84.0 KB | 2025-08-23 20:13:41 | .sqlite |
| assets-7.sqlite | 88.0 KB | 2025-08-23 20:13:41 | .sqlite |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 217.0 B | 2025-08-23 20:13:41 |  |
| __rootdirs__ | 67.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/close

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/close/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:13:41 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/close/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:13:41 |  |
| storage | 139.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/day

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/day/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 178.0 B | 2025-08-23 20:13:41 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/day/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:13:41 |  |
| storage | 139.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/high

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/high/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:13:41 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/high/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:13:41 |  |
| storage | 139.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/id

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/id/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 51.0 B | 2025-08-23 20:13:41 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/id/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:13:41 |  |
| storage | 139.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/low

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/low/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:13:41 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/low/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:13:41 |  |
| storage | 139.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/open

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/open/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:13:41 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/open/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:13:41 |  |
| storage | 139.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/volume

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/volume/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 165.0 B | 2025-08-23 20:13:41 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/daily_equities.bcolz/volume/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:13:41 |  |
| storage | 139.0 B | 2025-08-23 20:13:41 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;13;41.242635/minute_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| metadata.json | 172.0 B | 2025-08-23 20:13:41 | .json |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| adjustments.sqlite | 84.0 KB | 2025-08-23 20:19:01 | .sqlite |
| assets-7.sqlite | 88.0 KB | 2025-08-23 20:19:01 | .sqlite |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 217.0 B | 2025-08-23 20:19:01 |  |
| __rootdirs__ | 67.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/close

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/close/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:19:01 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/close/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:19:01 |  |
| storage | 139.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/day

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/day/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 178.0 B | 2025-08-23 20:19:01 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/day/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:19:01 |  |
| storage | 139.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/high

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/high/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:19:01 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/high/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:19:01 |  |
| storage | 139.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/id

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/id/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 51.0 B | 2025-08-23 20:19:01 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/id/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:19:01 |  |
| storage | 139.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/low

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/low/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:19:01 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/low/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:19:01 |  |
| storage | 139.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/open

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/open/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:19:01 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/open/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:19:01 |  |
| storage | 139.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/volume

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/volume/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 165.0 B | 2025-08-23 20:19:01 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/daily_equities.bcolz/volume/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:19:01 |  |
| storage | 139.0 B | 2025-08-23 20:19:01 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;19;01.144144/minute_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| metadata.json | 172.0 B | 2025-08-23 20:19:01 | .json |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| adjustments.sqlite | 84.0 KB | 2025-08-23 20:29:13 | .sqlite |
| assets-7.sqlite | 88.0 KB | 2025-08-23 20:29:13 | .sqlite |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 217.0 B | 2025-08-23 20:29:13 |  |
| __rootdirs__ | 67.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/close

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/close/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:29:13 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/close/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:29:13 |  |
| storage | 139.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/day

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/day/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 178.0 B | 2025-08-23 20:29:13 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/day/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:29:13 |  |
| storage | 139.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/high

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/high/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:29:13 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/high/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:29:13 |  |
| storage | 139.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/id

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/id/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 51.0 B | 2025-08-23 20:29:13 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/id/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:29:13 |  |
| storage | 139.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/low

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/low/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:29:13 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/low/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:29:13 |  |
| storage | 139.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/open

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/open/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 172.0 B | 2025-08-23 20:29:13 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/open/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:29:13 |  |
| storage | 139.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/volume

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __attrs__ | 3.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/volume/data

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| __0.blp | 165.0 B | 2025-08-23 20:29:13 | .blp |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/daily_equities.bcolz/volume/meta

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| sizes | 48.0 B | 2025-08-23 20:29:13 |  |
| storage | 139.0 B | 2025-08-23 20:29:13 |  |

### short_second_strategy/var/zipline/data/sss_csv/2025-08-23T12;29;12.987217/minute_equities.bcolz

| 文件名 | 大小 | 修改时间 | 类型 |
|--------|------|----------|------|
| metadata.json | 172.0 B | 2025-08-23 20:29:13 | .json |


## Python文件分析

| 文件路径 | 行数 | 类 | 函数 | 主要功能 |
|----------|------|----|----- |---------|
| ./create_init_files.py | 90 | 0 | 1 | 创建项目中缺失的__init__.py文件 |
| ./dependency_scanner.py | 96 | 0 | 4 | 依赖扫描脚本 - 输出当前Python环境的依赖信息 |
| ./project_structure_scanner.py | 398 | 1 | 13 | 项目结构扫描脚本 - 生成详细的项目文档 |
| backend/__init__.py | 2 | 0 | 0 | - |
| backend/app.py | 24 | 0 | 2 | - |
| backend/analysis/capital_flow.py | 1 | 0 | 0 | - |
| backend/analysis/correlation.py | 1 | 0 | 0 | - |
| backend/analysis/sentiment.py | 1 | 0 | 0 | - |
| backend/analysis/technical.py | 22 | 0 | 3 | df 需含: high, low, close |
| backend/api/auth.py | 1 | 0 | 0 | - |
| backend/api/routes.py | 178 | 0 | 14 | - |
| backend/api/websocket.py | 1 | 0 | 0 | - |
| backend/backtest/engine.py | 1 | 0 | 0 | - |
| backend/backtest/metrics.py | 1 | 0 | 0 | - |
| backend/backtest/optimizer.py | 1 | 0 | 0 | - |
| backend/backtest/zipline_csv_bundle.py | 151 | 0 | 5 | 注册 Zipline-Reloaded 的 CSV Bundle，并生成示例 CSV。 |
| backend/backtest/zipline_export.py | 510 | 1 | 8 | Zipline CSV导出模块 |
| backend/backtest/zipline_integration.py | 47 | 0 | 2 | 中文说明： |
| backend/config/settings.py | 9 | 0 | 1 | - |
| backend/core/backtester.py | 186 | 1 | 3 | 最小回测器（单标的、单策略、固定止盈/止损） |
| backend/core/entry_signals.py | 234 | 0 | 4 | 买点与分时硬校验（四类）：breakout \| pullback \| reversal \| foll... |
| backend/core/executor.py | 1 | 0 | 0 | - |
| backend/core/indicators.py | 146 | 0 | 11 | 统一的技术指标库（第12步） |
| backend/core/macro_filter.py | 73 | 1 | 2 | - |
| backend/core/risk_manager.py | 358 | 1 | 11 | - |
| backend/core/sector_rotation.py | 79 | 1 | 2 | - |
| backend/core/sentry.py | 104 | 1 | 5 | MarketSentry：盘中/盘前“停手/熔断”哨兵。 |
| backend/core/stock_selector.py | 155 | 1 | 3 | 一线龙头确认（只实现“first-line”，二线筛选在下一步）。 |
| backend/data/__init__.py | 2 | 0 | 0 | - |
| backend/data/cache.py | 148 | 0 | 10 | 简单文件缓存（CSV 版） |
| backend/data/exceptions.py | 493 | 11 | 27 | 数据源异常和错误处理 |
| backend/data/fetcher copy.py | 273 | 1 | 19 | 数据适配层：本阶段仅提供可离线运行的 Stub，后续再接 AkShare/TuShare/券商SDK... |
| backend/data/fetcher.py | 539 | 2 | 14 | 统一数据入口（fetcher） |
| backend/data/merge.py | 302 | 0 | 2 | 多源合并与回退（merge） |
| backend/data/normalize.py | 439 | 0 | 11 | 代码规范映射（normalize.symbol） |
| backend/data/providers/__init__.py | 2 | 0 | 0 | - |
| backend/data/providers/akshare_provider.py | 354 | 1 | 11 | AkShare 数据提供器 - 增强版 |
| backend/data/providers/base.py | 152 | 4 | 4 | 可插拔行情数据提供器的基础定义（统一接口与返回格式） |
| backend/data/providers/csv_provider.py | 328 | 1 | 9 | CSV / Stub 适配器 |
| backend/data/providers/tushare_provider.py | 332 | 1 | 10 | TuShare 适配器 - 修复版本 |
| backend/tests/test_macro.py | 1 | 0 | 0 | - |
| backend/tests/test_rotation.py | 1 | 0 | 0 | - |
| backend/tests/test_signals.py | 1 | 0 | 0 | - |
| backend/utils/__init__.py | 1 | 0 | 0 | - |
| backend/utils/helpers.py | 1 | 0 | 0 | - |
| backend/utils/logger.py | 1 | 0 | 0 | - |
| backend/utils/validators.py | 1 | 0 | 0 | - |
| backend/zipline/algo_breakout_min.py | 171 | 0 | 3 | 最小可用：20日高点突破 + 简单RR风控 + 时间止盈/止损 |
| backend/zipline/algo_sss_strategy.py | 161 | 0 | 4 | - |
| backend/zipline/algo_sss_strategy_relaxed.py | 209 | 0 | 5 | 放宽条件版本的SSS策略 - 用于测试交易系统是否正常工作 |
| scripts/monitor.py | 1 | 0 | 0 | - |
| tests/debug_data.py | 69 | 0 | 0 | 调试脚本：检查CSV数据并分析为什么没有触发交易 |
| tests/debug_sss.py | 252 | 0 | 5 | 诊断脚本：测试 SSS 策略的信号评估和风控条件 |
| tests/diagnostic.py | 335 | 0 | 9 | 问题诊断脚本 - 逐步排查 fetcher 测试失败的原因 |
| tests/optimize_parallel.py | 542 | 0 | 12 | 并行参数优化脚本 - 使用多进程加速参数搜索 |
| tests/optimize_params.py | 434 | 0 | 11 | 串行参数优化脚本：通过网格搜索找到最佳的策略参数组合 |
| tests/requirements_list.py | 96 | 0 | 4 | 依赖扫描脚本 - 输出当前Python环境的依赖信息 |
| tests/run_all_tests.py | 154 | 0 | 3 | 一次性测试脚本（函数级 + 接口级） |
| tests/run_backtest_demo.py | 24 | 0 | 1 | - |
| tests/run_cache_tests.py | 470 | 0 | 13 | 增强版缓存模块测试脚本 |
| tests/run_data_tests.py | 87 | 0 | 5 | 第 11 步 自测脚本： |
| tests/run_fetcher_step12_tests.py | 182 | 0 | 6 | 第12步：统一入口（fetcher）测试脚本 |
| tests/run_indicator_tests.py | 127 | 0 | 4 | 第12步：指标库自测脚本 |
| tests/run_merge_tests.py | 184 | 0 | 2 | 多源合并与回退 自测脚本 - 完全修正版 |
| tests/run_provider_akshare_smoke.py | 23 | 0 | 0 | - |
| tests/run_sentry_tests.py | 92 | 0 | 4 | Sentry 自测：离线 + 在线 |
| tests/run_sentry_yaml_tests.py | 123 | 0 | 5 | 验证：sentry 阈值从 config/thresholds.yaml 读取并生效 |
| tests/run_zipline_step1_check.py | 21 | 0 | 1 | - |
| tests/run_zipline_step2_bundle.py | 37 | 0 | 1 | Step 13-2：CSV Bundle 注册与 ingest 自测 |
| tests/run_zipline_step3_algo.py | 129 | 0 | 2 | step 13-3：运行最小 Zipline 算法，并验证： |
| tests/run_zipline_step4_strategy.py | 106 | 0 | 2 | step 13-4：运行"策略 + 风控"接入后的 Zipline 算法 |
| var/zipline/extension.py | 13 | 0 | 0 | - |

### 主要依赖分析

| 包名 | 使用次数 |
|------|----------|
| backend | 81 |
| pandas | 36 |
| zipline | 21 |
| numpy | 17 |
| __future__ | 15 |
| json | 10 |
|  | 7 |
| datetime | 5 |
| exchange_calendars | 5 |
| traceback | 5 |
