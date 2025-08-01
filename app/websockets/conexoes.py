from typing import Dict, List
from fastapi import WebSocket

class GerenciadorConexoes:
    def __init__(self):
        self.salas: Dict[str, List[WebSocket]] = {}

    async def conectar(self, sala_id: str, websocket: WebSocket):
        if sala_id not in self.salas:
            self.salas[sala_id] = []
        self.salas[sala_id].append(websocket)

    def desconectar(self, sala_id: str, websocket: WebSocket):
        if sala_id in self.salas and websocket in self.salas[sala_id]:
            self.salas[sala_id].remove(websocket)
            if not self.salas[sala_id]:
                del self.salas[sala_id]

    async def enviar_para_sala(self, sala_id: str, mensagem: dict):
        if sala_id in self.salas:
            for conexao in self.salas[sala_id]:
                await conexao.send_json(mensagem)
