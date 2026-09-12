---
name: facilapp-boletos
description: Use a API FacilApp Boletos para verificar status, autenticar, emitir e consultar boletos e acessar seus documentos. Use quando o usuário mencionar FacilApp Boletos, porta 4040, emissão de cobrança, boleto, PDF bancário ou XML de boleto.
---

# FacilApp Boletos

Use as ferramentas MCP `facilapp_boletos_*` para interagir com a API.

## Regras

- Verifique a disponibilidade com `facilapp_boletos_status` antes de operações protegidas.
- Use `facilapp_boletos_login` antes de emitir ou listar boletos.
- Nunca repita, registre ou exiba senha, Secret ID ou Bearer.
- Consulte `facilapp_boletos_openapi` quando o contrato de uma rota não estiver claro.
- Não invente campos ausentes no OpenAPI.
- Confirme os dados financeiros e o beneficiário antes de emitir um boleto.
- A emissão exige autenticação e fica limitada ao CNPJ da credencial.
- Links individuais de HTML, visualização, impressão, PDF e XML podem ser compartilhados com o destinatário.
- O token emitido pela API vale 30 dias, salvo revogação ou desativação da credencial.

## Fluxo normal

1. Verifique a API com `facilapp_boletos_status`.
2. Autentique com `facilapp_boletos_login`.
3. Consulte o período com `facilapp_boletos_listar` ou um ID com `facilapp_boletos_obter`.
4. Para emissão, envie o objeto completo documentado a `facilapp_boletos_emitir`.
5. Use os links retornados para HTML, impressão, PDF e XML.
