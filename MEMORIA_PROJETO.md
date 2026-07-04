# Memoria do Projeto - Album Copa 2026

## Objetivo

Aplicacao estatica/PWA para Bernardo controlar o album fisico da Copa 2026 no tablet, com imagens locais das figurinhas, marcacao de tenho/falta/repetidas, controle visual e publicacao via GitHub Pages.

## Arquivos ativos

- `album_copa_2026_premium_imagens_externas.html`: app principal. Alteracoes de interface e dados ficam aqui.
- `index.html`: entrada do GitHub Pages, redireciona para o HTML principal.
- `figurinhas/`: imagens das figurinhas em `COD_00.webp`.
- `bandeiras/`: bandeiras locais em SVG.
- `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png`: PWA/cache.
- `start_tablet_server.py`: servidor local opcional.
- `.nojekyll`: necessario para GitHub Pages servir arquivos estaticos sem Jekyll.

## Regras importantes

- Nao trocar imagens ja corrigidas pelo usuario, especialmente FWC e CC, sem pedido explicito.
- O padrao de imagem e sempre `figurinhas/COD_00.webp`, por exemplo `BRA_01.webp`, `FWC_12.webp`, `CC_04.webp`.
- Antes de mexer em HTML importante, criar backup local `backup_album_copa_2026_premium_imagens_externas_YYYYMMDD_HHMMSS.html`.
- Alteracoes de runtime devem ficar no HTML, imagens, bandeiras, manifest ou service worker.
- Ao mudar comportamento visual/cache, atualizar `CACHE_NAME` em `sw.js` quando fizer sentido.
- O progresso do album fica no `localStorage` do navegador. Para levar entre aparelhos, usar backup/importacao JSON do app.

## GitHub Pages

Repositorio: `https://github.com/brendofm-sketch/Album_Bernardo.git`

URL publica:

```text
https://brendofm-sketch.github.io/Album_Bernardo/
```

Branch publicada: `main`, pasta `/root`.

Se o GitHub Pages ficar preso em `building`, chamar a API de builds ou enviar um commit vazio costuma destravar:

```powershell
git commit --allow-empty -m "Republica ajustes"
git push
```

Depois validar o HTML remoto com cache busting:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://brendofm-sketch.github.io/Album_Bernardo/album_copa_2026_premium_imagens_externas.html?nocache=$(Get-Date -Format yyyyMMddHHmmss)"
```

## Estado das figurinhas especiais

- `FWC_00.webp` a `FWC_19.webp`: imagens ajustadas pelo usuario. Nao reorganizar imagens.
- A lista de nomes FWC no HTML deve seguir a ordem atual das imagens:
  - `FWC_00`: Pagina inicial
  - `FWC_01`: Trofeu FIFA World Cup 26
  - `FWC_02`: Card Panini FIFA World Cup 2026
  - `FWC_03`: Maple, Zayu e Clutch
  - `FWC_04`: Logo FIFA World Cup 26
  - `FWC_05`: Bola oficial Trionda
  - `FWC_06`: Emblema vermelho FIFA World Cup 2026
  - `FWC_07`: Emblema verde FIFA World Cup 2026
  - `FWC_08`: Emblema azul FIFA World Cup 2026
  - `FWC_09`: Italia 1934
  - `FWC_10`: Uruguai 1950
  - `FWC_11`: Alemanha Ocidental 1954
  - `FWC_12`: Brasil 1962
  - `FWC_13`: Alemanha Ocidental 1974
  - `FWC_14`: Argentina 1986
  - `FWC_15`: Brasil 1994
  - `FWC_16`: Brasil 2002
  - `FWC_17`: Italia 2006
  - `FWC_18`: Alemanha 2014
  - `FWC_19`: Argentina 2022
- CC esta com nomes alinhados conforme ordem corrigida pelo usuario.

## Pasta Obsoleto

`Obsoleto/` guarda material que nao e necessario para rodar o app:

- PDFs originais e recortes de extracao.
- Scripts antigos de geracao/extracao/busca.
- Backups HTML.
- Auditorias, referencias e relatorios antigos.

Essa pasta fica no `.gitignore` para nao subir arquivos pesados ao GitHub.

## Fluxo recomendado para proximas etapas

1. Ler esta memoria.
2. Rodar `git status --short`.
3. Mexer apenas nos arquivos ativos necessarios.
4. Validar sintaxe do JS embutido quando alterar o HTML.
5. Commitar e dar push.
6. Confirmar que o GitHub Pages serviu a versao nova.
