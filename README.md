# Smart Voice Remote Control

Servicio local para controlar Kodi mediante notas de voz recibidas por Telegram.

## Desarrollo

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/pytest
```

La configuración se cargará desde `.env`. La implementación no utiliza automatización gráfica: el control de Kodi se realizará mediante JSON-RPC HTTP.

El reconocimiento de voz se ejecuta localmente con `faster-whisper` usando únicamente los modelos `tiny` o `base`.
La extracción de intenciones se delega a Groq mediante `GROQ_API_KEY` y `GROQ_MODEL`; no se necesita Ollama.