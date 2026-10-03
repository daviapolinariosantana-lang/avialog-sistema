# Avialog — projeto editável

O código da aplicação está organizado em `app/`, `lib/`, `db/` e `components/`. A pasta `portable/` contém o servidor local e a versão compilada para distribuição.

Para desenvolvimento com Node.js 22 ou superior:

```bash
npm ci
npm run build
```

Para uma versão portátil:

```bash
node node_modules/vite/bin/vite.js build --config vite.portable.config.ts
cp -r portable-dist/. portable/web/
```

O motor de cálculo está em `lib/model.ts`. Os testes de invariantes estão em `tests/model.test.mjs`.
