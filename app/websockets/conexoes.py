from typing import Dict, List
from fastapi import WebSocket

class GerenciadorConexoes:
    def __init__(self):
        self.salas: Dict[str, List[WebSocket]] = {}

    async def conectar(self, sala_id: str, websocket: WebSocket, usuario: dict):
        if sala_id not in self.salas:
            self.salas[sala_id] = []
        self.salas[sala_id].append((websocket, usuario))

    def desconectar(self, sala_id: str, websocket: WebSocket):
        if sala_id in self.salas:
            self.salas[sala_id] = [
                (ws, usuario) for (ws, usuario) in self.salas[sala_id]
                if ws != websocket
            ]
            if not self.salas[sala_id]:
                del self.salas[sala_id]

    def lista_usuarios_na_sala(self, sala_id: str) -> list[dict]:
        return [usuario for (_, usuario) in self.salas.get(sala_id, [])]
    

    async def enviar_para_sala(self, sala_id: str, mensagem: dict):
        for websocket, _ in self.salas.get(sala_id, []):
            await websocket.send_json(mensagem)

    async def enviar_para_usuario(self, websocket: WebSocket, mensagem: dict):
        await websocket.send_json(mensagem)

