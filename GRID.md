# Grid

**Link oficial (privado):** https://grid.adminml.com/d/01M0DX2E5NHW6Y69E36P8B0Q0V/view
**doc_id:** `01M0DX2E5NHW6Y69E36P8B0Q0V`

## Gerar e subir nova versão
```bash
python generate_grid_dashboard.py           # gera gs_chuveirinho_grid.html (produção)
python generate_grid_dashboard.py --local   # gera versão de teste local (Plotly via CDN)
```

Depois de regenerar, subir via skill `grid-sharing`:
```bash
curl -s -X POST "https://grid.melioffice.com/api/v1/engine/run" \
  -F 'config={"skill_version":"3.6.6","doc_id":"01M0DX2E5NHW6Y69E36P8B0Q0V","file_new_version":true}' \
  -F "file=@gs_chuveirinho_grid.html"
```
