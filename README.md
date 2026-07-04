# Album Copa 2026

Aplicacao estatica/PWA para controlar o album fisico da Copa 2026 em tablet.

## Abrir o app

Arquivo principal:

```text
album_copa_2026_premium_imagens_externas.html
```

No GitHub Pages:

```text
https://brendofm-sketch.github.io/Album_Bernardo/
```

## Estrutura ativa

- `album_copa_2026_premium_imagens_externas.html`: interface e dados do album.
- `index.html`: entrada para o GitHub Pages.
- `figurinhas/`: imagens em `COD_00.webp`.
- `bandeiras/`: bandeiras em SVG.
- `manifest.webmanifest`, `sw.js`, `icon-192.png`, `icon-512.png`: PWA.
- `start_tablet_server.py`: servidor local opcional.
- `MEMORIA_PROJETO.md`: memoria viva do projeto.

## Imagens

O padrao das figurinhas e:

```text
figurinhas/COD_00.webp
```

Exemplos:

```text
figurinhas/BRA_01.webp
figurinhas/ARG_17.webp
figurinhas/FWC_12.webp
figurinhas/CC_04.webp
```

Para substituir uma figurinha, troque o arquivo mantendo exatamente o mesmo nome.

## Publicar

Depois de alterar:

```bash
git status --short
git add .
git commit -m "Descricao da alteracao"
git push
```

Se o GitHub Pages demorar ou ficar preso, um commit vazio costuma forcar republicacao:

```bash
git commit --allow-empty -m "Republica ajustes"
git push
```

## Tablet

No tablet, abra o link do GitHub Pages e use a opcao do navegador para adicionar a tela inicial.

O progresso fica salvo no navegador do aparelho. Use `Backup` e `Importar JSON` dentro do app para transferir progresso entre aparelhos.

## Supabase

O desenvolvimento com login e trocas esta no branch `supabase-dev`, para nao mexer no link publico usado pelo Bernardo enquanto a nuvem e testada.

Antes de testar login:

1. Abra o Supabase do projeto.
2. Va em `SQL Editor`.
3. Cole e rode o conteudo de `supabase/schema.sql`.
4. Abra o app no branch de teste e use o botao `Nuvem`.

A chave usada no HTML e a publishable key. Nao coloque `service_role` ou secret key no app estatico.

O app continua local-first: salva no `localStorage`, funciona offline, e quando entra na conta sincroniza com o Supabase mesclando as quantidades maiores de cada figurinha.

A aba `Amigos` usa as tabelas `friendships` e `messages`, e a busca agora usa `profiles.username` em vez de e-mail. Sempre que essa parte mudar, rode novamente `supabase/schema.sql` no SQL Editor para atualizar o banco sem apagar dados.

Para recuperacao de senha, cadastre a URL publicada do album em `Authentication` > `URL Configuration` > `Redirect URLs`:

```text
https://brendofm-sketch.github.io/Album_Bernardo/
https://brendofm-sketch.github.io/Album_Bernardo/album_copa_2026_premium_imagens_externas.html
```

## Obsoleto

A pasta `Obsoleto/` guarda PDFs, recortes, backups, referencias, auditorias e scripts antigos. Ela fica fora do GitHub pelo `.gitignore`.

Nao use arquivos de `Obsoleto/` como fonte ativa sem revisar antes.
