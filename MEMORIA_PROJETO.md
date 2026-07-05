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
- `supabase/schema.sql`: estrutura inicial do banco para login, sincronizacao e comparacao de trocas.

## Regras importantes

- Nao trocar imagens ja corrigidas pelo usuario, especialmente FWC e CC, sem pedido explicito.
- O padrao de imagem e sempre `figurinhas/COD_00.webp`, por exemplo `BRA_01.webp`, `FWC_12.webp`, `CC_04.webp`.
- Antes de mexer em HTML importante, criar backup local `backup_album_copa_2026_premium_imagens_externas_YYYYMMDD_HHMMSS.html`.
- Alteracoes de runtime devem ficar no HTML, imagens, bandeiras, manifest ou service worker.
- Ao mudar comportamento visual/cache, atualizar `CACHE_NAME` em `sw.js` quando fizer sentido.
- O progresso do album fica primeiro no `localStorage` do navegador. A versao `supabase-dev` sincroniza com Supabase depois de login, mesclando as maiores quantidades por figurinha.
- Nunca colocar `service_role` ou secret key no HTML. Somente publishable key e RLS.

## Supabase

- Branch de desenvolvimento: `supabase-dev`.
- Branch de seguranca local antes do Supabase: `stable-localstorage-before-supabase`.
- A branch publica do Pages segue sendo `main` ate a nuvem ser testada.
- URL do projeto Supabase: `https://gjtrxzczvbtvftjqdmah.supabase.co`.
- Chave no HTML: publishable key `sb_publishable_...`.
- Para preparar o banco, rodar `supabase/schema.sql` no SQL Editor.
- Tabelas previstas: `profiles`, `albums`, `user_stickers`, `trade_offers`.
- O app compara trocas lendo `user_stickers` de usuarios autenticados: quem tem repetida de uma faltante sua e quem precisa de uma repetida sua.
- Recuperacao de senha fica no modal `Conta e sincronizacao`, usando `resetPasswordForEmail` e `updateUser`.
- Ao publicar, cadastrar nas Redirect URLs do Supabase: `https://brendofm-sketch.github.io/Album_Bernardo/` e o HTML principal.
- Aba `Amigos`: usa `profiles.email`, `profiles.last_seen`, `friendships` e `messages`; perfil do amigo cruza repetidas/faltantes entre os dois usuarios.
- Perfil/configuracoes: usa `profiles.username`, `profiles.username_search` e `profiles.avatar_id`; `username` preserva maiusculas/minusculas como digitado, `username_search` faz busca/unicidade sem diferenciar caixa. O nome exibido deve ser igual ao username.
- Topo simplificado: manter `Album`, `Trocas`, `Amigos`, `Estatisticas`, `Controle`; evitar duplicar `Paises`/`Repetidas`.
- Importacao/exportacao preferida no tablet: codigo de transferencia copiavel no perfil. JSON continua como backup tecnico em Trocas.
- Painel lateral de paises: manter alternador entre lista detalhada e grade compacta so com bandeiras; o modo fica salvo em `albumCountryViewMode`.
- Repetidas: o comando `clearDuplicatesOnly()` deve reduzir quantidades maiores que 1 para 1, preservando as figurinhas marcadas como tenho.
- Login: a tela de conta deve usar apenas `usuario ou e-mail` + senha para entrar; para criar conta, usar usuario, e-mail e senha. O botao de sincronizar fica somente nas configuracoes do usuario.
- Criacao de conta: se o Supabase criar usuario sem sessao imediata, preencher o login com o e-mail e permitir entrada pelo e-mail mesmo que o perfil/username ainda nao exista.
- Textos de login: manter a tela curta e sem explicacoes tecnicas sobre Supabase/sincronizacao; traduzir erros tecnicos para mensagens simples.
- Fundos de paises: imagens ativas ficam em `Fundo/COD.webp` e sao aplicadas por `ALBUM_BACKGROUNDS` como camada translucida sobre o papel do album. PNGs originais ficam em `Obsoleto/Fundo_originais/`.
- Fundo geral: paises com imagem em `ALBUM_BACKGROUNDS` tambem aplicam `Fundo/COD.webp` no fundo do site; a barra direita pode ser recolhida e o estado fica em `albumRightbarCollapsed`.
- Mobile: a barra direita deve virar secao horizontal abaixo do album; recolhida, mostra apenas um botao horizontal. Evitar faixa vertical alta em telas pequenas.

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
