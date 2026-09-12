"""Servidor MCP stdio, sem dependências externas, para a API FacilApp Boletos."""
from __future__ import annotations

import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("FACILAPP_BOLETOS_URL", "http://127.0.0.1:4040").rstrip("/")
ACCESS_TOKEN: str | None = None


def api_request(method: str, path: str, body: Any = None, authenticated: bool = True) -> Any:
    headers = {"Accept": "application/json", "User-Agent": "FacilApp-Boletos-MCP/0.1.0"}
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if authenticated:
        if not ACCESS_TOKEN:
            raise RuntimeError("Autentique primeiro com facilapp_boletos_login.")
        headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
    request = Request(f"{BASE_URL}/{path.lstrip('/')}", data=data, headers=headers, method=method.upper())
    try:
        with urlopen(request, timeout=120) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type", "")
            if "json" in content_type:
                return json.loads(raw.decode("utf-8")) if raw else {"ok": True, "status": response.status}
            return {"status": response.status, "contentType": content_type, "bytes": len(raw), "url": request.full_url}
    except HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"FacilApp Boletos retornou HTTP {error.code}: {raw}") from error
    except URLError as error:
        raise RuntimeError(f"Não foi possível acessar {BASE_URL}: {error.reason}") from error


TOOLS = [
    {"name": "facilapp_boletos_status", "description": "Verifica status, versão e porta da API.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "facilapp_boletos_openapi", "description": "Obtém o contrato OpenAPI da API.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "facilapp_boletos_login", "description": "Autentica login/Client ID e senha/Secret ID. O Bearer permanece somente na memória do MCP.", "inputSchema": {"type": "object", "properties": {"login": {"type": "string"}, "senha": {"type": "string"}}, "required": ["login", "senha"]}},
    {"name": "facilapp_boletos_emitir", "description": "Emite e arquiva um boleto usando o contrato completo da API.", "inputSchema": {"type": "object", "properties": {"boleto": {"type": "object", "additionalProperties": True}}, "required": ["boleto"]}},
    {"name": "facilapp_boletos_listar", "description": "Lista os boletos do CNPJ autenticado em um período.", "inputSchema": {"type": "object", "properties": {"inicio": {"type": "string"}, "fim": {"type": "string"}}, "required": ["inicio", "fim"]}},
    {"name": "facilapp_boletos_obter", "description": "Consulta um boleto pelo ID e retorna seus links de documentos.", "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "facilapp_boletos_request", "description": "Chama outra rota documentada da API, restrita à URL configurada.", "inputSchema": {"type": "object", "properties": {"method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]}, "path": {"type": "string"}, "body": {}, "authenticated": {"type": "boolean", "default": True}}, "required": ["method", "path"]}},
]


def call_tool(name: str, args: dict[str, Any]) -> Any:
    global ACCESS_TOKEN
    if name == "facilapp_boletos_status":
        return api_request("GET", "/api/status", authenticated=False)
    if name == "facilapp_boletos_openapi":
        return api_request("GET", "/swagger/v1/swagger.json", authenticated=False)
    if name == "facilapp_boletos_login":
        result = api_request("POST", "/api/autenticacao/token", {"login": args["login"], "senha": args["senha"]}, authenticated=False)
        ACCESS_TOKEN = result.get("accessToken") or result.get("access_token")
        if not ACCESS_TOKEN:
            raise RuntimeError("A API autenticou, mas não retornou um access token.")
        safe = dict(result)
        for key in ("accessToken", "access_token"):
            if key in safe:
                safe[key] = "armazenado somente na memória do MCP"
        return safe
    if name == "facilapp_boletos_emitir":
        return api_request("POST", "/api/boletos", args["boleto"])
    if name == "facilapp_boletos_listar":
        query = urlencode({"inicio": args["inicio"], "fim": args["fim"]})
        return api_request("GET", f"/api/boletos?{query}")
    if name == "facilapp_boletos_obter":
        return api_request("GET", f"/api/boletos/{args['id']}", authenticated=False)
    if name == "facilapp_boletos_request":
        path = str(args["path"])
        if not path.startswith("/") or "://" in path:
            raise ValueError("Informe apenas um caminho local iniciado por /.")
        return api_request(args["method"], path, args.get("body"), args.get("authenticated", True))
    raise ValueError(f"Ferramenta desconhecida: {name}")


def response(request_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> None:
    payload = {"jsonrpc": "2.0", "id": request_id}
    payload["error" if error else "result"] = error if error else result
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main() -> None:
    for line in sys.stdin:
        try:
            message = json.loads(line)
            method, request_id = message.get("method"), message.get("id")
            if method == "initialize":
                response(request_id, {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "facilapp-boletos", "version": "0.1.0"}})
            elif method == "ping":
                response(request_id, {})
            elif method == "tools/list":
                response(request_id, {"tools": TOOLS})
            elif method == "tools/call":
                params = message.get("params") or {}
                try:
                    result = call_tool(params.get("name", ""), params.get("arguments") or {})
                    response(request_id, {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]})
                except Exception as error:
                    response(request_id, {"content": [{"type": "text", "text": str(error)}], "isError": True})
            elif request_id is not None:
                response(request_id, error={"code": -32601, "message": f"Método não suportado: {method}"})
        except Exception as error:
            response(None, error={"code": -32700, "message": str(error)})


if __name__ == "__main__":
    main()
