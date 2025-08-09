from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from fastapi import WebSocket
import asyncio

@dataclass
class Conexao:
    websocket: WebSocket
    usuario: dict  # idealmente conter ao menos {"id": "...", "nome": "..."} ou similar

class GerenciadorConexoes:
    def __init__(self):
        self.salas: Dict[str, List[Conexao]] = {}
        self._lock = asyncio.Lock()

    async def conectar(self, sala_id: str, websocket: WebSocket, usuario: dict) -> None:
        """Adiciona um websocket à sala informada e aceita a conexão caso necessário."""
        await websocket.accept()
        async with self._lock:
            lista = self.salas.setdefault(sala_id, [])
            if not any(c.websocket is websocket for c in lista):
                lista.append(Conexao(websocket=websocket, usuario=usuario))

    async def desconectar(self, sala_id: str, websocket: WebSocket) -> None:
        """Remove o websocket da sala; remove a sala se ficar vazia."""
        async with self._lock:
            if sala_id in self.salas:
                self.salas[sala_id] = [c for c in self.salas[sala_id] if c.websocket is not websocket]
                if not self.salas[sala_id]:
                    del self.salas[sala_id]
        try:
            await websocket.close()
        except Exception:
            pass

    def lista_usuarios_na_sala(self, sala_id: str) -> List[dict]:
        """Retorna a lista de payloads de usuário presentes na sala."""
        return [c.usuario for c in self.salas.get(sala_id, [])]

    def conexao_por_usuario(self, sala_id: str, usuario_id: str) -> Optional[Conexao]:
        """Retorna a conexão de um usuário da sala dado seu id, se existir."""
        for c in self.salas.get(sala_id, []):
            if str(c.usuario.get("id")) == str(usuario_id):
                return c
        return None

    async def enviar_para_sala(self, sala_id: str, mensagem: dict) -> None:
        """Envia uma mensagem a todos na sala, removendo conexões quebradas."""
        await self._broadcast(sala_id, mensagem, excluir_ws=None)

    async def enviar_para_outros(self, sala_id: str, remetente: WebSocket, mensagem: dict) -> None:
        """Envia uma mensagem a todos na sala exceto o remetente."""
        await self._broadcast(sala_id, mensagem, excluir_ws=remetente)

    async def enviar_para_usuario(self, websocket: WebSocket, mensagem: dict) -> None:
        """Envia uma mensagem diretamente a um websocket específico."""
        await websocket.send_json(mensagem)

    def salas_ativas(self) -> List[str]:
        """Lista os IDs das salas ativas."""
        return list(self.salas.keys())

    def total_conexoes(self, sala_id: Optional[str] = None) -> int:
        """Retorna o total de conexões em uma sala ou no sistema."""
        if sala_id is not None:
            return len(self.salas.get(sala_id, []))
        return sum(len(lst) for lst in self.salas.values())

    async def _broadcast(self, sala_id: str, mensagem: dict, excluir_ws: Optional[WebSocket]) -> None:
        """Envia mensagem para a sala com tolerância a falhas e remoção de sockets inválidos."""
        conexoes_snapshot: List[Conexao] = list(self.salas.get(sala_id, []))
        desconectar: List[WebSocket] = []
        for c in conexoes_snapshot:
            if excluir_ws is not None and c.websocket is excluir_ws:
                continue
            try:
                await c.websocket.send_json(mensagem)
            except Exception:
                desconectar.append(c.websocket)
        if desconectar:
            async with self._lock:
                if sala_id in self.salas:
                    self.salas[sala_id] = [c for c in self.salas[sala_id] if c.websocket not in desconectar]
                    if not self.salas[sala_id]:
                        del self.salas[sala_id]
            for ws in desconectar:
                try:
                    await ws.close()
                except Exception:
                    pass
