# FacilApp Boletos — Plugin Codex/MCP

Integra a API FacilApp Boletos ao Codex por um servidor MCP stdio em Python, sem dependências externas.

Por padrão, o servidor acessa `http://127.0.0.1:4040`. Para outra instalação, configure `FACILAPP_BOLETOS_URL` no ambiente do MCP.

O Bearer fica somente na memória do processo MCP e nunca é persistido pelo plugin.
