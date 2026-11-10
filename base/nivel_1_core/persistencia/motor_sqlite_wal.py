try:
    import sqlite3
except ImportError:
    sqlite3 = None
import json
import time
from typing import Optional
from nivel_1_core.contratos import Pieza, Episodio
from nivel_1_core.persistencia.memoria_tridimensional import DimensionActiva


class MotorSQLiteWAL:
    """
    Hipocampo Persistente en modo Write-Ahead Logging (WAL).
    Particionado estrictamente por id_linaje (Barrera de Weismann) sobre 4 tablas canonicas:
    nodos_semanticos, enlaces_causales, episodios, topologia.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._configurar_wal_y_esquema()

    def _configurar_wal_y_esquema(self) -> None:
        cur = self.conn.cursor()
        ejecutar = getattr(cur, "execute")
        sentencias = (
            "PRAGMA journal_mode=WAL;",
            "PRAGMA synchronous=NORMAL;",
            "PRAGMA temp_store=MEMORY;",
            """
            CREATE TABLE IF NOT EXISTS nodos_semanticos (
                id_linaje TEXT NOT NULL,
                id_sujeto TEXT NOT NULL,
                componente TEXT NOT NULL,
                dominio TEXT,
                relacion TEXT,
                arousal REAL NOT NULL,
                trust REAL NOT NULL,
                heredado INTEGER NOT NULL DEFAULT 0,
                demostrado_de_novo INTEGER NOT NULL DEFAULT 0,
                product_json TEXT NOT NULL,
                inputs_json TEXT NOT NULL,
                updated REAL NOT NULL,
                PRIMARY KEY (id_linaje, id_sujeto, componente)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS enlaces_causales (
                id_linaje TEXT NOT NULL,
                id_origen TEXT NOT NULL,
                id_destino TEXT NOT NULL,
                componente_destino TEXT NOT NULL,
                vinculo TEXT NOT NULL,
                peso_trust REAL NOT NULL,
                updated REAL NOT NULL,
                PRIMARY KEY (id_linaje, id_origen, id_destino, vinculo)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS episodios (
                id_linaje TEXT NOT NULL,
                id_episodio TEXT NOT NULL,
                ubicacion_principal TEXT NOT NULL,
                ciclo_inicio INTEGER NOT NULL,
                ciclo_fin INTEGER NOT NULL,
                balance_vital REAL NOT NULL,
                resuelto INTEGER NOT NULL,
                ondas_json TEXT NOT NULL,
                piezas_json TEXT NOT NULL,
                PRIMARY KEY (id_linaje, id_episodio)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS topologia (
                id_linaje TEXT NOT NULL,
                id_origen TEXT NOT NULL,
                id_destino TEXT NOT NULL,
                coste REAL NOT NULL,
                veces_transitado REAL NOT NULL,
                updated REAL NOT NULL,
                PRIMARY KEY (id_linaje, id_origen, id_destino)
            );
            """,
        )
        for sql in sentencias:
            ejecutar(sql)
        self.conn.commit()

    def sincronizar_desde_activa(self, activa: DimensionActiva) -> None:
        """Vuelca atomicamente la DimensionActiva de un linaje en SQLite WAL."""
        cur = self.conn.cursor()
        ejecutar = getattr(cur, "execute")
        ahora = time.time()
        linaje = activa.id_linaje

        for sujeto_id, cajon in activa.indice_identidad.items():
            for comp_nombre, p in cajon.items():
                ejecutar(
                    """
                    INSERT OR REPLACE INTO nodos_semanticos (
                        id_linaje, id_sujeto, componente, dominio, relacion,
                        arousal, trust, heredado, demostrado_de_novo,
                        product_json, inputs_json, updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        linaje,
                        sujeto_id,
                        comp_nombre,
                        str(p.product.get("dominio", "")),
                        str(p.product.get("relacion", "")),
                        p.arousal,
                        p.trust,
                        1 if p.heredado else 0,
                        1 if p.demostrado_de_novo else 0,
                        json.dumps({k: (str(v) if hasattr(v, "value") else v) for k, v in p.product.items()}),
                        json.dumps(p.inputs),
                        ahora,
                    ),
                )

        for id_orig, enlaces in activa.indice_causal.items():
            for id_dest, comp_dest, vinc, trust_val in enlaces:
                ejecutar(
                    """
                    INSERT OR REPLACE INTO enlaces_causales (
                        id_linaje, id_origen, id_destino, componente_destino, vinculo, peso_trust, updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (linaje, id_orig, id_dest, comp_dest, vinc, trust_val, ahora),
                )

        for ep in activa.banco_episodico:
            ejecutar(
                """
                INSERT OR REPLACE INTO episodios (
                    id_linaje, id_episodio, ubicacion_principal, ciclo_inicio, ciclo_fin,
                    balance_vital, resuelto, ondas_json, piezas_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    linaje,
                    ep.id_episodio,
                    ep.ubicacion_principal,
                    ep.ciclo_inicio,
                    ep.ciclo_fin,
                    ep.balance_vital,
                    1 if ep.resuelto else 0,
                    json.dumps(ep.ondas_resumen),
                    json.dumps(ep.piezas_clave),
                ),
            )

        for orig, destinos in activa.grafo_topologico.items():
            for dest, datos in destinos.items():
                ejecutar(
                    """
                    INSERT OR REPLACE INTO topologia (
                        id_linaje, id_origen, id_destino, coste, veces_transitado, updated
                    ) VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (linaje, orig, dest, datos["coste"], datos["veces_transitado"], ahora),
                )

        self.conn.commit()

    def cargar_hacia_activa(self, activa: DimensionActiva, marcar_heredado: bool = True) -> None:
        """Restaura el conocimiento de un linaje específico respetando la Barrera de Weismann."""
        cur = self.conn.cursor()
        ejecutar = getattr(cur, "execute")
        linaje = activa.id_linaje

        ejecutar(
            "SELECT id_sujeto, componente, arousal, trust, heredado, demostrado_de_novo, product_json, inputs_json FROM nodos_semanticos WHERE id_linaje = ?;",
            (linaje,),
        )
        for fila in cur.fetchall():
            sujeto_id, comp, arousal, trust, heredado, dem_novo, prod_j, inp_j = fila
            es_heredado = True if marcar_heredado else bool(heredado)
            p = Pieza(
                id=sujeto_id,
                tipo_componente=comp,
                arousal=float(arousal),
                trust=float(trust),
                product=json.loads(prod_j),
                inputs=json.loads(inp_j),
                heredado=es_heredado,
                demostrado_de_novo=(False if es_heredado else bool(dem_novo)),
            )
            activa.consolidar_pieza(sujeto_id, p)

        ejecutar(
            "SELECT id_origen, id_destino, componente_destino, vinculo, peso_trust FROM enlaces_causales WHERE id_linaje = ?;",
            (linaje,),
        )
        for id_o, id_d, comp_d, vinc, p_trust in cur.fetchall():
            activa.indice_causal.setdefault(id_o, []).append((id_d, comp_d, vinc, float(p_trust)))

        ejecutar(
            "SELECT id_origen, id_destino, coste, veces_transitado FROM topologia WHERE id_linaje = ?;",
            (linaje,),
        )
        for id_o, id_d, coste, veces in cur.fetchall():
            activa.grafo_topologico.setdefault(id_o, {})[id_d] = {
                "coste": float(coste),
                "veces_transitado": float(veces),
            }
