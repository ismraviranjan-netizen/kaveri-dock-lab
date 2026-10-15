@echo off
REM Run every Domain 3 exhibit on battery (DRY_RUN=1).  Windows version. E1 and E9 need:  pip install fastmcp
cd /d "%~dp0"
set DRY_RUN=1
for %%f in (e1_connector.py e2_bloat_audit.py e3_gate_pass.py e4_chunking.py e5_hybrid.py e6_shape_router.py e7_dock_cameras.py e8_two_bills.py e9_one_ticket.py) do (
  echo ################ %%f ################
  python %%f
  echo.
)
set DRY_RUN=
