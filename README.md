# Robô de publicação · @nudge.saude

Publica sozinho no Instagram o que está em `agenda.json`, no horário marcado (GitHub Actions, a cada 20 min).
As imagens e vídeos ficam em `midia/` e são servidos pelo GitHub Pages para a Meta buscar.

- Montar a semana: `python montar_agenda.py` (no computador, a partir da pasta publicacoes) e depois enviar ao GitHub.
- Conferir: `python publicar.py --conferir`
- O que já saiu fica em `publicados.json`.
