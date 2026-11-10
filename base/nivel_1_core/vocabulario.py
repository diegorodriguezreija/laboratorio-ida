from enum import Enum


class _VocabEnum(str, Enum):
    def __str__(self) -> str:
        return str(self.value)


class V_Comando(_VocabEnum):
    # Locomocion y Espera
    MOVER = "ACC_MOVER"
    ACECHAR = "ACC_ACECHAR"
    ESPERAR = "ACC_ESPERAR"
    COLAPSO = "ACC_COLAPSO"             # Inmovilidad tonica por panico agudo sin salida
    # Tracto Motor Bifurcado (v11.0+ - PROHIBIDO usar el comando antiguo erradicado)
    DEGLUTIR = "ACC_DEGLUTIR"           # Metabolismo destructivo multi-bocado (cosecha energia fisica)
    ASIMILAR = "ACC_ASIMILAR"           # Epistemologia inmaterial pasiva (lee sin destruir)
    CENSURAR = "ACC_CENSURAR"           # Deontologia destructiva atomica (purga mentiras/amenazas parasitas)
    ATACAR = "ACC_ATACAR"               # Defensa/Combate activo contra amenaza
    # Ingenieria de Nicho y Gratificacion Diferida
    COGER = "ACC_COGER"                 # Carga en fauces/manos (aplica lastre metabolico -0.5/latido)
    SOLTAR = "ACC_SOLTAR"               # Deposita en zona segura o suelta lastre en emergencia


class V_Dominio(_VocabEnum):
    SUPERVIVENCIA = "SUPERVIVENCIA"     # S1: Integridad fisica e inminencia
    VALOR = "VALOR"                     # S2: Valencia estetica, agrado, aversion
    SOCIAL = "SOCIAL"                   # S2/S3: Fiabilidad de emisores y alianzas
    VERDAD = "VERDAD"                   # S3: Epistemologia y causalidad empirica
    DEONTICO = "DEONTICO"               # S3: Normas de linaje, tabues y deber ser


class V_Modalidad(_VocabEnum):
    SIENTE = "SIENTE"                   # Experiencia interoceptiva o afectiva directa
    CREE = "CREE"                       # Creencia asimilada con incertidumbre
    DESEA = "DESEA"                     # Meta proactiva o intencionalidad atribuida
    EXPRESA = "EXPRESA"                 # Emision comunicativa hacia el exterior (senales/alertas)
    HIPOTESIS = "HIPOTESIS"             # Conjetura formal pendiente de verificacion empirica
    DEMOSTRADO = "DEMOSTRADO"           # Verdad contrastada empiricamente (Trust >= 0.85, base del gameto fertil)
    DEMOSTRADO_DEDUCTIVO = "DEMOSTRADO_DEDUCTIVO"  # Derivado por silogismo puro sobre axiomas demostrados
    SIMULA_MENTE = "SIMULA_MENTE"       # Proyeccion en DimensionSimulada O(k) (Teoria de la Mente)
    ASUME_ROL = "ASUME_ROL"             # Identidad narrativa del Yo (Protector, Altruista, Explorador)


class V_Relacion(_VocabEnum):
    ES_NUTRITIVO = "ES_NUTRITIVO"
    ES_LETAL = "ES_LETAL"
    ES_SEGURO = "ES_SEGURO"
    ES_TERRORIFICO = "ES_TERRORIFICO"
    ES_AGRADABLE = "ES_AGRADABLE"
    ES_REPULSIVO = "ES_REPULSIVO"
    ES_ARMONICO = "ES_ARMONICO"
    ES_DISONANTE = "ES_DISONANTE"
    ES_ALIADO = "ES_ALIADO"
    ES_DESCONOCIDO = "ES_DESCONOCIDO"
    ES_ENEMIGO = "ES_ENEMIGO"
    ES_PARASITARIO = "ES_PARASITARIO"   # Emisor que busca Delta(IdA) < 0 y Delta(Emisor) > 0
    ES_TABU = "ES_TABU"                 # Prohibicion normativa del linaje
    ES_FALIBLE = "ES_FALIBLE"           # Metacognicion cuando Autoestima < 0.50
    ES_FIABLE = "ES_FIABLE"             # Metacognicion cuando Autoestima >= 0.85


class V_Vinculo(_VocabEnum):
    CAUSA = "CAUSA"                     # [A] CAUSA [B] (Consolidado por agencia causal ei -> ef)
    IMPLICA = "IMPLICA"                 # [A] IMPLICA [B] (Regla condicional o expectativa espacial)
    CONTRADICE = "CONTRADICE"           # [EMPIRISMO] CONTRADICE [TERROR_VICARIO / HIPOTESIS]
    ES_ANALOGO_A = "ES_ANALOGO_A"       # [Sujeto_A] ES_ANALOGO_A [Sujeto_B] (Isomorfismo O(1) en REM)
    MOTIVADO_POR = "MOTIVADO_POR"       # [Emisor EXPRESA X] MOTIVADO_POR [Emisor DESEA Y] (ToM)
    IMPONE_NORMA = "IMPONE_NORMA"       # [LINAJE] IMPONE_NORMA [...]
    DEBE = "DEBE"
    NO_DEBE = "NO_DEBE"
    PRIORIZA = "PRIORIZA"               # [PRIORIZA (Valor_Superior) SOBRE (Homeostasis)]
    SOBRE = "SOBRE"


class V_Estado(_VocabEnum):
    CALMA = "CALMA"
    ALERTA = "ALERTA"
    MIEDO = "MIEDO"
    PANICO = "PANICO"
    CURIOSIDAD = "CURIOSIDAD"
    CULPA = "CULPA"                     # Toxina psicosomatica por violar ES_TABU (-1.0 Vit/latido)
    SENESCENTE = "SENESCENTE"           # Edad biologica >= 0.88: serenidad y busqueda de zona segura
    TRASCENDENTE = "TRASCENDENTE"       # Sacrificio consciente o maxima integracion Phi >= 3.50
    DORMIDO = "DORMIDO"                 # Fase REM activa (Amplitud reducida a 20, paralisis motora)

