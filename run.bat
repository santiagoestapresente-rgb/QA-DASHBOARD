@echo off
cd /d "%~dp0"
set PY="C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe"

echo Verificando datos...
%PY% -c "from modules.data_loader import has_packaged_snapshot; print('Snapshot parquet listo.' if has_packaged_snapshot() else 'Sin snapshot: se reconstruira desde el Excel (mas lento).')"

echo Iniciando dashboard...
%PY% -m streamlit run app.py
