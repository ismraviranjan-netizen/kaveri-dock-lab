@echo off
REM Run every Domain 1 exhibit on battery (DRY_RUN=1), then E7 under each stop_reason scenario.  Windows version.
cd /d "%~dp0"
set DRY_RUN=1
for %%f in (e1_augmented_llm.py e2_chaining.py e3_routing.py e4_parallel.py e5_orchestrator_workers.py e6_evaluator_optimizer.py e7_agent_loop.py e8_replanning.py) do (
  echo ################ %%f ################
  python %%f
  echo.
)
for %%s in (truncate refuse exhaust) do (
  echo ################ e7_agent_loop.py  D1_SCENARIO=%%s ################
  set D1_SCENARIO=%%s
  python e7_agent_loop.py
  echo.
)
set DRY_RUN=
set D1_SCENARIO=
