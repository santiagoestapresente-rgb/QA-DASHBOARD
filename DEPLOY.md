# Despliegue en Streamlit Community Cloud

Guía para publicar el **DiDi CX Quality Dashboard** y obtener un enlace interactivo
compartible, manteniendo el diseño ejecutivo actual.

> **Confidencialidad:** el Business Case está marcado como confidencial y no debe
> compartirse fuera del proceso de selección. Por eso esta guía exige
> **repositorio privado** y **acceso restringido por correo** en la app.
>
> ⚠️ **Acción urgente antes de desplegar:** el repo remoto que ya existe
> (`santiagoestapresente-rgb/QA-DASHBOARD`) está **público** y contiene el Excel del
> Business Case. Ponlo en privado siguiendo el **paso 1**.

---

## 0. Qué está ya resuelto

- Los datos viajan **dentro del repositorio** en `data/packaged/` (9 archivos parquet,
  0,8 MB en total). La app no depende de ninguna ruta de tu PC.
- `requirements.txt` tiene las versiones fijadas y solo las librerías de runtime.
- `.streamlit/config.toml` tiene el tema de marca DiDi y opciones de producción.
  No contiene secretos ni rutas locales.
- El caché local (`data/cache/`, ~34 MB) está en `.gitignore`: no se sube y no se
  necesita en la nube.

Antes de subir, puedes revalidar todo con:

```bat
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe scripts\smoke_test_deploy.py
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe scripts\smoke_test_app.py
```

El primero debe terminar en `SMOKE TEST PASSED` con los tres totales de control:
QA Score **94,14** · CSAT Score **79,95** · Recontact Rate **5,83**.
El segundo ejecuta `app.py` completo (sin navegador) y debe terminar en
`APP SMOKE TEST PASSED`.

---

## 1. ⚠️ Primero: poner en privado el repositorio que ya existe

Este proyecto **ya tiene un remoto configurado y ya se subió a GitHub**:

```
origin  https://github.com/santiagoestapresente-rgb/QA-DASHBOARD.git
```

Ese repositorio está actualmente **PÚBLICO**, y el push incluyó
`data/Business Case.xlsx`. Es decir, **los datos confidenciales del Business Case son
hoy accesibles por cualquiera**. Antes de seguir con el despliegue, arréglalo:

1. Entra a <https://github.com/santiagoestapresente-rgb/QA-DASHBOARD/settings>.
2. Baja hasta **Danger Zone** → **Change repository visibility** →
   **Make private** → confirma escribiendo el nombre del repo.
3. Alternativa más drástica si prefieres empezar de cero: **Delete this repository** y
   crear uno nuevo privado (ver paso 1-bis).

Comprueba que quedó privado abriendo el enlace en una ventana de incógnito: debe dar
**404**. (En el momento de escribir esto no había forks del repo, así que pasarlo a
privado corta el acceso de forma efectiva.)

### 1-bis. Si prefieres crear un repositorio nuevo

1. Entra a <https://github.com/new>.
2. **Repository name:** `didi-cx-quality-dashboard`.
3. **Visibility: Private.** ← Streamlit Community Cloud despliega repos privados sin
   problema y es lo que protege el Business Case.
4. **No** marques "Add a README file" ni `.gitignore` ni licencia (el repo local ya los
   tiene y generaría conflicto al hacer push).
5. **Create repository** y copia la URL.
6. Reapunta el remoto local:

```powershell
cd C:\Users\PC\Documents\DIDI
git remote set-url origin https://github.com/TU_USUARIO/didi-cx-quality-dashboard.git
```

---

## 2. Subir los cambios

El repositorio local ya existe en `C:\Users\PC\Documents\DIDI`, está en la rama `main` y
sigue a `origin/main`. Abre PowerShell en la carpeta del proyecto:

```powershell
cd C:\Users\PC\Documents\DIDI

# 1) Revisa qué se va a subir antes de confirmar nada
git status

# 2) Añade los cambios y crea el commit
git add .
git commit -m "Dashboard listo para desplegar: datos empaquetados en parquet"

# 3) Sube a la rama main
git push -u origin main
```

Notas:

- Git pedirá autenticación. Lo más simple es instalar
  [GitHub CLI](https://cli.github.com/) y ejecutar `gh auth login`, o usar un
  **Personal Access Token** como contraseña (Settings → Developer settings →
  Personal access tokens → Fine-grained token con permiso `Contents: Read and write`).
- Verifica en GitHub que exista la carpeta `data/packaged/` con los 9 `.parquet`.
  Si no está, la app fallará en la nube.
- `git add .` sube también los entregables (`entregable 2/`, `powerbi/`) y el Excel
  fuente. El repo queda en unos 21 MB, muy por debajo de los límites de GitHub, y el
  dashboard solo necesita `data/packaged/`. Si prefieres un repo mínimo, sube solo
  `app.py`, `config.py`, `modules/`, `scripts/`, `requirements.txt`, `.streamlit/` y
  `data/packaged/`.

---

## 3. Desplegar en Streamlit Community Cloud

1. Entra a <https://share.streamlit.io> e inicia sesión con **Continue with GitHub**.
2. Autoriza a Streamlit. Para repositorios **privados** debes conceder el permiso extra
   de acceso a repos privados que solicita la app de GitHub; si no aparece tu repo en la
   lista, usa el enlace *"If you don't see your repo, click here"* y concede el acceso.
3. Pulsa **Create app** → opción de desplegar desde GitHub.
4. Rellena el formulario:
   - **Repository:** tu repo privado (p. ej. `santiagoestapresente-rgb/QA-DASHBOARD`,
     ya en privado tras el paso 1)
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** elige un subdominio, p. ej. `didi-cx-quality`
5. Abre **Advanced settings** y selecciona **Python 3.11**.
   Esto es importante: las versiones de `requirements.txt` están fijadas y verificadas
   en Python 3.11. Streamlit Cloud **ignora** `runtime.txt` y `.python-version`; el
   desplegable de *Advanced settings* es el único mecanismo válido.
   Deja **Secrets** vacío: la app no usa secretos.
6. Pulsa **Deploy**. La primera compilación tarda 2–5 minutos (instala dependencias).
   Verás los logs en vivo; al terminar se abre el dashboard.

Tu enlace queda como `https://didi-cx-quality.streamlit.app`.

---

## 4. Restringir quién puede ver la app (confidencialidad)

Esta es la parte clave por la confidencialidad del Business Case.

**Regla de Streamlit Community Cloud:** una app desplegada desde un **repositorio
privado** nace **privada**. Solo la ven quienes tienen permiso de push/admin en el repo
de GitHub (es decir, tú). Cualquier otra persona que abra el enlace ve una pantalla de
"no tienes acceso", incluso teniendo la URL. Si en cambio despliegas desde un repo
público, la app es pública para todo internet — **motivo por el que el paso 1 insiste en
repo privado**.

Para dar acceso a las personas del proceso de selección:

1. En <https://share.streamlit.io>, localiza la app en tu lista.
2. Menú **⋮** (tres puntos) → **Settings** → pestaña **Sharing**
   (también accesible desde la propia app: **Manage app** → **Settings** → **Sharing**).
3. En **Invite viewers by email**, añade los correos autorizados separados por coma
   (los de la entrevistadora / el equipo de CX Quality) y guarda.
4. Streamlit envía a cada persona un email con el enlace. Para entrar deben
   autenticarse: con **Google OAuth** si el correo es una cuenta Google, o con un
   **enlace de un solo uso** que reciben por email (válido 15 minutos).

Cuidados importantes:

- En esa misma pestaña **Sharing** existe la opción de hacer la app pública
  ("anyone with the link"). **No la actives**: eso expondría el Business Case a
  cualquiera con la URL.
- Límite de 100 viewers por app.
- Los viewers invitados también pueden ver analytics del workspace e invitar a otros;
  invita solo a quien realmente lo necesite.
- Cuando termine el proceso, quita los correos de la lista o borra la app
  (**⋮ → Delete app**).

---

## 5. Actualizar la app después

No hace falta volver a desplegar. Streamlit Cloud escucha la rama conectada:

```powershell
cd C:\Users\PC\Documents\DIDI
git add .
git commit -m "Ajuste en el dashboard"
git push
```

En 1–2 minutos la app se reconstruye sola. Si cambiaste `requirements.txt`, reinstala
dependencias (tarda algo más).

Si modificas el Excel fuente (`data/Business Case.xlsx`), **regenera el snapshot antes
de hacer push**, o la nube seguirá mostrando los datos viejos:

```bat
C:\Users\PC\AppData\Local\Programs\Python\Python311\python.exe scripts\build_data_artifact.py
```

---

## 6. Si el despliegue falla

**Dónde ver los logs:** en la app desplegada, abajo a la derecha, **Manage app** →
panel de logs. Desde el dashboard de <https://share.streamlit.io> también tienes
**⋮ → Logs**. Para reintentar: **⋮ → Reboot app**.

Errores más comunes:

| Síntoma en los logs | Causa | Solución |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'plotly'` (o pandas, pyarrow…) | Falta la librería en `requirements.txt` | Añádela con versión fijada, commit y push |
| `No matching distribution found for pandas==3.0.3` | La nube usó otra versión de Python (suele forzar 3.13/3.14) | Borra la app y vuelve a desplegar seleccionando **Python 3.11** en *Advanced settings*. Si persiste, relaja los pines a `>=` en `requirements.txt` |
| `FileNotFoundError: ... data/packaged` o el mensaje "Business Case data could not be loaded" | El snapshot parquet no llegó al repo | Comprueba en GitHub que `data/packaged/*.parquet` existe; revisa que `.gitignore` no lo excluya y vuelve a hacer `git add data/packaged` |
| `Error installing requirements` con paquetes raros | Se colaron dependencias que solo usan los scripts (`python-docx`, `matplotlib`, `reportlab`…) | Mantén `requirements.txt` solo con las 6 librerías de runtime |
| La app arranca pero se queda en blanco o "Please wait…" | Memoria agotada (límite ~1 GB en el tier gratuito) | **Reboot app**; el snapshot parquet ya minimiza el consumo |
| `App is over its resource limits` | Pico de memoria/CPU | **Reboot app** y evita abrir muchas pestañas simultáneas |

**Para depurar con detalle:** `.streamlit/config.toml` tiene
`showErrorDetails = "none"` para que un visitante ejecutivo no vea trazas. Si necesitas
ver el error completo en pantalla, cámbialo temporalmente a `"full"`, haz push, depura
y vuelve a dejarlo en `"none"`.

---

## 7. Límites del tier gratuito que conviene saber

- **La app se duerme** tras varios días sin visitas (y puede hibernar antes por
  inactividad). Al abrir el enlace tarda entre unos segundos y ~1 minuto en despertar;
  aparece un botón *"Yes, get this app back up!"*. Abre el enlace **antes** de
  compartirlo en una entrevista para que ya esté caliente.
- **Recursos:** ~1 GB de RAM y CPU compartida por app. Este dashboard es ligero
  (parquet de 0,8 MB, ~93 mil filas en memoria), pero evita muchos usuarios simultáneos.
- **Sistema de archivos efímero:** cualquier archivo que la app escriba se pierde al
  reiniciar. La carga de datos ya está diseñada para no depender de escrituras.
- **Cuota:** solo **1 app privada a la vez** por workspace (las públicas son
  ilimitadas). Si ya tienes otra app privada desplegada, tendrás que borrarla o hacerla
  pública antes de desplegar esta. Borrar el repo en GitHub no libera la cuota: hay que
  borrar la app en share.streamlit.io.
- El enlace `*.streamlit.app` existe como URL, pero la protección real es la
  autenticación: repo privado + lista de correos autorizados del paso 4.
- **Cambiar la versión de Python después no se puede** en una app ya desplegada: hay que
  borrarla y volver a desplegar eligiendo la versión en *Advanced settings*.
