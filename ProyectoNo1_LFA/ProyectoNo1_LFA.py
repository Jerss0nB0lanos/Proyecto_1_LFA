# -*- coding: utf-8 -*-
"""
Proyecto No. 2 - Lenguajes Formales y Autómatas
Motor de AFD, AFND, Conversión por Subconjuntos y Simulación
Todo en un solo archivo para evitar problemas de importación.
"""

import re

# ========================== CLASE AFD ==========================
class AFD:
    """
    Representa un Autómata Finito Determinista (AFD).
    """
    def __init__(self, nombre=""):
        self.nombre = nombre
        self.Q = set()          # estados
        self.Sigma = set()      # alfabeto
        self.delta = {}         # transiciones: (estado, simbolo) -> estado
        self.q0 = None          # estado inicial
        self.F = set()          # estados finales
        # Atributos para análisis estructural
        self.estados_alcanzables = set()
        self.estados_inaccesibles = set()
        self.finales_alcanzables = set()
        self.lenguaje_vacio = False
        self.historial = []     # evaluaciones

    def agregar_transicion(self, origen, simbolo, destino):
        """
        Agrega una transición. Lanza excepción si ya existe (AFND).
        """
        clave = (origen, simbolo)
        if clave in self.delta:
            raise ValueError(f"Transición duplicada para ({origen}, {simbolo}). No es determinista.")
        self.delta[clave] = destino

    def __str__(self):
        return (f"AFD: {self.nombre}\nQ = {self.Q}\nΣ = {self.Sigma}\n"
                f"δ = {self.delta}\nq0 = {self.q0}\nF = {self.F}")

    def tabla_transiciones(self):
        """
        Devuelve encabezado y filas para mostrar la tabla de transiciones.
        """
        estados = sorted(self.Q)
        simbolos = sorted(self.Sigma)
        header = ["Estado"] + simbolos
        filas = []
        for estado in estados:
            fila = [estado]
            for sim in simbolos:
                fila.append(self.delta.get((estado, sim), "-"))
            filas.append(fila)
        return header, filas


class AFND:
    """Representa un AFND como M = (Q, Sigma, delta, q0, F)."""
    def __init__(self, nombre=""):
        self.nombre = nombre
        self.Q = set()
        self.Sigma = set()
        self.delta = {}  # (estado, simbolo) -> set de destinos
        self.q0 = None
        self.F = set()

    def agregar_transicion(self, origen, simbolo, destinos):
        """Guarda cero, uno o varios destinos para un mismo par."""
        clave = (origen, simbolo)
        if clave not in self.delta:
            self.delta[clave] = set()
        self.delta[clave].update(destinos)

    def obtener_destinos(self, estado, simbolo):
        return self.delta.get((estado, simbolo), set())

    def __str__(self):
        transiciones = {}
        for clave, destinos in self.delta.items():
            transiciones[clave] = set(destinos)
        return (f"AFND: {self.nombre}\nQ = {self.Q}\nΣ = {self.Sigma}\n"
                f"δ = {transiciones}\nq0 = {self.q0}\nF = {self.F}")

    def tabla_transiciones(self):
        header = ["Estado"] + sorted(self.Sigma)
        filas = []
        for estado in sorted(self.Q):
            fila = [estado]
            for simbolo in sorted(self.Sigma):
                destinos = self.obtener_destinos(estado, simbolo)
                if destinos:
                    fila.append("{" + ",".join(sorted(destinos)) + "}")
                else:
                    fila.append("∅")
            filas.append(fila)
        return header, filas


def es_epsilon(valor):
    """Reconoce las formas prohibidas de epsilon sin importar mayúsculas."""
    return valor.strip().casefold() in {"ε", "epsilon"}


def normalizar_cadena(texto):
    """Convierte ε / epsilon (o texto vacío) en la cadena vacía."""
    texto = texto.strip()
    return "" if es_epsilon(texto) else texto


def generar_nombre_macroestado(indice):
    """Genera A, B, ..., Z, AA, AB... para identificar macroestados."""
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    indice += 1
    nombre = ""
    while indice > 0:
        indice, residuo = divmod(indice - 1, 26)
        nombre = letras[residuo] + nombre
    return nombre

# ========================== CLASE PDA (APD / APND) ==========================
class PDA:
    """
    Autómata de Pila Determinista (APD) o No Determinista (APND).
    M = (Q, Σ, Γ, δ, q0, Z0, F)
    δ: (estado, símbolo_entrada, tope_pila) -> lista de (destino, reemplazo)
    - 'EPS' se usa para ε (en entrada o en reemplazo de pila).
    - reemplazo es lista de símbolos; el índice 0 es el nuevo tope.
    - lista vacía en reemplazo significa "desapilar sin insertar".
    """

    def __init__(self, nombre="", tipo="APD"):
        self.nombre = nombre
        self.tipo = tipo.upper()          # "APD" o "APND"
        self.Q = set()                    # estados
        self.Sigma = set()                # alfabeto de entrada
        self.Gamma = set()                # alfabeto de pila
        self.q0 = None                    # estado inicial
        self.Z0 = None                    # símbolo inicial de pila
        self.F = set()                    # estados finales
        self.delta = {}                   # (estado, entrada, tope) -> [(destino, [reemplazo])]
        self.historial = []

    def agregar_transicion(self, origen, simbolo, tope, destino, reemplazo):
        clave = (origen, simbolo, tope)
        self.delta.setdefault(clave, []).append((destino, list(reemplazo)))

    def __str__(self):
        lineas = [f"{self.tipo}: {self.nombre}",
                  f"Q = {sorted(self.Q)}",
                  f"Σ = {sorted(self.Sigma)}",
                  f"Γ = {sorted(self.Gamma)}",
                  f"q0 = {self.q0}",
                  f"Z0 = {self.Z0}",
                  f"F = {sorted(self.F)}",
                  "δ:"]
        for (o, s, t), alts in sorted(self.delta.items()):
            for d, r in alts:
                reempl = ";".join(r) if r else "EPS"
                lineas.append(f"   ({o}, {s}, {t}) -> ({d}, {reempl})")
        if not self.delta:
            lineas.append("   (vacía)")
        return "\n".join(lineas)


def parsear_linea_transicion_pda(linea):
    """
    Parsear una línea de transición del formato del proyecto.
    Formato general: est,entrada,tope,dest,reempl|dest2,reempl2|...
    Devuelve lista de tuplas (origen, simbolo, tope, destino, reemplazo_list).
    """
    partes = [p.strip() for p in linea.split("|")]
    if not partes or not partes[0]:
        raise ValueError("Línea de transición vacía.")

    campos0 = [c.strip() for c in partes[0].split(",")]
    if len(campos0) != 5:
        raise ValueError(
            f"La primera alternativa debe tener 5 campos "
            f"(estado, entrada, tope, destino, reemplazo); tiene {len(campos0)}."
        )
    origen, simbolo, tope, destino0, reempl0 = campos0

    def _parsear_reemplazo(texto):
        texto = texto.strip()
        if not texto:
            raise ValueError("Reemplazo vacío.")
        if texto == "EPS":
            return []
        piezas = [p.strip() for p in texto.split(";")]
        for p in piezas:
            if not p:
                raise ValueError("Símbolo vacío dentro del reemplazo.")
            if p == "EPS":
                raise ValueError("EPS no puede combinarse con otros símbolos en el reemplazo.")
        return piezas

    resultado = [(origen, simbolo, tope, destino0, _parsear_reemplazo(reempl0))]

    for parte in partes[1:]:
        campos = [c.strip() for c in parte.split(",")]
        if len(campos) != 2:
            raise ValueError(
                f"Cada alternativa adicional debe tener 2 campos (destino, reemplazo); "
                f"tiene {len(campos)}."
            )
        destino, reempl = campos
        if not destino:
            raise ValueError("Destino vacío en alternativa.")
        resultado.append((origen, simbolo, tope, destino, _parsear_reemplazo(reempl)))

    return resultado

# ========================== CARGA MANUAL Y DESDE ARCHIVO ==========================
def cargar_manual():
    """
    Solicita al usuario los componentes del AFD por consola.
    Retorna un objeto AFD.
    """
    print("\n--- CREACIÓN MANUAL DE AFD ---")
    nombre = input("Nombre o identificador del autómata: ").strip()
    afd = AFD(nombre)

    # Estados: se revisan duplicados antes de convertir la lista a set.
    while True:
        estados_str = input("Ingrese los estados (separados por comas): ").strip()
        estados = [e.strip() for e in estados_str.split(",") if e.strip()]
        duplicados = {e for e in estados if estados.count(e) > 1}
        if not estados:
            print("Debe ingresar al menos un estado.")
        elif duplicados:
            print(f"Error: estados duplicados: {sorted(duplicados)}. Intente de nuevo.")
        else:
            afd.Q = set(estados)
            break

    # Alfabeto: también se revisan duplicados antes de usar set.
    while True:
        sigma_str = input("Ingrese el alfabeto (símbolos separados por comas): ").strip()
        sigma = [s.strip() for s in sigma_str.split(",") if s.strip()]
        duplicados = {s for s in sigma if sigma.count(s) > 1}
        if not sigma:
            print("Debe ingresar al menos un símbolo.")
        elif duplicados:
            print(f"Error: símbolos duplicados: {sorted(duplicados)}. Intente de nuevo.")
        # Epsilon no forma parte del alfabeto porque no consume un símbolo de entrada.
        elif any(s.casefold() in {"ε", "epsilon"} for s in sigma):
            print("Error: ε no puede formar parte del alfabeto de un AFD.")
        elif any(len(s) != 1 for s in sigma):
            print("Error: cada símbolo del alfabeto debe tener un solo carácter.")
        else:
            afd.Sigma = set(sigma)
            break

    # Estado inicial
    while True:
        q0 = input("Ingrese el estado inicial: ").strip()
        if q0 in afd.Q:
            afd.q0 = q0
            break
        else:
            print(f"Error: '{q0}' no está en el conjunto de estados. Intente de nuevo.")

    # F puede ser vacío: el AFD es válido, aunque no aceptará cadenas.
    while True:
        finales_str = input("Ingrese los estados finales (separados por comas): ").strip()
        if not finales_str:
            afd.F = set()
            break
        finales = [f.strip() for f in finales_str.split(",") if f.strip()]
        # Se buscan duplicados antes de usar set para no ocultarlos.
        duplicados = {f for f in finales if finales.count(f) > 1}
        if duplicados:
            print(
                f"Error: estados finales duplicados: {sorted(duplicados)}. "
                "Intente de nuevo."
            )
        elif all(f in afd.Q for f in finales):
            afd.F = set(finales)
            break
        else:
            print("Error: uno o más estados finales no pertenecen a Q. Intente de nuevo.")

    # Transiciones
    print("\nIngrese las transiciones una por una.")
    print("Formato: estado_origen, símbolo, estado_destino")
    print("Escriba 'fin' para terminar.")
    # Regex exige exactamente tres elementos y permite espacios junto a las comas.
    patron_transicion_manual = re.compile(
        r"([^,\s]+)\s*,\s*([^,\s]+)\s*,\s*([^,\s]+)"
    )
    while True:
        linea = input("Transición: ").strip()
        if linea.lower() == "fin":
            break
        coincidencia = patron_transicion_manual.fullmatch(linea)
        if not coincidencia:
            print("Formato incorrecto. Debe ser: origen, símbolo, destino")
            continue
        origen, simbolo, destino = coincidencia.groups()
        if origen not in afd.Q:
            print(f"Error: '{origen}' no está en Q.")
            continue
        # Un AFD consume símbolos; no puede cambiar de estado usando epsilon.
        if simbolo.casefold() in {"ε", "epsilon"}:
            print("Error: un AFD no permite transiciones ε.")
            continue
        if simbolo not in afd.Sigma:
            print(f"Error: '{simbolo}' no está en Σ.")
            continue
        if destino not in afd.Q:
            print(f"Error: '{destino}' no está en Q.")
            continue
        try:
            afd.agregar_transicion(origen, simbolo, destino)
            print("Transición agregada.")
        except ValueError as e:
            print(f"Error: {e}")

    return afd


def cargar_desde_archivo(ruta_archivo):
    """
    Lee un archivo de texto con el formato especificado y retorna un objeto AFD.
    Las expresiones regulares validan la sintaxis completa de cada línea.
    """
    if not str(ruta_archivo).lower().endswith(".txt"):
        raise ValueError("Solo se permiten archivos .txt.")

    afd = AFD()
    modo_transiciones = False

    # Un elemento no puede estar vacío ni contener comas o espacios.
    elemento = r"[^,\s]+"
    lista = rf"({elemento}(?:\s*,\s*{elemento})*)"

    # fullmatch exige que toda la línea, de principio a fin, cumpla el patrón.
    patrones_secciones = {
        "NOMBRE": re.compile(r"NOMBRE\s*=\s*(\S+)\s*", re.IGNORECASE),
        "ESTADOS": re.compile(rf"ESTADOS\s*=\s*{lista}\s*", re.IGNORECASE),
        "ALFABETO": re.compile(rf"ALFABETO\s*=\s*{lista}\s*", re.IGNORECASE),
        "INICIAL": re.compile(rf"INICIAL\s*=\s*({elemento})\s*", re.IGNORECASE),
        # El grupo opcional permite escribir FINALES= para representar F vacío.
        "FINALES": re.compile(
            rf"FINALES\s*=\s*({elemento}(?:\s*,\s*{elemento})*)?\s*",
            re.IGNORECASE
        ),
        "TRANSICIONES": re.compile(r"TRANSICIONES\s*:\s*", re.IGNORECASE)
    }
    # Tres elementos separados por comas: origen, símbolo y destino.
    patron_transicion = re.compile(
        rf"({elemento})\s*,\s*({elemento})\s*,\s*({elemento})"
    )
    secciones_encontradas = set()
    secciones_esperadas = set(patrones_secciones)
    valores_secciones = {}
    transiciones_temporales = []

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise Exception(f"Error al leer el archivo: {e}")

    # ETAPA 1: reconocer la sintaxis y guardar los datos temporalmente.
    for num_linea, linea_raw in enumerate(lineas, start=1):
        linea = linea_raw.strip()
        if not linea:
            continue

        # Primero se comprueba si la línea es una sección principal.
        seccion_actual = None
        coincidencia = None
        for nombre_seccion, patron in patrones_secciones.items():
            resultado = patron.fullmatch(linea)
            if resultado:
                seccion_actual = nombre_seccion
                coincidencia = resultado
                break

        if seccion_actual:
            if seccion_actual in secciones_encontradas:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: "
                    f"la sección {seccion_actual} está repetida."
                )
            if modo_transiciones:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: no se permiten "
                    f"secciones después de TRANSICIONES: '{linea}'"
                )

            secciones_encontradas.add(seccion_actual)
            if seccion_actual == "TRANSICIONES":
                modo_transiciones = True
            else:
                valores_secciones[seccion_actual] = (
                    coincidencia.group(1), num_linea
                )
            continue

        if modo_transiciones:
            coincidencia = patron_transicion.fullmatch(linea)
            if not coincidencia:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: '{linea}'"
                )
            transiciones_temporales.append((num_linea,) + coincidencia.groups())
            continue

        raise SyntaxError(f"Error de sintaxis en línea {num_linea}: '{linea}'")

    faltantes = secciones_esperadas - secciones_encontradas
    if faltantes:
        raise ValueError(
            f"Faltan las siguientes secciones: {', '.join(sorted(faltantes))}."
        )

    # ETAPA 2: construir el AFD y validar relaciones entre sus componentes.
    afd.nombre = valores_secciones["NOMBRE"][0]

    estados_str, linea_estados = valores_secciones["ESTADOS"]
    estados = [e.strip() for e in estados_str.split(",")]
    duplicados = {e for e in estados if estados.count(e) > 1}
    if duplicados:
        raise ValueError(
            f"Línea {linea_estados}: estados duplicados: {sorted(duplicados)}."
        )
    afd.Q = set(estados)

    sigma_str, linea_sigma = valores_secciones["ALFABETO"]
    sigma = [s.strip() for s in sigma_str.split(",")]
    duplicados = {s for s in sigma if sigma.count(s) > 1}
    if duplicados:
        raise ValueError(
            f"Línea {linea_sigma}: símbolos duplicados: {sorted(duplicados)}."
        )
    if any(s.casefold() in {"ε", "epsilon"} for s in sigma):
        raise ValueError(
            f"Línea {linea_sigma}: ε no puede formar parte del alfabeto de un AFD."
        )
    if any(len(s) != 1 for s in sigma):
        raise ValueError(
            f"Línea {linea_sigma}: cada símbolo del alfabeto debe tener un solo carácter."
        )
    afd.Sigma = set(sigma)

    q0, linea_inicial = valores_secciones["INICIAL"]
    if q0 not in afd.Q:
        raise ValueError(
            f"Línea {linea_inicial}: el estado inicial '{q0}' no pertenece a Q."
        )
    afd.q0 = q0

    finales_str, linea_finales = valores_secciones["FINALES"]
    finales = []
    if finales_str:
        finales = [f.strip() for f in finales_str.split(",")]
    duplicados = {f for f in finales if finales.count(f) > 1}
    if duplicados:
        raise ValueError(
            f"Línea {linea_finales}: estados finales duplicados: "
            f"{sorted(duplicados)}."
        )
    finales_invalidos = sorted(f for f in finales if f not in afd.Q)
    if len(finales_invalidos) == 1:
        raise ValueError(
            f"Línea {linea_finales}: el estado final "
            f"'{finales_invalidos[0]}' no pertenece a Q."
        )
    if len(finales_invalidos) > 1:
        raise ValueError(
            f"Línea {linea_finales}: los estados finales "
            f"{finales_invalidos} no pertenecen a Q."
        )
    afd.F = set(finales)

    for num_linea, origen, simbolo, destino in transiciones_temporales:
        if origen not in afd.Q:
            raise ValueError(
                f"Línea {num_linea}: el estado origen '{origen}' no pertenece a Q."
            )
        if simbolo.casefold() in {"ε", "epsilon"}:
            raise ValueError(
                f"Línea {num_linea}: un AFD no permite transiciones ε."
            )
        if simbolo not in afd.Sigma:
            raise ValueError(
                f"Línea {num_linea}: el símbolo '{simbolo}' no pertenece al alfabeto."
            )
        if destino not in afd.Q:
            raise ValueError(
                f"Línea {num_linea}: el estado destino '{destino}' no pertenece a Q."
            )
        # CORRECCIÓN: distinguir transición repetida de transición no determinista.
        clave = (origen, simbolo)
        if clave in afd.delta:
            if afd.delta[clave] == destino:
                raise ValueError(
                    f"Línea {num_linea}: transición duplicada "
                    f"({origen}, {simbolo}) -> {destino}."
                )
            raise ValueError(
                f"Línea {num_linea}: la transición ({origen}, {simbolo}) "
                f"tiene más de un destino; corresponde a un AFND y no a un AFD."
            )
        afd.agregar_transicion(origen, simbolo, destino)

    # Validaciones básicas después de la construcción.
    if not afd.Q:
        raise ValueError("No se definieron estados (Q).")
    if not afd.Sigma:
        raise ValueError("No se definió el alfabeto (Σ).")
    if afd.q0 is None:
        raise ValueError("No se definió el estado inicial (q0).")

    return afd


def cargar_manual_afnd():
    """Solicita por consola los cinco componentes y transiciones de un AFND."""
    print("\n--- CREACIÓN MANUAL DE AFND ---")
    afnd = AFND(input("Nombre o identificador del autómata: ").strip())

    while True:
        texto = input("Ingrese los estados (separados por comas): ").strip()
        estados = [e.strip() for e in texto.split(",") if e.strip()]
        duplicados = {e for e in estados if estados.count(e) > 1}
        if not estados:
            print("Debe ingresar al menos un estado.")
        elif duplicados:
            print(f"Error: estados duplicados: {sorted(duplicados)}. Intente de nuevo.")
        else:
            afnd.Q = set(estados)
            break

    while True:
        texto = input("Ingrese el alfabeto (símbolos separados por comas): ").strip()
        simbolos = [s.strip() for s in texto.split(",") if s.strip()]
        duplicados = {s for s in simbolos if simbolos.count(s) > 1}
        if not simbolos:
            print("Debe ingresar al menos un símbolo.")
        elif duplicados:
            print(f"Error: símbolos duplicados: {sorted(duplicados)}. Intente de nuevo.")
        elif any(es_epsilon(s) for s in simbolos):
            print("Error: ε no puede formar parte del alfabeto de un AFND.")
        elif any(len(s) != 1 for s in simbolos):
            print("Error: cada símbolo del alfabeto debe tener un solo carácter.")
        else:
            afnd.Sigma = set(simbolos)
            break

    while True:
        q0 = input("Ingrese el estado inicial: ").strip()
        if q0 in afnd.Q:
            afnd.q0 = q0
            break
        print(f"Error: '{q0}' no está en el conjunto de estados. Intente de nuevo.")

    while True:
        texto = input("Ingrese los estados finales (separados por comas): ").strip()
        if not texto:
            afnd.F = set()
            break
        finales = [f.strip() for f in texto.split(",") if f.strip()]
        duplicados = {f for f in finales if finales.count(f) > 1}
        if duplicados:
            print(f"Error: estados finales duplicados: {sorted(duplicados)}. Intente de nuevo.")
        elif not set(finales).issubset(afnd.Q):
            print("Error: uno o más estados finales no pertenecen a Q. Intente de nuevo.")
        else:
            afnd.F = set(finales)
            break

    # CORRECCIÓN: '|' queda excluido de origen y símbolo (igual que en archivo).
    patron = re.compile(
        r"([^,\s|]+)\s*,\s*([^,\s|]+)\s*,\s*(∅|[^,\s|]+(?:\s*\|\s*[^,\s|]+)*)"
    )
    print("\nIngrese transiciones: origen, símbolo, destino1|destino2")
    print("Use ∅ para indicar ausencia de destinos y 'fin' para terminar.")
    while True:
        linea = input("Transición: ").strip()
        if linea.lower() == "fin":
            break
        coincidencia = patron.fullmatch(linea)
        if not coincidencia:
            print("Formato incorrecto. Debe ser: origen, símbolo, destino(s)")
            continue
        origen, simbolo, destinos_str = coincidencia.groups()
        if origen not in afnd.Q:
            print(f"Error: '{origen}' no está en Q.")
            continue
        if es_epsilon(simbolo) or es_epsilon(destinos_str):
            print("Error: las transiciones ε no están permitidas.")
            continue
        if simbolo not in afnd.Sigma:
            print(f"Error: '{simbolo}' no está en Σ.")
            continue
        if destinos_str == "∅":
            destinos = set()
        else:
            lista_destinos = [d.strip() for d in destinos_str.split("|")]
            if any(es_epsilon(d) for d in lista_destinos):
                print("Error: las transiciones ε no están permitidas.")
                continue
            destinos = set(lista_destinos)
            invalidos = destinos - afnd.Q
            if invalidos:
                print(f"Error: destinos no declarados en Q: {sorted(invalidos)}")
                continue
        afnd.agregar_transicion(origen, simbolo, destinos)
        print("Transición agregada.")

    return afnd


def cargar_desde_archivo_afnd(ruta_archivo):
    """Carga un AFND con regex, primero sintaxis y luego semántica."""
    if not str(ruta_archivo).lower().endswith(".txt"):
        raise ValueError("Solo se permiten archivos .txt.")

    elemento = r"[^,\s|]+"
    lista = rf"({elemento}(?:\s*,\s*{elemento})*)"
    patrones = {
        "NOMBRE": re.compile(r"NOMBRE\s*=\s*(\S+)\s*", re.IGNORECASE),
        "TIPO": re.compile(r"TIPO\s*=\s*(AFND)\s*", re.IGNORECASE),
        "ESTADOS": re.compile(rf"ESTADOS\s*=\s*{lista}\s*", re.IGNORECASE),
        "ALFABETO": re.compile(rf"ALFABETO\s*=\s*{lista}\s*", re.IGNORECASE),
        "INICIAL": re.compile(rf"INICIAL\s*=\s*({elemento})\s*", re.IGNORECASE),
        "FINALES": re.compile(
            rf"FINALES\s*=\s*({elemento}(?:\s*,\s*{elemento})*)?\s*",
            re.IGNORECASE
        ),
        "TRANSICIONES": re.compile(r"TRANSICIONES\s*:\s*", re.IGNORECASE)
    }
    patron_transicion = re.compile(
        rf"({elemento})\s*,\s*({elemento})\s*,\s*(∅|{elemento}(?:\s*\|\s*{elemento})*)"
    )
    encontrados = set()
    valores = {}
    transiciones = []
    modo_transiciones = False

    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            lineas = archivo.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise Exception(f"Error al leer el archivo: {e}")

    # Primera etapa: reconocer líneas completas y guardar datos temporales.
    for num_linea, linea_raw in enumerate(lineas, start=1):
        linea = linea_raw.strip()
        if not linea:
            continue
        seccion = None
        coincidencia = None
        for nombre, patron in patrones.items():
            resultado = patron.fullmatch(linea)
            if resultado:
                seccion = nombre
                coincidencia = resultado
                break
        if seccion:
            if seccion in encontrados:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: la sección {seccion} está repetida."
                )
            if modo_transiciones:
                raise SyntaxError(
                    f"Error de sintaxis en línea {num_linea}: no se permiten secciones "
                    "después de TRANSICIONES."
                )
            encontrados.add(seccion)
            if seccion == "TRANSICIONES":
                modo_transiciones = True
            else:
                valores[seccion] = (coincidencia.group(1), num_linea)
            continue
        if modo_transiciones:
            coincidencia = patron_transicion.fullmatch(linea)
            if not coincidencia:
                raise SyntaxError(f"Error de sintaxis en línea {num_linea}: '{linea}'")
            transiciones.append((num_linea,) + coincidencia.groups())
            continue
        raise SyntaxError(f"Error de sintaxis en línea {num_linea}: '{linea}'")

    faltantes = set(patrones) - encontrados
    if faltantes:
        raise ValueError(f"Faltan las siguientes secciones: {', '.join(sorted(faltantes))}.")

    # Segunda etapa: construir conjuntos y comprobar relaciones semánticas.
    afnd = AFND(valores["NOMBRE"][0])
    estados_str, linea_estados = valores["ESTADOS"]
    estados = [e.strip() for e in estados_str.split(",")]
    duplicados = {e for e in estados if estados.count(e) > 1}
    if duplicados:
        raise ValueError(f"Línea {linea_estados}: estados duplicados: {sorted(duplicados)}.")
    afnd.Q = set(estados)

    sigma_str, linea_sigma = valores["ALFABETO"]
    sigma = [s.strip() for s in sigma_str.split(",")]
    duplicados = {s for s in sigma if sigma.count(s) > 1}
    if duplicados:
        raise ValueError(f"Línea {linea_sigma}: símbolos duplicados: {sorted(duplicados)}.")
    if any(es_epsilon(s) for s in sigma):
        raise ValueError(f"Línea {linea_sigma}: ε no puede formar parte del alfabeto de un AFND.")
    if any(len(s) != 1 for s in sigma):
        raise ValueError(
            f"Línea {linea_sigma}: cada símbolo del alfabeto debe tener un solo carácter."
        )
    afnd.Sigma = set(sigma)

    q0, linea_inicial = valores["INICIAL"]
    if q0 not in afnd.Q:
        raise ValueError(f"Línea {linea_inicial}: el estado inicial '{q0}' no pertenece a Q.")
    afnd.q0 = q0

    finales_str, linea_finales = valores["FINALES"]
    finales = [] if not finales_str else [f.strip() for f in finales_str.split(",")]
    duplicados = {f for f in finales if finales.count(f) > 1}
    if duplicados:
        raise ValueError(
            f"Línea {linea_finales}: estados finales duplicados: {sorted(duplicados)}."
        )
    invalidos = sorted(set(finales) - afnd.Q)
    if invalidos:
        raise ValueError(
            f"Línea {linea_finales}: estados finales que no pertenecen a Q: {invalidos}."
        )
    afnd.F = set(finales)

    for num_linea, origen, simbolo, destinos_str in transiciones:
        if origen not in afnd.Q:
            raise ValueError(f"Línea {num_linea}: el estado origen '{origen}' no pertenece a Q.")
        if es_epsilon(simbolo) or es_epsilon(destinos_str):
            raise ValueError(f"Línea {num_linea}: las transiciones ε no están permitidas.")
        if simbolo not in afnd.Sigma:
            raise ValueError(f"Línea {num_linea}: el símbolo '{simbolo}' no pertenece al alfabeto.")
        if destinos_str == "∅":
            destinos = set()
        else:
            lista_destinos = [d.strip() for d in destinos_str.split("|")]
            if any(es_epsilon(d) for d in lista_destinos):
                raise ValueError(
                    f"Línea {num_linea}: las transiciones ε no están permitidas."
                )
            destinos = set(lista_destinos)
            invalidos = sorted(destinos - afnd.Q)
            if invalidos:
                raise ValueError(
                    f"Línea {num_linea}: estados destino que no pertenecen a Q: {invalidos}."
                )
        afnd.agregar_transicion(origen, simbolo, destinos)

    return afnd

def cargar_manual_pda():
    print("\n--- CREACIÓN MANUAL DE APD/APND ---")
    tipo = ""
    while tipo not in ("APD", "APND"):
        tipo = input("Tipo de autómata (APD/APND): ").strip().upper()
        if tipo not in ("APD", "APND"):
            print("Debe ser APD o APND.")

    nombre = input("Nombre o identificador: ").strip()
    pda = PDA(nombre, tipo)

    while True:
        texto = input("Estados (separados por coma): ").strip()
        estados = [e.strip() for e in texto.split(",") if e.strip()]
        if not estados:
            print("Debe haber al menos un estado.")
        elif len(estados) != len(set(estados)):
            print("Hay estados duplicados.")
        else:
            pda.Q = set(estados)
            break

    while True:
        texto = input("Alfabeto de entrada Σ: ").strip()
        sigma = [s.strip() for s in texto.split(",") if s.strip()]
        if not sigma:
            print("Debe haber al menos un símbolo.")
        elif len(sigma) != len(set(sigma)):
            print("Hay símbolos duplicados.")
        elif "EPS" in sigma:
            print("EPS no puede estar en Σ.")
        elif any(len(s) != 1 for s in sigma):
            print("Cada símbolo de entrada debe tener un solo carácter.")
        else:
            pda.Sigma = set(sigma)
            break

    while True:
        texto = input("Alfabeto de pila Γ: ").strip()
        gamma = [g.strip() for g in texto.split(",") if g.strip()]
        if not gamma:
            print("Debe haber al menos un símbolo.")
        elif len(gamma) != len(set(gamma)):
            print("Hay símbolos duplicados.")
        elif "EPS" in gamma:
            print("EPS no puede estar en Γ.")
        else:
            pda.Gamma = set(gamma)
            break

    while True:
        q0 = input("Estado inicial: ").strip()
        if q0 in pda.Q:
            pda.q0 = q0
            break
        print(f"'{q0}' no está en Q.")

    while True:
        z0 = input("Símbolo inicial de pila Z0: ").strip()
        if z0 in pda.Gamma:
            pda.Z0 = z0
            break
        print(f"'{z0}' no está en Γ.")

    while True:
        texto = input("Estados finales (coma, vacío si no hay): ").strip()
        if not texto:
            pda.F = set()
            break
        finales = [f.strip() for f in texto.split(",") if f.strip()]
        if len(finales) != len(set(finales)):
            print("Hay estados finales duplicados.")
        elif any(f not in pda.Q for f in finales):
            print("Algún estado final no está en Q.")
        else:
            pda.F = set(finales)
            break

    print("\nIngrese transiciones. Formato:")
    print("  estado,entrada,tope,destino,reemplazo")
    print("  - EPS para épsilon")
    print("  - Reemplazo con ; (ej: A;Z0). Primer símbolo = nuevo tope.")
    print("  - Alternativas con | (ej: q0,a,Z0,q1,A|q2,EPS)")
    print("  - Escriba 'fin' para terminar\n")

    while True:
        linea = input("Transición: ").strip()
        if linea.lower() == "fin":
            break
        try:
            trans = parsear_linea_transicion_pda(linea)
        except ValueError as e:
            print(f"Formato inválido: {e}")
            continue

        errores = []
        for (o, s, t, d, r) in trans:
            errores += validar_pda_transicion_individual(pda, o, s, t, d, r)
        if errores:
            for e in errores:
                print(f"  - {e}")
            continue

        for (o, s, t, d, r) in trans:
            pda.agregar_transicion(o, s, t, d, r)
        print(f"Se agregaron {len(trans)} transición(es).")

    errores = validar_pda(pda)
    if errores:
        raise ValueError("Autómata inválido:\n  " + "\n  ".join(errores))
    print("\n✅ Autómata válido.")
    return pda

# ========================== SIMULACIÓN APD / APND ==========================
def _aplicar_transicion(pila, reemplazo):
    """Desapila el tope y empuja el reemplazo (índice 0 = nuevo tope)."""
    nueva = list(pila[:-1])
    for sym in reversed(reemplazo):
        nueva.append(sym)
    return nueva


def simular_apd(pda, cadena, max_pasos=10000):
    for s in cadena:
        if s not in pda.Sigma:
            raise ValueError(f"Símbolo '{s}' no pertenece a Σ.")

    estado = pda.q0
    pos = 0
    pila = [pda.Z0]
    traza = []
    visitadas = set()

    for paso in range(1, max_pasos + 1):
        config = (estado, pos, tuple(pila))
        if config in visitadas:
            return {"aceptada": False, "traza": traza,
                    "motivo": "ciclo de configuraciones detectado",
                    "estado_final": estado, "pila_final": pila}
        visitadas.add(config)

        if pos >= len(cadena) and estado in pda.F:
            return {"aceptada": True, "traza": traza,
                    "estado_final": estado, "pila_final": pila}

        if not pila:
            return {"aceptada": False, "traza": traza,
                    "motivo": "pila vacía",
                    "estado_final": estado, "pila_final": pila}

        tope = pila[-1]
        elegida = None
        if pos < len(cadena):
            clave = (estado, cadena[pos], tope)
            if clave in pda.delta:
                d, r = pda.delta[clave][0]
                elegida = (cadena[pos], True, d, r, clave)
        if elegida is None:
            clave = (estado, "EPS", tope)
            if clave in pda.delta:
                d, r = pda.delta[clave][0]
                elegida = ("EPS", False, d, r, clave)

        if elegida is None:
            return {"aceptada": False, "traza": traza,
                    "motivo": "sin transición aplicable",
                    "estado_final": estado, "pila_final": pila}

        simbolo, consume, destino, reempl, _ = elegida
        pila_antes = list(pila)
        nueva_pila = _aplicar_transicion(pila, reempl)

        traza.append({
            "paso": paso, "rama": "única",
            "estado_antes": estado, "pos_antes": pos,
            "entrada_restante": cadena[pos:],
            "pila_antes": pila_antes, "simbolo": simbolo,
            "tope": tope, "destino": destino,
            "reemplazo": list(reempl),
            "pila_despues": nueva_pila,
        })
        estado, pila = destino, nueva_pila
        if consume:
            pos += 1

    # El último paso también puede haber llegado a aceptación o a una parada normal.
    if pos >= len(cadena) and estado in pda.F:
        return {"aceptada": True, "traza": traza,
                "estado_final": estado, "pila_final": pila}
    if (estado, pos, tuple(pila)) in visitadas:
        return {"aceptada": False, "traza": traza,
                "motivo": "ciclo de configuraciones detectado",
                "estado_final": estado, "pila_final": pila}
    if not pila or ((pos >= len(cadena) or (estado, cadena[pos], pila[-1]) not in pda.delta)
                    and (estado, "EPS", pila[-1]) not in pda.delta):
        return {"aceptada": False, "traza": traza,
                "motivo": "sin transición aplicable",
                "estado_final": estado, "pila_final": pila}
    return {"aceptada": False, "traza": traza,
            "motivo": "límite de pasos excedido",
            "estado_final": estado, "pila_final": pila, "limite": True}


def simular_apnd(pda, cadena, max_pasos=5000, max_nodos=2000):
    for s in cadena:
        if s not in pda.Sigma:
            raise ValueError(f"Símbolo '{s}' no pertenece a Σ.")

    contador = [0]
    def _nuevo_id():
        contador[0] += 1
        return contador[0]

    raiz = {
        "id": _nuevo_id(), "parent": None,
        "paso": 0,
        "estado": pda.q0, "pos": 0, "pila": (pda.Z0,),
        "trans": None,
        "acepta": pda.q0 in pda.F and len(cadena) == 0,
        "hijos": [],
    }
    nodos = [raiz]
    cola = [raiz]
    visitadas = {(pda.q0, 0, (pda.Z0,))}
    aceptados = [raiz] if raiz["acepta"] else []
    pasos = 0
    limite = False

    while cola:
        nodo = cola.pop(0)
        if not nodo["pila"]:
            continue
        estado, pos, pila = nodo["estado"], nodo["pos"], nodo["pila"]
        tope = pila[-1]
        alternativas = []

        if pos < len(cadena):
            for d, r in pda.delta.get((estado, cadena[pos], tope), []):
                alternativas.append((cadena[pos], True, d, r))
        for d, r in pda.delta.get((estado, "EPS", tope), []):
            alternativas.append(("EPS", False, d, r))

        if len(alternativas) > 1:
            nodo["bifurcacion"] = len(alternativas)

        for simbolo, consume, destino, reempl in alternativas:
            nueva_pila = tuple(_aplicar_transicion(pila, reempl))
            nueva_pos = pos + 1 if consume else pos
            config = (destino, nueva_pos, nueva_pila)
            if pasos >= max_pasos or len(nodos) >= max_nodos:
                limite = True
                break
            repetida = config in visitadas
            if not repetida:
                visitadas.add(config)

            hijo = {
                "id": _nuevo_id(), "parent": nodo["id"],
                "paso": nodo["paso"] + 1,
                "estado": destino, "pos": nueva_pos, "pila": nueva_pila,
                "repetida": repetida,
                "trans": {"simbolo": simbolo, "tope": tope,
                          "reemplazo": tuple(reempl)},
                "acepta": nueva_pos >= len(cadena) and destino in pda.F,
                "hijos": [],
            }
            nodo["hijos"].append(hijo["id"])
            nodos.append(hijo)
            # Se muestra la rama repetida, pero no se procesa otra vez.
            if not repetida:
                cola.append(hijo)
            pasos += 1
            if hijo["acepta"]:
                aceptados.append(hijo)
        if limite:
            break

    return {
        "aceptada": len(aceptados) > 0,
        "nodos": nodos,
        "aceptados": aceptados,
        "limite": limite,
    }


def _str_pila(pila):
    return "[" + (" ".join(pila) if pila else "vacía") + "]"


def imprimir_traza_pda(pda, cadena, resultado):
    cadena_mostrada = "ε" if cadena == "" else f"'{cadena}'"
    print("\n" + "=" * 72)
    print(f"SIMULACIÓN {pda.tipo} - Cadena: {cadena_mostrada}")
    print("=" * 72)

    if pda.tipo == "APD":
        if not resultado["traza"]:
            print("(No se ejecutó ninguna transición.)")
        for p in resultado["traza"]:
            print(f"\nPaso {p['paso']}:")
            print(f"  Estado actual: {p['estado_antes']}  |  Entrada restante: '{p['entrada_restante']}'")
            print(f"  Pila antes: {_str_pila(p['pila_antes'])}  (tope a la derecha)")
            if p["simbolo"] == "EPS":
                print(f"  Transición EPS")
            else:
                print(f"  Símbolo procesado: '{p['simbolo']}'")
            reempl = ";".join(p["reemplazo"]) if p["reemplazo"] else "EPS"
            print(f"  Tope leído: {p['tope']}  |  Destino: {p['destino']}  |  Reemplazo: {reempl}")
            print(f"  Pila después: {_str_pila(p['pila_despues'])}")

        print(f"\nEstado final: {resultado['estado_final']}  |  Pila final: {_str_pila(resultado['pila_final'])}")
        # CORRECCIÓN: el límite de pasos no es un rechazo definitivo.
        if resultado["aceptada"]:
            print("VEREDICTO: ACEPTADA ✅")
        elif resultado.get("limite"):
            print("VEREDICTO: INDETERMINADO ⚠️  (límite de pasos excedido)")
        else:
            print(f"VEREDICTO: RECHAZADA ❌  ({resultado.get('motivo', '')})")
        return

    # APND
    nodos = resultado["nodos"]
    nodos_por_id = {nodo["id"]: nodo for nodo in nodos}
    print(f"\nConfiguraciones exploradas: {len(nodos)}")
    limite_display = 80
    for nodo in nodos[:limite_display]:
        if nodo["parent"] is None:
            print(f"\nPaso 0 | Rama {nodo['id']} INICIAL  estado={nodo['estado']}")
            print(f"  Entrada restante: '{cadena}'  |  Pila inicial: {_str_pila(nodo['pila'])}")
        else:
            padre = nodos_por_id[nodo["parent"]]
            t = nodo["trans"]
            reempl = ";".join(t["reemplazo"]) if t["reemplazo"] else "EPS"
            etiqueta = "EPS" if t["simbolo"] == "EPS" else f"'{t['simbolo']}'"
            print(f"\nPaso {nodo['paso']} | Rama {nodo['id']} (desde rama {nodo['parent']})")
            print(f"  Estado anterior: {padre['estado']}  |  Entrada restante: '{cadena[padre['pos']:]}'")
            print(f"  Pila antes: {_str_pila(padre['pila'])}")
            print(f"  Transición: {etiqueta}  |  tope={t['tope']} -> destino={nodo['estado']}, reemplazo={reempl}")
            print(f"  Estado destino: {nodo['estado']}  |  Entrada restante después: '{cadena[nodo['pos']:]}'")
            print(f"  Pila después: {_str_pila(nodo['pila'])}")
            if nodo.get("repetida"):
                print("  Configuración repetida: esta rama no se explora otra vez.")
        if nodo.get("bifurcacion"):
            print(f"  ↳ Se detectaron {nodo['bifurcacion']} alternativas desde esta rama.")
        if nodo["acepta"]:
            print("  *** ACEPTA ***")
    if len(nodos) > limite_display:
        print(f"\n(Se muestran solo los primeros {limite_display} nodos.)")

    # CORRECCIÓN: veredicto único y coherente con el límite de exploración.
    if resultado["aceptada"]:
        print("\n--- CAMINO DE ACEPTACIÓN ---")
        acc = resultado["aceptados"][0]
        camino = []
        actual = acc
        while actual is not None:
            camino.append(actual)
            if actual["parent"] is None:
                actual = None
            else:
                actual = next(n for n in nodos if n["id"] == actual["parent"])
        camino.reverse()
        for n in camino:
            print(f"  [{n['id']}] estado={n['estado']}  pos={n['pos']}  pila={_str_pila(n['pila'])}"
                  + ("  (ACEPTA)" if n["acepta"] else ""))
        print("\nVEREDICTO: ACEPTADA ✅")
    elif resultado.get("limite"):
        print("\nVEREDICTO: INDETERMINADO ⚠️")
        print("Se alcanzó el límite de exploración; no se puede afirmar que la cadena sea rechazada.")
    else:
        print("\nVEREDICTO: RECHAZADA ❌")


def validar_pda_transicion_individual(pda, origen, simbolo, tope, destino, reemplazo):
    errs = []
    if origen not in pda.Q:
        errs.append(f"Origen '{origen}' no en Q.")
    if simbolo != "EPS" and simbolo not in pda.Sigma:
        errs.append(f"Entrada '{simbolo}' no en Σ ni EPS.")
    if tope == "EPS":
        errs.append("El tope de pila no puede ser EPS.")
    elif tope not in pda.Gamma:
        errs.append(f"Tope '{tope}' no en Γ.")
    if destino not in pda.Q:
        errs.append(f"Destino '{destino}' no en Q.")
    for sym in reemplazo:
        if sym not in pda.Gamma:
            errs.append(f"Símbolo '{sym}' del reemplazo no en Γ.")
    return errs


def cargar_desde_archivo_pda(ruta):
    if not str(ruta).lower().endswith(".txt"):
        raise ValueError("Solo se permiten archivos .txt.")

    elemento = r"[^,\s|;]+"
    lista = rf"({elemento}(?:\s*,\s*{elemento})*)"
    patrones = {
        "NOMBRE": re.compile(r"NOMBRE\s*=\s*(\S+)\s*", re.IGNORECASE),
        "TIPO": re.compile(r"TIPO\s*=\s*(APD|APND)\s*", re.IGNORECASE),
        "ESTADOS": re.compile(rf"ESTADOS\s*=\s*{lista}\s*", re.IGNORECASE),
        "ALFABETO": re.compile(rf"ALFABETO\s*=\s*{lista}\s*", re.IGNORECASE),
        "ALFABETO_PILA": re.compile(rf"ALFABETO_PILA\s*=\s*{lista}\s*", re.IGNORECASE),
        "INICIAL": re.compile(rf"INICIAL\s*=\s*({elemento})\s*", re.IGNORECASE),
        "INICIAL_PILA": re.compile(rf"INICIAL_PILA\s*=\s*({elemento})\s*", re.IGNORECASE),
        "FINALES": re.compile(rf"FINALES\s*=\s*({elemento}(?:\s*,\s*{elemento})*)?\s*", re.IGNORECASE),
        "TRANSICIONES": re.compile(r"TRANSICIONES\s*:\s*", re.IGNORECASE),
    }

    valores = {}
    transiciones_raw = []
    modo_trans = False

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            lineas = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")
    except Exception as e:
        raise Exception(f"Error al leer el archivo: {e}")

    for num, raw in enumerate(lineas, start=1):
        linea = raw.strip()
        if not linea:
            continue

        seccion, match = None, None
        for nombre, pat in patrones.items():
            m = pat.fullmatch(linea)
            if m:
                seccion, match = nombre, m
                break

        if seccion:
            if seccion in valores:
                raise SyntaxError(f"Línea {num}: sección {seccion} repetida.")
            if modo_trans and seccion != "TRANSICIONES":
                raise SyntaxError(f"Línea {num}: no se permiten secciones después de TRANSICIONES.")
            if seccion == "TRANSICIONES":
                modo_trans = True
                valores[seccion] = (None, num)
            else:
                valores[seccion] = (match.group(1) if match.groups() else None, num)
            continue

        if modo_trans:
            transiciones_raw.append((num, linea))
            continue

        raise SyntaxError(f"Línea {num}: '{linea}' no corresponde a ninguna sección.")

    requeridas = {"NOMBRE", "TIPO", "ESTADOS", "ALFABETO", "ALFABETO_PILA",
                  "INICIAL", "INICIAL_PILA", "FINALES", "TRANSICIONES"}
    faltan = requeridas - set(valores)
    if faltan:
        raise ValueError(f"Faltan secciones: {sorted(faltan)}.")

    tipo = valores["TIPO"][0].upper()
    pda = PDA(valores["NOMBRE"][0], tipo)

    def _lista(valor, num, campo):
        if valor is None:
            raise ValueError(f"Línea {num}: {campo} no puede estar vacío.")
        items = [x.strip() for x in valor.split(",") if x.strip()]
        if len(items) != len(set(items)):
            raise ValueError(f"Línea {num}: {campo} tiene duplicados.")
        return items

    pda.Q = set(_lista(*valores["ESTADOS"], "ESTADOS"))
    pda.Sigma = set(_lista(*valores["ALFABETO"], "ALFABETO"))
    pda.Gamma = set(_lista(*valores["ALFABETO_PILA"], "ALFABETO_PILA"))

    if "EPS" in pda.Sigma:
        raise ValueError("EPS no puede pertenecer a Σ.")
    if "EPS" in pda.Gamma:
        raise ValueError("EPS no puede pertenecer a Γ.")
    if any(len(s) != 1 for s in pda.Sigma):
        linea_sigma = valores["ALFABETO"][1]
        raise ValueError(
            f"Línea {linea_sigma}: cada símbolo de entrada debe tener un solo carácter."
        )

    q0, l_q0 = valores["INICIAL"]
    if q0 not in pda.Q:
        raise ValueError(f"Línea {l_q0}: INICIAL '{q0}' no en Q.")
    pda.q0 = q0

    z0, l_z0 = valores["INICIAL_PILA"]
    if z0 not in pda.Gamma:
        raise ValueError(f"Línea {l_z0}: INICIAL_PILA '{z0}' no en Γ.")
    pda.Z0 = z0

    finales_str, l_fin = valores["FINALES"]
    if finales_str is None:
        finales = []
    else:
        finales = [f.strip() for f in finales_str.split(",") if f.strip()]
        if len(finales) != len(set(finales)):
            raise ValueError(f"Línea {l_fin}: estados finales duplicados.")
        invalidos = [f for f in finales if f not in pda.Q]
        if invalidos:
            raise ValueError(f"Línea {l_fin}: estados finales fuera de Q: {invalidos}.")
    pda.F = set(finales)

    for num, linea in transiciones_raw:
        try:
            trans = parsear_linea_transicion_pda(linea)
        except ValueError as e:
            raise ValueError(f"Línea {num}: {e}")
        for (o, s, t, d, r) in trans:
            errs = validar_pda_transicion_individual(pda, o, s, t, d, r)
            if errs:
                raise ValueError(f"Línea {num}: " + " ".join(errs))
            pda.agregar_transicion(o, s, t, d, r)

    errores = validar_pda(pda)
    if errores:
        raise ValueError("Autómata inválido:\n  " + "\n  ".join(errores))

    return pda


# ========================== VALIDACIÓN Y ANÁLISIS ESTRUCTURAL ==========================
def validar_afd(afd):
    """
    Verifica la integridad del AFD:
    - q0 ∈ Q
    - F ⊆ Q
    - Transiciones consistentes
    - Determinismo: exactamente una transición por par (estado, símbolo)
    Retorna una lista de errores (vacía si todo es correcto).
    """
    errores = []

    if afd.q0 not in afd.Q:
        errores.append(f"El estado inicial '{afd.q0}' no pertenece a Q.")

    if not afd.F.issubset(afd.Q):
        no_pertenecen = afd.F - afd.Q
        errores.append(f"Los siguientes estados finales no pertenecen a Q: {no_pertenecen}")

    if any(len(s) != 1 for s in afd.Sigma):
        errores.append("Cada símbolo del alfabeto debe tener un solo carácter.")

    for (origen, simbolo), destino in afd.delta.items():
        # Epsilon convertiría la transición en una característica de un AFND-ε.
        if simbolo.casefold() in {"ε", "epsilon"}:
            errores.append("Un AFD no permite transiciones ε.")
        if origen not in afd.Q:
            errores.append(f"En transición ({origen}, {simbolo}) -> {destino}: origen no está en Q.")
        if simbolo not in afd.Sigma:
            errores.append(f"En transición ({origen}, {simbolo}) -> {destino}: símbolo no está en Σ.")
        if destino not in afd.Q:
            errores.append(f"En transición ({origen}, {simbolo}) -> {destino}: destino no está en Q.")

    # Determinismo: verificar que exista transición para cada par
    for estado in afd.Q:
        for simbolo in afd.Sigma:
            if (estado, simbolo) not in afd.delta:
                errores.append(f"Falta transición para el par ({estado}, {simbolo}).")

    return errores


def validar_afnd(afnd):
    """Valida la integridad de un AFND sin exigir una transición por cada par."""
    errores = []
    if afnd.q0 not in afnd.Q:
        errores.append(f"El estado inicial '{afnd.q0}' no pertenece a Q.")
    if not afnd.F.issubset(afnd.Q):
        errores.append(f"Estados finales fuera de Q: {sorted(afnd.F - afnd.Q)}.")
    if any(es_epsilon(s) for s in afnd.Sigma):
        errores.append("ε no puede formar parte del alfabeto de un AFND.")
    if any(len(s) != 1 for s in afnd.Sigma):
        errores.append("Cada símbolo del alfabeto debe tener un solo carácter.")
    for (origen, simbolo), destinos in afnd.delta.items():
        if origen not in afnd.Q:
            errores.append(f"En ({origen}, {simbolo}): el origen no pertenece a Q.")
        if es_epsilon(simbolo):
            errores.append("Las transiciones ε no están permitidas.")
        elif simbolo not in afnd.Sigma:
            errores.append(f"En ({origen}, {simbolo}): el símbolo no pertenece a Σ.")
        invalidos = destinos - afnd.Q
        if invalidos:
            errores.append(
                f"En ({origen}, {simbolo}): destinos fuera de Q: {sorted(invalidos)}."
            )
    return errores

def validar_pda(pda):
    """
    Reglas:
      - q0 ∈ Q, F ⊆ Q, Z0 ∈ Γ.
      - EPS no pertenece a Σ ni a Γ.
      - Símbolos de entrada ∈ Σ ∪ {EPS}; tope ∈ Γ; reemplazo ⊆ Γ.
      - Si TIPO=APD: máximo 1 transición por (q, s, tope) y sin conflicto EPS
        con transiciones que consumen Σ para la misma (q, tope).
    """
    errores = []

    if pda.tipo not in ("APD", "APND"):
        errores.append(f"TIPO inválido: '{pda.tipo}' (debe ser APD o APND).")

    if pda.q0 not in pda.Q:
        errores.append(f"El estado inicial '{pda.q0}' no pertenece a Q.")
    if not pda.F.issubset(pda.Q):
        errores.append(f"Estados finales fuera de Q: {sorted(pda.F - pda.Q)}.")
    if pda.Z0 not in pda.Gamma:
        errores.append(f"El símbolo inicial de pila '{pda.Z0}' no pertenece a Γ.")
    if "EPS" in pda.Sigma:
        errores.append("EPS no puede pertenecer a Σ.")
    if "EPS" in pda.Gamma:
        errores.append("EPS no puede pertenecer a Γ.")
    if any(len(s) != 1 for s in pda.Sigma):
        errores.append("Cada símbolo de entrada debe tener un solo carácter.")

    for (origen, simbolo, tope), alts in pda.delta.items():
        if origen not in pda.Q:
            errores.append(f"({origen},{simbolo},{tope}): origen no en Q.")
        if simbolo != "EPS" and simbolo not in pda.Sigma:
            errores.append(f"({origen},{simbolo},{tope}): símbolo de entrada no válido.")
        if tope == "EPS":
            errores.append(f"({origen},{simbolo},{tope}): el tope no puede ser EPS.")
        elif tope not in pda.Gamma:
            errores.append(f"({origen},{simbolo},{tope}): tope no está en Γ.")
        for destino, reempl in alts:
            if destino not in pda.Q:
                errores.append(f"({origen},{simbolo},{tope}): destino '{destino}' no en Q.")
            for sym in reempl:
                if sym not in pda.Gamma:
                    errores.append(f"({origen},{simbolo},{tope}): símbolo de reemplazo '{sym}' no en Γ.")

    if pda.tipo == "APD":
        for clave, alts in pda.delta.items():
            if len(alts) > 1:
                errores.append(f"APD no determinista: hay {len(alts)} transiciones para {clave}.")
        for (origen, simbolo, tope), _ in pda.delta.items():
            if simbolo == "EPS":
                for (o2, s2, t2) in pda.delta:
                    if o2 == origen and t2 == tope and s2 != "EPS":
                        errores.append(
                            f"APD con conflicto EPS en ({origen}, {tope}): "
                            f"coexiste EPS con '{s2}'."
                        )
                        break

    return errores

def tabla_transiciones_pda(pda):
    """
    Filas: (estado, tope).
    Columnas: símbolos de Σ + columna EPS si hay transiciones EPS.
    """
    # Incluye todos los pares Q × Γ, aun cuando no tengan transición.
    pares = [(estado, tope) for estado in sorted(pda.Q)
             for tope in sorted(pda.Gamma)]
    hay_eps = any(s == "EPS" for (_, s, _) in pda.delta)

    columnas = sorted(pda.Sigma)
    if hay_eps:
        columnas.append("EPS")

    filas = []
    for (estado, tope) in pares:
        fila = [f"({estado}, {tope})"]
        for col in columnas:
            alts = pda.delta.get((estado, col, tope), [])
            if alts:
                celdas = []
                for destino, reempl in alts:
                    r = ";".join(reempl) if reempl else "EPS"
                    celdas.append(f"({destino}, {r})")
                fila.append(" | ".join(celdas))
            else:
                fila.append("-")
        filas.append(fila)

    header = ["(Estado, Tope)"] + columnas
    return header, filas


def imprimir_tabla_pda(pda):
    header, filas = tabla_transiciones_pda(pda)
    print(f"\n--- TABLA DE TRANSICIÓN ({pda.tipo}) ---")

    # Ancho de cada columna
    anchos = [len(h) for h in header]
    for fila in filas:
        for i, celda in enumerate(fila):
            anchos[i] = max(anchos[i], len(str(celda)))

    def linea_sep():
        return "-+-".join("-" * a for a in anchos)

    print(" | ".join(h.ljust(anchos[i]) for i, h in enumerate(header)))
    print(linea_sep())
    for fila in filas:
        print(" | ".join(str(c).ljust(anchos[i]) for i, c in enumerate(fila)))


def convertir_afnd_a_afd(afnd):
    """Convierte un AFND a AFD mediante construcción manual de subconjuntos."""
    errores = validar_afnd(afnd)
    if errores:
        raise ValueError("No se puede convertir un AFND inválido.")

    subconjunto_inicial = frozenset({afnd.q0})
    nombres = {}
    pendientes = []
    procesados = set()

    def registrar(subconjunto):
        if subconjunto not in nombres:
            nombres[subconjunto] = generar_nombre_macroestado(len(nombres))
            pendientes.append(subconjunto)
        return nombres[subconjunto]

    registrar(subconjunto_inicial)
    afd = AFD(f"{afnd.nombre}_AFD")
    afd.Sigma = set(afnd.Sigma)

    while pendientes:
        macroestado = pendientes.pop(0)
        if macroestado in procesados:
            continue
        procesados.add(macroestado)
        nombre_origen = nombres[macroestado]
        afd.Q.add(nombre_origen)

        for simbolo in sorted(afnd.Sigma):
            union_destinos = set()
            for estado in macroestado:
                union_destinos.update(afnd.obtener_destinos(estado, simbolo))
            destino = frozenset(union_destinos)
            nombre_destino = registrar(destino)
            afd.delta[(nombre_origen, simbolo)] = nombre_destino

    afd.q0 = nombres[subconjunto_inicial]
    for subconjunto, nombre in nombres.items():
        afd.Q.add(nombre)
        if subconjunto.intersection(afnd.F):
            afd.F.add(nombre)

    equivalencias = {
        nombre: subconjunto for subconjunto, nombre in nombres.items()
    }
    return afd, equivalencias


def imprimir_tabla_equivalencias(equivalencias):
    """Muestra la relación entre nombres del AFD y subconjuntos del AFND."""
    print("\n--- TABLA DE EQUIVALENCIAS ---")
    print("Macroestado AFD | Estados AFND")
    print("-" * 42)
    for nombre in sorted(equivalencias):
        estados = equivalencias[nombre]
        representacion = "∅" if not estados else "{" + ",".join(sorted(estados)) + "}"
        print(f"{nombre:<15} | {representacion}")


def completar_con_estado_trampa(afd, transiciones_faltantes):
    """Completa un AFD enviando las transiciones faltantes a un estado de trampa."""
    nombre_trampa = "TRAMPA"
    numero = 1
    while nombre_trampa in afd.Q:
        nombre_trampa = f"TRAMPA_{numero}"
        numero += 1

    afd.Q.add(nombre_trampa)

    # Cada transición faltante dirige al estado de trampa.
    for estado, simbolo in transiciones_faltantes:
        afd.delta[(estado, simbolo)] = nombre_trampa

    # Una vez en el estado de trampa, cualquier símbolo permanece en él.
    for simbolo in afd.Sigma:
        afd.delta[(nombre_trampa, simbolo)] = nombre_trampa

    return nombre_trampa


def analizar_estructura(afd):
    """
    Calcula estados alcanzables, inaccesibles, finales alcanzables y si el lenguaje es vacío.
    Actualiza los atributos del objeto AFD.
    """
    if afd.q0 not in afd.Q:
        afd.estados_alcanzables = set()
        afd.estados_inaccesibles = afd.Q.copy()
        afd.finales_alcanzables = set()
        afd.lenguaje_vacio = True
        return {
            "alcanzables": set(),
            "inaccesibles": afd.Q.copy(),
            "finales_alcanzables": set(),
            "lenguaje_vacio": True
        }

    # BFS con lista (sin usar collections.deque)
    alcanzables = set()
    cola = [afd.q0]
    alcanzables.add(afd.q0)
    idx = 0
    while idx < len(cola):
        estado = cola[idx]
        idx += 1
        for simbolo in afd.Sigma:
            destino = afd.delta.get((estado, simbolo))
            if destino is not None and destino not in alcanzables:
                alcanzables.add(destino)
                cola.append(destino)

    inaccesibles = afd.Q - alcanzables
    finales_alcanzables = afd.F.intersection(alcanzables)
    lenguaje_vacio = (len(finales_alcanzables) == 0)

    afd.estados_alcanzables = alcanzables
    afd.estados_inaccesibles = inaccesibles
    afd.finales_alcanzables = finales_alcanzables
    afd.lenguaje_vacio = lenguaje_vacio

    return {
        "alcanzables": alcanzables,
        "inaccesibles": inaccesibles,
        "finales_alcanzables": finales_alcanzables,
        "lenguaje_vacio": lenguaje_vacio
    }


# ========================== SIMULACIÓN ==========================
def simular(afd, cadena):
    """
    Simula el AFD con la cadena de entrada.
    Retorna un diccionario con:
        - aceptada: bool
        - traza: lista de pasos (cada paso: estado, simbolo, destino)
        - estado_final: str
    """
    # Validar símbolos
    for simbolo in cadena:
        if simbolo not in afd.Sigma:
            raise ValueError(f"El símbolo '{simbolo}' no pertenece al alfabeto {afd.Sigma}")

    estado_actual = afd.q0
    traza = []
    for simbolo in cadena:
        destino = afd.delta.get((estado_actual, simbolo))
        if destino is None:
            raise ValueError(f"No hay transición definida para ({estado_actual}, {simbolo})")
        traza.append({
            "estado": estado_actual,
            "simbolo": simbolo,
            "destino": destino
        })
        estado_actual = destino

    aceptada = estado_actual in afd.F
    return {
        "aceptada": aceptada,
        "traza": traza,
        "estado_final": estado_actual
    }


def imprimir_traza(resultado, cadena):
    """
    Imprime en consola la traza de la simulación.
    """
    print("\n--- TRAZA DE EJECUCIÓN ---")
    cadena_mostrada = "ε" if cadena == "" else f"'{cadena}'"
    print(f"Cadena evaluada: {cadena_mostrada}")
    for i, paso in enumerate(resultado["traza"], start=1):
        print(f"Paso {i}: Estado actual: {paso['estado']}, "
              f"Símbolo: '{paso['simbolo']}', Siguiente estado: {paso['destino']}")
    print(f"Estado final: {resultado['estado_final']}")
    if resultado["aceptada"]:
        print("VEREDICTO: ACEPTADA ✅")
    else:
        print("VEREDICTO: RECHAZADA ❌")
    print("-" * 30)


# ========================== HISTORIAL ==========================
def agregar_historial(afd, cadena, resultado=None, error=None):
    """
    Agrega una evaluación o un intento inválido al historial del AFD.
    """
    if error is not None:
        entrada = {"cadena": cadena, "error": error}
    else:
        entrada = {
            "cadena": cadena,
            "aceptada": resultado["aceptada"],
            "estado_final": resultado["estado_final"],
            "traza": resultado["traza"]
        }
    afd.historial.append(entrada)


def mostrar_historial(afd):
    """
    Muestra el historial de evaluaciones.
    """
    if not afd.historial:
        print("\nNo hay evaluaciones en el historial.")
        return
    print("\n--- HISTORIAL DE EVALUACIONES ---")
    for i, entrada in enumerate(afd.historial, start=1):
        cadena_mostrada = "ε" if entrada["cadena"] == "" else f"'{entrada['cadena']}'"
        if "error" in entrada:
            print(f"{i}. Cadena: {cadena_mostrada} -> INVÁLIDA ({entrada['error']})")
        else:
            estado = "ACEPTADA ✅" if entrada["aceptada"] else "RECHAZADA ❌"
            print(f"{i}. Cadena: {cadena_mostrada} -> {estado} "
                  f"(Estado final: {entrada['estado_final']})")
    print("-" * 30)


# ========================== MENÚ PRINCIPAL ==========================
class EstadoSesion:
    def __init__(self):
        self.reiniciar()

    def reiniciar(self, incluir_pda=True):
        """
        Descarta los autómatas finitos de la sesión.
        CORRECCIÓN: el autómata de pila solo se borra si incluir_pda=True,
        para no perderlo al cargar un AFD/AFND.
        """
        self.afd_directo = None
        self.afnd = None
        self.afd_generado = None
        self.equivalencias = None
        if incluir_pda:
            self.pda = None

    def afd_activo(self):
        if self.afd_generado is not None:
            return self.afd_generado
        return self.afd_directo


def convertir_afnd_en_sesion(sesion):
    """Actualiza el AFD equivalente sin borrar las evaluaciones anteriores."""
    nuevo_afd, equivalencias = convertir_afnd_a_afd(sesion.afnd)
    if sesion.afd_generado is not None:
        nuevo_afd.historial = list(sesion.afd_generado.historial)
    sesion.afd_generado = nuevo_afd
    sesion.equivalencias = equivalencias


def cargar_afnd_en_sesion(sesion, nuevo_afnd):
    """Valida y convierte antes de reemplazar el autómata activo."""
    nuevo_afd, equivalencias = convertir_afnd_a_afd(nuevo_afnd)
    sesion.reiniciar(incluir_pda=False)
    sesion.afnd = nuevo_afnd
    sesion.afd_generado = nuevo_afd
    sesion.equivalencias = equivalencias


def imprimir_tabla(header, filas, titulo):
    print(f"\n--- {titulo} ---")
    print(" | ".join(header))
    print("-" * (len(header) * 8))
    for fila in filas:
        print(" | ".join(str(valor) for valor in fila))


def mostrar_menu():
    print("\n" + "=" * 62)
    print("   MOTOR DE AFD, AFND Y CONVERSIÓN POR SUBCONJUNTOS")
    print("=" * 62)
    print("1. Crear AFD manualmente")
    print("2. Cargar AFD desde archivo .txt")
    print("3. Crear AFND manualmente")
    print("4. Cargar AFND desde archivo .txt")
    print("5. Mostrar definición formal y tabla del autómata cargado")
    print("6. Validar estructura")
    print("7. Convertir AFND a AFD")
    print("8. Mostrar tabla de equivalencias")
    print("9. Mostrar tabla del AFD generado")
    print("10. Evaluar cadena")
    print("11. Evaluar archivo de cadenas")
    print("12. Historial")
    print("13. Análisis estructural")
    print("14. Cargar o crear otro autómata")
    print("15. Modo Autómata de Pila (APD/APND)")
    print("16. Salir")
    print("-" * 62)


def mostrar_menu_pda():
    print("\n" + "=" * 62)
    print("   MODO AUTÓMATA DE PILA (APD / APND)")
    print("=" * 62)
    print("1. Crear APD/APND manualmente")
    print("2. Cargar APD/APND desde archivo .txt")
    print("3. Mostrar definición formal y tabla de transición")
    print("4. Validar estructura")
    print("5. Evaluar cadena")
    print("6. Evaluar archivo de cadenas")
    print("7. Volver al menú principal")
    print("-" * 62)


def menu_pda(sesion):
    while True:
        mostrar_menu_pda()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            try:
                sesion.pda = cargar_manual_pda()
                print("\nAPD/APND creado en memoria.")
            except Exception as e:
                print(f"\nError: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "2":
            ruta = input("Ruta del archivo .txt: ").strip()
            try:
                sesion.pda = cargar_desde_archivo_pda(ruta)
                print(f"\nAPD/APND cargado desde '{ruta}'.")
            except Exception as e:
                print(f"\nError: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "3":
            if sesion.pda is None:
                print("\nPrimero cree o cargue un APD/APND.")
            else:
                print(f"\n--- DEFINICIÓN FORMAL ({sesion.pda.tipo}) ---")
                print(sesion.pda)
                imprimir_tabla_pda(sesion.pda)
            input("Presione Enter para continuar...")

        elif opcion == "4":
            if sesion.pda is None:
                print("\nPrimero cree o cargue un APD/APND.")
            else:
                errores = validar_pda(sesion.pda)
                if errores:
                    print("\nErrores encontrados:")
                    for e in errores:
                        print(f"  - {e}")
                else:
                    print(f"\n✅ El {sesion.pda.tipo} es formalmente válido.")
            input("Presione Enter para continuar...")

        elif opcion == "5":
            if sesion.pda is None:
                print("\nPrimero cree o cargue un APD/APND.")
            else:
                errores = validar_pda(sesion.pda)
                if errores:
                    print("\nEl autómata tiene errores; corrija antes de simular.")
                    for e in errores:
                        print(f"  - {e}")
                else:
                    # CORRECCIÓN: ε / epsilon se interpreta como cadena vacía.
                    cadena = normalizar_cadena(input("Ingrese la cadena a evaluar: "))
                    try:
                        if sesion.pda.tipo == "APD":
                            res = simular_apd(sesion.pda, cadena)
                        else:
                            res = simular_apnd(sesion.pda, cadena)
                        imprimir_traza_pda(sesion.pda, cadena, res)
                    except Exception as e:
                        print(f"Error durante la simulación: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "6":
            if sesion.pda is None:
                print("\nPrimero cree o cargue un APD/APND.")
            else:
                ruta = input("Ruta del archivo de cadenas: ").strip()
                try:
                    with open(ruta, "r", encoding="utf-8") as f:
                        cadenas = []
                        for linea in f:
                            if not linea.strip():
                                continue
                            cadenas.append(normalizar_cadena(linea))
                    if not cadenas:
                        print("El archivo está vacío.")
                    for c in cadenas:
                        try:
                            if sesion.pda.tipo == "APD":
                                res = simular_apd(sesion.pda, c)
                            else:
                                res = simular_apnd(sesion.pda, c)
                            imprimir_traza_pda(sesion.pda, c, res)
                        except Exception as e:
                            print(f"Error con '{c}': {e}")
                except Exception as e:
                    print(f"Error al leer archivo: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "7":
            return
        else:
            print("Opción no válida.")
            input("Presione Enter para continuar...")

def menu_principal():
    """Bucle principal del menú."""
    sesion = EstadoSesion()

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            nuevo = cargar_manual()
            sesion.reiniciar(incluir_pda=False)
            sesion.afd_directo = nuevo
            print("\nAFD creado exitosamente.")
            input("Presione Enter para continuar...")

        elif opcion == "2":
            ruta = input("Ingrese la ruta del archivo .txt: ").strip()
            try:
                nuevo = cargar_desde_archivo(ruta)
                sesion.reiniciar(incluir_pda=False)
                sesion.afd_directo = nuevo
                print(f"\nAFD cargado exitosamente desde '{ruta}'.")
            except Exception as e:
                print(f"\nError: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "3":
            nuevo = cargar_manual_afnd()
            errores = validar_afnd(nuevo)
            if errores:
                print("\nEl AFND es inválido:")
                for error in errores:
                    print(f"  - {error}")
            else:
                cargar_afnd_en_sesion(sesion, nuevo)
                print("\nAFND creado y validado. AFD equivalente generado automáticamente.")
            input("Presione Enter para continuar...")

        elif opcion == "4":
            ruta = input("Ingrese la ruta del archivo .txt: ").strip()
            try:
                nuevo = cargar_desde_archivo_afnd(ruta)
                cargar_afnd_en_sesion(sesion, nuevo)
                print(f"\nAFND cargado y validado desde '{ruta}'.")
                print("AFD equivalente generado automáticamente (opciones 8 y 9).")
            except Exception as e:
                print(f"\nError: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "5":
            if sesion.afnd is None and sesion.afd_activo() is None:
                print("\nPrimero debe crear o cargar un autómata.")
            if sesion.afnd is not None:
                print("\n--- DEFINICIÓN FORMAL DEL AFND ORIGINAL ---")
                print(sesion.afnd)
                imprimir_tabla(*sesion.afnd.tabla_transiciones(), "TABLA DEL AFND")
            afd = sesion.afd_activo()
            if afd is not None:
                titulo = "AFD GENERADO" if sesion.afd_generado else "AFD CARGADO"
                print(f"\n--- DEFINICIÓN FORMAL DEL {titulo} ---")
                print(afd)
                imprimir_tabla(*afd.tabla_transiciones(), f"TABLA DEL {titulo}")
            input("Presione Enter para continuar...")

        elif opcion == "6":
            if sesion.afnd is None and sesion.afd_activo() is None:
                print("\nPrimero debe crear o cargar un autómata.")
            if sesion.afnd is not None:
                errores = validar_afnd(sesion.afnd)
                if errores:
                    print("\nEl AFND es inválido:")
                    for error in errores:
                        print(f"  - {error}")
                else:
                    print("\n✅ El AFND es formalmente válido.")
                    if sesion.afd_generado is None:
                        convertir_afnd_en_sesion(sesion)
                    print("El AFD equivalente está disponible.")
            afd = sesion.afd_activo()
            if afd is not None:
                errores = validar_afd(afd)
                faltantes = [(q, s) for q in afd.Q for s in afd.Sigma
                             if (q, s) not in afd.delta]
                otros_errores = [e for e in errores if not e.startswith("Falta transición")]
                if otros_errores:
                    print("\nEl AFD es inválido:")
                    for error in errores:
                        print(f"  - {error}")
                elif faltantes:
                    print("\nEl AFD es determinista, pero está incompleto:")
                    for error in errores:
                        print(f"  - {error}")
                    respuesta = input(
                        "¿Desea completar el AFD utilizando un estado de trampa? (S/N): "
                    ).strip().upper()
                    if respuesta == "S":
                        nombre = completar_con_estado_trampa(afd, faltantes)
                        print(f"Se creó el estado de trampa '{nombre}'.")
                        if not validar_afd(afd):
                            print("✅ El AFD ahora es válido, completo y determinista.")
                else:
                    print("\n✅ El AFD es válido, completo y determinista.")
            input("Presione Enter para continuar...")

        elif opcion == "7":
            if sesion.afnd is None:
                print("\nNo hay un AFND cargado para convertir.")
            else:
                errores = validar_afnd(sesion.afnd)
                if errores:
                    print("\nEl AFND es inválido y no puede convertirse:")
                    for error in errores:
                        print(f"  - {error}")
                else:
                    convertir_afnd_en_sesion(sesion)
                    print("\nConversión realizada correctamente.")
                    imprimir_tabla_equivalencias(sesion.equivalencias)
            input("Presione Enter para continuar...")

        elif opcion == "8":
            if sesion.equivalencias is None:
                print("\nPrimero debe convertir un AFND.")
            else:
                imprimir_tabla_equivalencias(sesion.equivalencias)
            input("Presione Enter para continuar...")

        elif opcion == "9":
            if sesion.afd_generado is None:
                print("\nPrimero debe convertir un AFND.")
            else:
                imprimir_tabla(
                    *sesion.afd_generado.tabla_transiciones(),
                    "TABLA DE TRANSICIÓN DEL AFD GENERADO"
                )
            input("Presione Enter para continuar...")

        elif opcion == "10":
            afd = sesion.afd_activo()
            if afd is None:
                print("\nNo hay un AFD disponible. Convierta primero el AFND.")
            elif validar_afd(afd):
                print("\nEl AFD no está completo y válido. Use la opción 6.")
            else:
                # CORRECCIÓN: ε / epsilon se interpreta como cadena vacía.
                cadena = normalizar_cadena(input("Ingrese la cadena a evaluar: "))
                try:
                    resultado = simular(afd, cadena)
                    imprimir_traza(resultado, cadena)
                    agregar_historial(afd, cadena, resultado)
                except Exception as e:
                    agregar_historial(afd, cadena, error=str(e))
                    print(f"Error: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "11":
            afd = sesion.afd_activo()
            if afd is None:
                print("\nNo hay un AFD disponible. Convierta primero el AFND.")
            elif validar_afd(afd):
                print("\nEl AFD no está completo y válido. Use la opción 6.")
            else:
                ruta = input("Ingrese la ruta del archivo con cadenas: ").strip()
                try:
                    with open(ruta, "r", encoding="utf-8") as archivo:
                        cadenas = []
                        for linea in archivo:
                            if not linea.strip():
                                continue
                            cadenas.append(normalizar_cadena(linea))
                    if not cadenas:
                        print("El archivo no contiene cadenas.")
                    for cadena in cadenas:
                        try:
                            resultado = simular(afd, cadena)
                            imprimir_traza(resultado, cadena)
                            agregar_historial(afd, cadena, resultado)
                        except Exception as e:
                            agregar_historial(afd, cadena, error=str(e))
                            print(f"Error al evaluar '{cadena}': {e}")
                except Exception as e:
                    print(f"Error al leer el archivo: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "12":
            afd = sesion.afd_activo()
            if afd is None:
                print("\nNo hay un AFD disponible. Convierta primero el AFND.")
            else:
                mostrar_historial(afd)
            input("Presione Enter para continuar...")

        elif opcion == "13":
            afd = sesion.afd_activo()
            if afd is None:
                print("\nNo hay un AFD disponible. Convierta primero el AFND.")
            elif validar_afd(afd):
                print("\nEl AFD no está completo y válido. Use la opción 6.")
            else:
                analisis = analizar_estructura(afd)
                print("\n--- ANÁLISIS ESTRUCTURAL ---")
                print(f"Estados alcanzables: {analisis['alcanzables']}")
                print(f"Estados inaccesibles: {analisis['inaccesibles']}")
                print(f"Finales alcanzables: {analisis['finales_alcanzables']}")
                print(f"Lenguaje vacío: {analisis['lenguaje_vacio']}")
            input("Presione Enter para continuar...")

        elif opcion == "14":
            # Descarta todo, incluido el autómata de pila.
            sesion.reiniciar()
            print("\nAutómatas, equivalencias e historiales anteriores descartados.")
            input("Presione Enter para continuar...")

        elif opcion == "15":
            menu_pda(sesion)
        elif opcion == "16":
            print("\nSaliendo del programa. ¡Hasta luego!")
            break
        else:
            print("\nOpción no válida. Intente de nuevo.")
            input("Presione Enter para continuar...")


# ========================== PUNTO DE ENTRADA ==========================
if __name__ == "__main__":
    try:
        menu_principal()
    except (EOFError, KeyboardInterrupt):
        print("\nEntrada finalizada. Saliendo del programa.")
