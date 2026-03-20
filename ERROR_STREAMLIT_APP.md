# 🔧 SOLUCIÓN RÁPIDA: Error "streamlit_app.py does not exist"

## ⚠️ El Problema

Cuando intentas desplegar en Streamlit Cloud, ves este error:

```
Main file path: streamlit_app.py
This file does not exist
```

## ✅ La Solución

### Opción 1: CAMBIAR el campo (Recomendado)

1. En Streamlit Cloud → "New app"
2. En el campo **"Main file path"**, **BORRA** lo que dice
3. **ESCRIBE MANUALMENTE**: `app.py`
4. Click en **"Deploy"**

**¡Eso es todo!** Streamlit Cloud busca `app.py` que SÍ existe.

---

### Opción 2: SI YA INTENTASTE y Sigue Error

1. Primero verifica que el archivo existe localmente:
   ```bash
   ls -la app.py
   # Debe mostrar: -rw-r--r-- ... app.py
   ```

2. Si existe, pero Streamlit Cloud no lo ve:
   - Ir a Streamlit Cloud
   - Eliminar la app (Settings → Advanced → Delete the app)
   - Ir a `github.com` y hacer refresh del repo
   - Intentar nuevamente con `app.py`

---

### Opción 3: SI AÚN NO FUNCIONA

Crear un archivo `streamlit_app.py` que sea alias de `app.py`:

```python
# streamlit_app.py
import subprocess
import sys

# Ejecutar app.py
exec(open('app.py').read())
```

Luego en Streamlit Cloud poner: `streamlit_app.py`

(Pero esto no debería ser necesario - **la Opción 1 debe funcionar**)

---

## 📋 Checklist del Deployment

- [ ] Repository: `tu-usuario/freightmetrics-mvp`
- [ ] Branch: `main`
- [ ] Main file path: **`app.py`** ← Verificar esto
- [ ] Secrets configurados en Settings
- [ ] Click "Deploy"
- [ ] Esperar 2-3 minutos

---

## 🆘 Si NADA funciona

1. Verificar que el archivo `app.py` existe en la raíz:
   ```bash
   pwd
   # Debe mostrar: .../freightmetrics_mvp
   
   ls app.py
   # Debe mostrar: app.py
   ```

2. Verificar que el repo está en GitHub:
   ```bash
   git remote -v
   # Debe mostrar origin apuntando a GitHub
   
   git log | head -1
   # Debe mostrar tu último commit
   ```

3. Si todo está bien:
   - Eliminar la app en Streamlit Cloud
   - Desconectar GitHub
   - Reconectar GitHub
   - Intentar nuevamente

---

**Solución habitual: Simplemente escribe `app.py` en lugar de `streamlit_app.py` ✅**
