# -*- coding: utf-8 -*-
"""
Proyecto No. 2 - Lenguajes Formales y Autómatas
Motor de Conversión de Autómatas Finitos No Deterministas (AFND)
a Autómatas Finitos Deterministas (AFD) y Simulación
Universidad Rafael Landívar

Este módulo integra y AMPLÍA el motor de la Fase 1 (carga, validación,
análisis estructural, simulación, trazas e historial de un AFD) para
incorporar la Fase 2: carga y validación de AFND, y su transformación en
un AFD equivalente mediante el algoritmo de construcción de subconjuntos.

Todo en un solo archivo para evitar problemas de importación.

Organización del módulo (separación de responsabilidades):
    1. Clases AFD y AFND: representación formal M = (Q, Σ, δ, q0, F).
    2. Carga: manual y desde archivo .txt (con expresiones regulares).
    3. Validación: integridad, determinismo/incompletitud (AFD) y forma
       general (AFND).
    4. Análisis estructural: alcanzabilidad, estados inaccesibles, vacuidad
       del lenguaje reconocido.
    5. Conversión: algoritmo de construcción de subconjuntos (AFND -> AFD).
    6. Simulación: evaluación de cadenas, traza paso a paso, historial.
    7. Menú principal de consola.
"""

<<<<<<< Updated upstream
=======
import re

# ========================== EXPRESIONES REGULARES ==========================
# Requisito: "La lectura y validación sintáctica de archivos deberá
# utilizar expresiones regulares." Se usan tanto para AFD como para AFND.

# Línea de cabecera del tipo CLAVE=valor (NOMBRE, TIPO, ESTADOS, ALFABETO,
# INICIAL, FINALES). Acepta espacios alrededor del signo "=".
RE_ASIGNACION = re.compile(r'^\s*([A-Za-zÁÉÍÓÚáéíóúñÑ_]+)\s*=\s*(.*?)\s*$')

# Línea que marca el inicio del bloque de transiciones ("TRANSICIONES:").
RE_TRANSICIONES_HEADER = re.compile(r'^\s*TRANSICIONES\s*:\s*$', re.IGNORECASE)

# Línea de transición "origen,simbolo,destino(s)". El tercer grupo puede
# contener uno o varios destinos separados por "|", o el símbolo de
# conjunto vacío "∅".
RE_TRANSICION = re.compile(r'^\s*([^,]+?)\s*,\s*([^,]+?)\s*,\s*(.+?)\s*$')

# Representaciones aceptadas para "sin destinos" y para "transición épsilon"
# (ver Funcionalidad 1 de la Fase 2: no se requieren transiciones ε).
TOKENS_VACIO = {"∅", "VACIO", "VACÍO", "-"}
TOKENS_EPSILON = {"ε", "EPSILON"}


def _es_token_vacio(token):
    return token.strip().upper() in TOKENS_VACIO or token.strip() == ""


def _es_epsilon(token):
    t = token.strip()
    return t == "ε" or t.upper() == "EPSILON"


def generar_nombre_macroestado(indice):
    """
    Genera nombres de macroestado tipo hoja de cálculo: A, B, ..., Z,
    AA, AB, ... a partir de un índice entero >= 0.
    """
    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    indice += 1
    nombre = ""
    while indice > 0:
        indice, resto = divmod(indice - 1, 26)
        nombre = letras[resto] + nombre
    return nombre


>>>>>>> Stashed changes
# ========================== CLASE AFD ==========================
class AFD:
    """
    Representa un Autómata Finito Determinista (AFD) mediante la
    quíntupla M = (Q, Σ, δ, q0, F).
    Esta clase se utiliza tanto para un AFD cargado directamente (Fase 1)
    como para el AFD equivalente generado a partir de un AFND (Fase 2),
    de modo que toda la funcionalidad de la Fase 1 opera igual sobre
    ambos orígenes (principio de compatibilidad).
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
        # Metadatos de origen (para trazabilidad, no afectan la ejecución)
        self.origen = "directo"       # "directo" o "conversion"
        self.tabla_equivalencias = None  # dict nombre -> frozenset(estados AFND)

    def agregar_transicion(self, origen, simbolo, destino):
        """
        Agrega una transición determinista. Lanza excepción si ya existe
        una transición distinta para el mismo par (origen, simbolo), lo
        cual indica que la definición no es determinista.
        """
        clave = (origen, simbolo)
        if clave in self.delta and self.delta[clave] != destino:
            raise ValueError(
                f"Transición duplicada para ({origen}, {simbolo}). No es determinista."
            )
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


# ========================== CLASE AFND ==========================
class AFND:
    """
    Representa un Autómata Finito No Determinista (AFND) mediante la
    quíntupla M = (Q, Σ, δ, q0, F), donde δ asocia cada par (estado,
    símbolo) con CERO, UNO o VARIOS estados de llegada (un conjunto).
    No se contemplan transiciones ε en esta fase.
    """
    def __init__(self, nombre=""):
        self.nombre = nombre
        self.Q = set()
        self.Sigma = set()
        self.delta = {}   # (estado, simbolo) -> set(estados destino), puede ser set() vacío
        self.q0 = None
        self.F = set()

    def agregar_transicion(self, origen, simbolo, destinos):
        """
        Agrega (o amplía) el conjunto de destinos para (origen, simbolo).
        'destinos' es un iterable de estados (puede estar vacío => ∅).
        """
        clave = (origen, simbolo)
        if clave not in self.delta:
            self.delta[clave] = set()
        self.delta[clave].update(destinos)

    def destinos(self, estado, simbolo):
        """Devuelve el conjunto de destinos para (estado, simbolo); ∅ si no existe."""
        return self.delta.get((estado, simbolo), set())

    def __str__(self):
        partes_delta = []
        for (o, s), d in sorted(self.delta.items()):
            rep = "∅" if not d else "{" + ",".join(sorted(d)) + "}"
            partes_delta.append(f"({o},{s})->{rep}")
        return (f"AFND: {self.nombre}\nQ = {self.Q}\nΣ = {self.Sigma}\n"
                f"δ = {{{', '.join(partes_delta)}}}\nq0 = {self.q0}\nF = {self.F}")

    def tabla_transiciones(self):
        """
        Devuelve encabezado y filas de la tabla de transición del AFND.
        Cada celda muestra el conjunto de destinos: '∅', '{q0}', '{q0,q1}', etc.
        '-' indica que el par no fue declarado en absoluto (equivalente a ∅
        para efectos de la construcción de subconjuntos).
        """
        estados = sorted(self.Q)
        simbolos = sorted(self.Sigma)
        header = ["Estado"] + simbolos
        filas = []
        for estado in estados:
            fila = [estado]
            for sim in simbolos:
                if (estado, sim) not in self.delta:
                    fila.append("-")
                else:
                    d = self.delta[(estado, sim)]
                    fila.append("∅" if not d else "{" + ",".join(sorted(d)) + "}")
            filas.append(fila)
        return header, filas


# ========================== CARGA MANUAL ==========================
def _pedir_conjunto(mensaje):
    texto = input(mensaje).strip()
    return set(e.strip() for e in texto.split(",") if e.strip())


def cargar_manual_afd():
    """
    Solicita al usuario los componentes de un AFD por consola.
    Retorna un objeto AFD.
    """
    print("\n--- CREACIÓN MANUAL DE AFD ---")
    nombre = input("Nombre o identificador del autómata: ").strip()
    afd = AFD(nombre)

<<<<<<< Updated upstream
    # Estados
    estados_str = input("Ingrese los estados (separados por comas): ").strip()
    estados = [e.strip() for e in estados_str.split(",") if e.strip()]
    afd.Q = set(estados)

    # Alfabeto
    sigma_str = input("Ingrese el alfabeto (símbolos separados por comas): ").strip()
    sigma = [s.strip() for s in sigma_str.split(",") if s.strip()]
    afd.Sigma = set(sigma)

    # Estado inicial
=======
    afd.Q = _pedir_conjunto("Ingrese los estados (separados por comas): ")
    afd.Sigma = _pedir_conjunto("Ingrese el alfabeto (símbolos separados por comas): ")

>>>>>>> Stashed changes
    while True:
        q0 = input("Ingrese el estado inicial: ").strip()
        if q0 in afd.Q:
            afd.q0 = q0
            break
        print(f"Error: '{q0}' no está en el conjunto de estados. Intente de nuevo.")

<<<<<<< Updated upstream
    # Estados finales
=======
>>>>>>> Stashed changes
    while True:
        finales_str = input("Ingrese los estados finales (separados por comas): ").strip()
        if not finales_str:
            print("Debe ingresar al menos un estado final.")
            continue
<<<<<<< Updated upstream
        finales = [f.strip() for f in finales_str.split(",") if f.strip()]
        if all(f in afd.Q for f in finales):
            afd.F = set(finales)
            break
        else:
            print("Error: uno o más estados finales no pertenecen a Q. Intente de nuevo.")
=======
        finales = set(f.strip() for f in finales_str.split(",") if f.strip())
        if finales.issubset(afd.Q):
            afd.F = finales
            break
        print("Error: uno o más estados finales no pertenecen a Q. Intente de nuevo.")
>>>>>>> Stashed changes

    print("\nIngrese las transiciones una por una.")
    print("Formato: estado_origen, símbolo, estado_destino")
    print("Escriba 'fin' para terminar.")
    while True:
        linea = input("Transición: ").strip()
        if linea.lower() == "fin":
            break
<<<<<<< Updated upstream
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) != 3:
            print("Formato incorrecto. Debe ser: origen, símbolo, destino")
            continue
        origen, simbolo, destino = partes
=======
        m = RE_TRANSICION.match(linea)
        if not m:
            print("Formato incorrecto. Debe ser: origen, símbolo, destino")
            continue
        origen, simbolo, destino = (g.strip() for g in m.groups())
>>>>>>> Stashed changes
        if origen not in afd.Q:
            print(f"Error: '{origen}' no está en Q.")
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


def cargar_manual_afnd():
    """
<<<<<<< Updated upstream
    Lee un archivo de texto con el formato especificado y retorna un objeto AFD.
    No utiliza expresiones regulares, solo métodos de cadena.
=======
    Solicita al usuario los componentes de un AFND por consola.
    Un mismo par (origen, símbolo) puede tener cero, uno o varios destinos.
    Retorna un objeto AFND.
>>>>>>> Stashed changes
    """
    print("\n--- CREACIÓN MANUAL DE AFND ---")
    nombre = input("Nombre o identificador del autómata: ").strip()
    afnd = AFND(nombre)

<<<<<<< Updated upstream
=======
    afnd.Q = _pedir_conjunto("Ingrese los estados (separados por comas): ")
    afnd.Sigma = _pedir_conjunto("Ingrese el alfabeto (símbolos separados por comas): ")

    while True:
        q0 = input("Ingrese el estado inicial: ").strip()
        if q0 in afnd.Q:
            afnd.q0 = q0
            break
        print(f"Error: '{q0}' no está en el conjunto de estados. Intente de nuevo.")

    while True:
        finales_str = input("Ingrese los estados finales (separados por comas): ").strip()
        if not finales_str:
            print("Debe ingresar al menos un estado final.")
            continue
        finales = set(f.strip() for f in finales_str.split(",") if f.strip())
        if finales.issubset(afnd.Q):
            afnd.F = finales
            break
        print("Error: uno o más estados finales no pertenecen a Q. Intente de nuevo.")

    print("\nIngrese las transiciones una por una.")
    print("Formato: origen, símbolo, destino1|destino2|...")
    print("Use '∅' (o deje el campo vacío) para indicar ausencia de destinos.")
    print("Escriba 'fin' para terminar.")
    while True:
        linea = input("Transición: ").strip()
        if linea.lower() == "fin":
            break
        m = RE_TRANSICION.match(linea)
        if not m:
            print("Formato incorrecto. Debe ser: origen, símbolo, destino(s)")
            continue
        origen, simbolo, destino_str = (g.strip() for g in m.groups())
        if origen not in afnd.Q:
            print(f"Error: '{origen}' no está en Q.")
            continue
        if simbolo not in afnd.Sigma:
            print(f"Error: '{simbolo}' no está en Σ.")
            continue
        if _es_epsilon(destino_str) or _es_epsilon(simbolo):
            print("Aviso: las transiciones ε no forman parte del alcance de este proyecto. Ignorada.")
            continue
        if _es_token_vacio(destino_str):
            destinos = set()
        else:
            destinos = set(d.strip() for d in destino_str.split("|") if d.strip())
            invalidos = destinos - afnd.Q
            if invalidos:
                print(f"Error: los siguientes destinos no están en Q: {invalidos}")
                continue
        afnd.agregar_transicion(origen, simbolo, destinos)
        print("Transición agregada.")

    return afnd


# ========================== CARGA DESDE ARCHIVO ==========================
def _leer_lineas(ruta_archivo):
>>>>>>> Stashed changes
    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            return f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise Exception(f"Error al leer el archivo: {e}")

<<<<<<< Updated upstream
=======

def cargar_desde_archivo_afd(ruta_archivo):
    """
    Lee un archivo de texto con el formato CLAVE=valor + bloque
    TRANSICIONES: y retorna un objeto AFD. Usa expresiones regulares
    para el análisis sintáctico, tal como exige el enunciado.
    """
    afd = AFD()
    modo_transiciones = False
    lineas = _leer_lineas(ruta_archivo)

>>>>>>> Stashed changes
    for num_linea, linea_raw in enumerate(lineas, start=1):
        linea = linea_raw.strip()
        if not linea:
            continue

        if modo_transiciones:
<<<<<<< Updated upstream
            partes = [p.strip() for p in linea.split(',')]
            if len(partes) != 3:
                raise SyntaxError(
                    f"Línea {num_linea}: formato de transición inválido (se esperan 3 campos): '{linea}'"
                )
            origen, simbolo, destino = partes
=======
            m = RE_TRANSICION.match(linea)
            if not m:
                raise SyntaxError(
                    f"Línea {num_linea}: formato de transición inválido: '{linea}'"
                )
            origen, simbolo, destino = (g.strip() for g in m.groups())
>>>>>>> Stashed changes
            try:
                afd.agregar_transicion(origen, simbolo, destino)
            except ValueError as e:
                raise ValueError(f"Línea {num_linea}: {e}")
            continue

<<<<<<< Updated upstream
        # Detectar secciones por palabra clave al inicio de la línea
        linea_upper = linea.upper()
        if linea_upper.startswith("NOMBRE="):
            afd.nombre = linea.split("=", 1)[1].strip()
        elif linea_upper.startswith("ESTADOS="):
            estados_str = linea.split("=", 1)[1].strip()
            estados = [e.strip() for e in estados_str.split(",") if e.strip()]
            afd.Q = set(estados)
        elif linea_upper.startswith("ALFABETO="):
            sigma_str = linea.split("=", 1)[1].strip()
            sigma = [s.strip() for s in sigma_str.split(",") if s.strip()]
            afd.Sigma = set(sigma)
        elif linea_upper.startswith("INICIAL="):
            q0 = linea.split("=", 1)[1].strip()
            afd.q0 = q0
        elif linea_upper.startswith("FINALES="):
            finales_str = linea.split("=", 1)[1].strip()
            finales = [f.strip() for f in finales_str.split(",") if f.strip()]
            afd.F = set(finales)
        elif linea_upper.startswith("TRANSICIONES:"):
            modo_transiciones = True
        else:
            raise SyntaxError(
                f"Línea {num_linea}: sintaxis no reconocida: '{linea}'"
            )

    # Validaciones básicas después de la lectura
=======
        if RE_TRANSICIONES_HEADER.match(linea):
            modo_transiciones = True
            continue

        m = RE_ASIGNACION.match(linea)
        if not m:
            raise SyntaxError(f"Línea {num_linea}: sintaxis no reconocida: '{linea}'")
        clave, valor = m.group(1).upper(), m.group(2)

        if clave == "NOMBRE":
            afd.nombre = valor
        elif clave == "TIPO":
            if valor.strip().upper() not in ("AFD", ""):
                raise ValueError(
                    f"Línea {num_linea}: se esperaba TIPO=AFD para cargar un AFD, se encontró '{valor}'."
                )
        elif clave == "ESTADOS":
            afd.Q = set(e.strip() for e in valor.split(",") if e.strip())
        elif clave == "ALFABETO":
            afd.Sigma = set(s.strip() for s in valor.split(",") if s.strip())
        elif clave == "INICIAL":
            afd.q0 = valor.strip()
        elif clave == "FINALES":
            afd.F = set(f.strip() for f in valor.split(",") if f.strip())
        else:
            raise SyntaxError(f"Línea {num_linea}: clave no reconocida: '{clave}'")

>>>>>>> Stashed changes
    if not afd.Q:
        raise ValueError("No se definieron estados (Q).")
    if not afd.Sigma:
        raise ValueError("No se definió el alfabeto (Σ).")
    if afd.q0 is None:
        raise ValueError("No se definió el estado inicial (q0).")
    if not afd.F:
        raise ValueError("No se definieron estados finales (F).")

    return afd


def cargar_desde_archivo_afnd(ruta_archivo):
    """
    Lee un archivo de texto con el mismo formato de cabecera que el AFD,
    pero con TIPO=AFND y transiciones que admiten cero, uno o varios
    destinos separados por '|' (o '∅' para conjunto vacío). Usa
    expresiones regulares para el análisis sintáctico.
    """
    afnd = AFND()
    modo_transiciones = False
    lineas = _leer_lineas(ruta_archivo)

    for num_linea, linea_raw in enumerate(lineas, start=1):
        linea = linea_raw.strip()
        if not linea:
            continue

        if modo_transiciones:
            m = RE_TRANSICION.match(linea)
            if not m:
                raise SyntaxError(
                    f"Línea {num_linea}: formato de transición inválido: '{linea}'"
                )
            origen, simbolo, destino_str = (g.strip() for g in m.groups())
            if _es_epsilon(simbolo) or _es_epsilon(destino_str):
                raise ValueError(
                    f"Línea {num_linea}: las transiciones ε no forman parte del "
                    f"alcance solicitado en esta fase."
                )
            if origen not in afnd.Q:
                raise ValueError(f"Línea {num_linea}: el estado origen '{origen}' no fue declarado en ESTADOS.")
            if simbolo not in afnd.Sigma:
                raise ValueError(f"Línea {num_linea}: el símbolo '{simbolo}' no fue declarado en ALFABETO.")
            if _es_token_vacio(destino_str):
                destinos = set()
            else:
                destinos = set(d.strip() for d in destino_str.split("|") if d.strip())
                invalidos = destinos - afnd.Q
                if invalidos:
                    raise ValueError(
                        f"Línea {num_linea}: los siguientes destinos no fueron declarados en ESTADOS: {invalidos}"
                    )
            afnd.agregar_transicion(origen, simbolo, destinos)
            continue

        if RE_TRANSICIONES_HEADER.match(linea):
            modo_transiciones = True
            continue

        m = RE_ASIGNACION.match(linea)
        if not m:
            raise SyntaxError(f"Línea {num_linea}: sintaxis no reconocida: '{linea}'")
        clave, valor = m.group(1).upper(), m.group(2)

        if clave == "NOMBRE":
            afnd.nombre = valor
        elif clave == "TIPO":
            if valor.strip().upper() not in ("AFND", ""):
                raise ValueError(
                    f"Línea {num_linea}: se esperaba TIPO=AFND para cargar un AFND, se encontró '{valor}'."
                )
        elif clave == "ESTADOS":
            afnd.Q = set(e.strip() for e in valor.split(",") if e.strip())
        elif clave == "ALFABETO":
            afnd.Sigma = set(s.strip() for s in valor.split(",") if s.strip())
        elif clave == "INICIAL":
            afnd.q0 = valor.strip()
        elif clave == "FINALES":
            afnd.F = set(f.strip() for f in valor.split(",") if f.strip())
        else:
            raise SyntaxError(f"Línea {num_linea}: clave no reconocida: '{clave}'")

    if not afnd.Q:
        raise ValueError("No se definieron estados (Q).")
    if not afnd.Sigma:
        raise ValueError("No se definió el alfabeto (Σ).")
    if afnd.q0 is None:
        raise ValueError("No se definió el estado inicial (q0).")
    if not afnd.F:
        raise ValueError("No se definieron estados finales (F).")
    if afnd.q0 not in afnd.Q:
        raise ValueError(f"El estado inicial '{afnd.q0}' no pertenece a Q.")
    if not afnd.F.issubset(afnd.Q):
        raise ValueError("Uno o más estados finales no pertenecen a Q.")

    return afnd


# ========================== VALIDACIÓN Y ANÁLISIS ESTRUCTURAL (AFD) ==========================
def validar_afd(afd):
    """
    Verifica la integridad del AFD:
    - q0 ∈ Q
    - F ⊆ Q
    - Transiciones consistentes
    - Completitud: exactamente una transición por par (estado, símbolo)
    Retorna una lista de errores/observaciones (vacía si todo es correcto
    y completo). Si la única observación es de incompletitud, el AFD se
    considera "incompleto" pero sigue siendo determinista.
    """
    errores = []

    if afd.q0 not in afd.Q:
        errores.append(f"El estado inicial '{afd.q0}' no pertenece a Q.")

    if not afd.F.issubset(afd.Q):
        no_pertenecen = afd.F - afd.Q
        errores.append(f"Los siguientes estados finales no pertenecen a Q: {no_pertenecen}")

    for (origen, simbolo), destino in afd.delta.items():
        if origen not in afd.Q:
            errores.append(f"En transición ({origen}, {simbolo}) -> {destino}: origen no está en Q.")
        if simbolo not in afd.Sigma:
            errores.append(f"En transición ({origen}, {simbolo}) -> {destino}: símbolo no está en Σ.")
        if destino not in afd.Q:
            errores.append(f"En transición ({origen}, {simbolo}) -> {destino}: destino no está en Q.")

    faltantes = [(e, s) for e in afd.Q for s in afd.Sigma if (e, s) not in afd.delta]
    for (e, s) in faltantes:
        errores.append(f"Falta transición para el par ({e}, {s}). [AFD INCOMPLETO]")

    return errores


<<<<<<< Updated upstream
=======
def clasificar_afd(afd):
    """
    Clasifica la definición cargada según los objetivos de aprendizaje:
    'valido_completo', 'incompleto' o 'invalido'.
    Se apoya en validar_afd(); una definición no determinista nunca llega
    aquí porque agregar_transicion ya lo impide en el momento de la carga.
    """
    errores = validar_afd(afd)
    if not errores:
        return "valido_completo", errores
    solo_incompletitud = all("[AFD INCOMPLETO]" in e for e in errores)
    if solo_incompletitud:
        return "incompleto", errores
    return "invalido", errores


def completar_afd_con_trampa(afd, nombre_trampa="TRAMPA"):
    """
    Completa un AFD incompleto agregando un estado de trampa (sumidero)
    para todos los pares (estado, símbolo) sin transición definida.
    Retorna True si se agregó el estado de trampa, False si el AFD ya
    estaba completo (no había nada que hacer).
    """
    faltantes = [(e, s) for e in afd.Q for s in afd.Sigma if (e, s) not in afd.delta]
    if not faltantes:
        return False, nombre_trampa

    nombre_final = nombre_trampa
    contador = 1
    while nombre_final in afd.Q:
        nombre_final = f"{nombre_trampa}_{contador}"
        contador += 1

    afd.Q.add(nombre_final)
    for simbolo in afd.Sigma:
        afd.delta[(nombre_final, simbolo)] = nombre_final
    for (e, s) in faltantes:
        afd.delta[(e, s)] = nombre_final

    return True, nombre_final


>>>>>>> Stashed changes
def analizar_estructura(afd):
    """
    Calcula estados alcanzables, inaccesibles, finales alcanzables y si el
    lenguaje es vacío. Actualiza los atributos del objeto AFD.
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


# ========================== VALIDACIÓN (AFND) ==========================
def validar_afnd(afnd):
    """
    Verifica la integridad formal del AFND:
    - q0 ∈ Q
    - F ⊆ Q
    - Todos los estados y símbolos usados en δ fueron declarados
    A diferencia del AFD, NO se exige completitud (∅ es una transición
    legítima) ni determinismo (varios destinos son legítimos).
    Retorna una lista de errores (vacía si el AFND es formalmente válido).
    """
    errores = []

    if afnd.q0 not in afnd.Q:
        errores.append(f"El estado inicial '{afnd.q0}' no pertenece a Q.")

    if not afnd.F.issubset(afnd.Q):
        no_pertenecen = afnd.F - afnd.Q
        errores.append(f"Los siguientes estados finales no pertenecen a Q: {no_pertenecen}")

    for (origen, simbolo), destinos in afnd.delta.items():
        if origen not in afnd.Q:
            errores.append(f"En transición ({origen}, {simbolo}): origen no está en Q.")
        if simbolo not in afnd.Sigma:
            errores.append(f"En transición ({origen}, {simbolo}): símbolo no está en Σ.")
        no_declarados = destinos - afnd.Q
        if no_declarados:
            errores.append(
                f"En transición ({origen}, {simbolo}): destino(s) no declarados en Q: {no_declarados}"
            )

    return errores


def es_afnd_realmente_no_determinista(afnd):
    """
    Indica si el AFND presentado tiene al menos un par (estado, símbolo)
    con más de un destino (no determinismo genuino) o con cero destinos
    (incompletitud/∅). Útil solo con fines informativos para el usuario.
    """
    tiene_multiples = any(len(d) > 1 for d in afnd.delta.values())
    tiene_vacios = any(len(d) == 0 for d in afnd.delta.values())
    return tiene_multiples, tiene_vacios


# ========================== CONVERSIÓN: CONSTRUCCIÓN DE SUBCONJUNTOS ==========================
def convertir_afnd_a_afd(afnd):
    """
    Aplica el algoritmo de construcción de subconjuntos (sin usar
    bibliotecas que lo implementen directamente) para obtener un AFD
    equivalente al AFND recibido.

    Reglas aplicadas (según el enunciado de la Fase 2):
      - El estado inicial del AFD es el macroestado {q0}.
      - Para cada macroestado S y símbolo a, el destino es la unión de
        δ(q, a) para todo q en S.
      - Cada subconjunto nuevo se registra y procesa hasta agotar la cola
        de macroestados pendientes (BFS con lista, sin collections.deque).
      - El conjunto vacío ∅ se incorpora como estado de trampa si es
        alcanzado durante la conversión.
      - Un macroestado es final si contiene al menos un estado final del
        AFND original.

    Retorna una tupla (afd, tabla_equivalencias) donde tabla_equivalencias
    es un diccionario {nombre_macroestado: frozenset(estados del AFND)}.
    """
    nombres = {}      # frozenset(estados AFND) -> nombre del macroestado
    orden_creacion = []  # lista de frozensets, en el orden en que se nombraron
    en_cola = set()   # frozensets ya encolados (evita reprocesar)

    def obtener_nombre(conjunto):
        if conjunto not in nombres:
            nombres[conjunto] = generar_nombre_macroestado(len(orden_creacion))
            orden_creacion.append(conjunto)
        return nombres[conjunto]

    inicial = frozenset([afnd.q0])
    obtener_nombre(inicial)

    afd = AFD(f"{afnd.nombre}_AFD" if afnd.nombre else "AFD_generado")
    afd.Sigma = set(afnd.Sigma)
    afd.origen = "conversion"

    cola = [inicial]
    en_cola.add(inicial)
    procesados = set()

    while cola:
        actual = cola.pop(0)
        if actual in procesados:
            continue
        procesados.add(actual)
        nombre_actual = obtener_nombre(actual)
        afd.Q.add(nombre_actual)

        for simbolo in sorted(afd.Sigma):
            union_destinos = set()
            for estado in actual:
                union_destinos.update(afnd.destinos(estado, simbolo))
            conjunto_destino = frozenset(union_destinos)
            nombre_destino = obtener_nombre(conjunto_destino)
            afd.delta[(nombre_actual, simbolo)] = nombre_destino
            if conjunto_destino not in en_cola:
                cola.append(conjunto_destino)
                en_cola.add(conjunto_destino)

    afd.q0 = nombres[inicial]
    for conjunto, nombre in nombres.items():
        afd.Q.add(nombre)  # asegura que también el ∅ (estado de trampa) quede en Q
        if conjunto & afnd.F:
            afd.F.add(nombre)

    tabla_equivalencias = {nombre: conjunto for conjunto, nombre in nombres.items()}
    afd.tabla_equivalencias = tabla_equivalencias

    return afd, tabla_equivalencias


def imprimir_tabla_equivalencias(tabla_equivalencias):
    """
    Imprime la tabla de equivalencias macroestado <-> subconjunto del AFND,
    en el formato solicitado en el enunciado.
    """
    print("\n--- TABLA DE EQUIVALENCIAS DE MACROESTADOS ---")
    print(f"{'Macroestado del AFD':<22}{'Conjunto de estados del AFND'}")
    for nombre in sorted(tabla_equivalencias.keys()):
        conjunto = tabla_equivalencias[nombre]
        rep = "∅" if not conjunto else "{" + ",".join(sorted(conjunto)) + "}"
        print(f"{nombre:<22}{rep}")
    print("-" * 50)


# ========================== SIMULACIÓN (reutilizable para cualquier AFD) ==========================
def simular(afd, cadena):
    """
    Simula el AFD con la cadena de entrada. Funciona igual para un AFD
    cargado directamente o para el AFD generado por conversión, ya que
    ambos comparten la misma estructura interna.
    Retorna un diccionario con:
        - aceptada: bool
        - traza: lista de pasos (cada paso: estado, simbolo, destino)
        - estado_final: str
    """
    for simbolo in cadena:
        if simbolo not in afd.Sigma:
            raise ValueError(f"El símbolo '{simbolo}' no pertenece al alfabeto {afd.Sigma}")

    estado_actual = afd.q0
    traza = []
    for simbolo in cadena:
        destino = afd.delta.get((estado_actual, simbolo))
        if destino is None:
            raise ValueError(f"No hay transición definida para ({estado_actual}, {simbolo})")
        traza.append({"estado": estado_actual, "simbolo": simbolo, "destino": destino})
        estado_actual = destino

    aceptada = estado_actual in afd.F
    return {"aceptada": aceptada, "traza": traza, "estado_final": estado_actual}


def imprimir_traza(resultado, cadena):
    """Imprime en consola la traza de la simulación."""
    print("\n--- TRAZA DE EJECUCIÓN ---")
    print(f"Cadena evaluada: '{cadena}'")
<<<<<<< Updated upstream
=======
    if not resultado["traza"] and cadena == "":
        print("(cadena vacía: no se realiza ninguna transición)")
>>>>>>> Stashed changes
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
def agregar_historial(afd, cadena, resultado):
    """Agrega una entrada al historial del AFD."""
    entrada = {
        "cadena": cadena,
        "aceptada": resultado["aceptada"],
        "estado_final": resultado["estado_final"],
        "traza": resultado["traza"]
    }
    afd.historial.append(entrada)


def mostrar_historial(afd):
    """Muestra el historial de evaluaciones."""
    if not afd.historial:
        print("\nNo hay evaluaciones en el historial.")
        return
    print("\n--- HISTORIAL DE EVALUACIONES ---")
    for i, entrada in enumerate(afd.historial, start=1):
        estado = "ACEPTADA ✅" if entrada["aceptada"] else "RECHAZADA ❌"
        print(f"{i}. Cadena: '{entrada['cadena']}' -> {estado} (Estado final: {entrada['estado_final']})")
    print("-" * 30)


def imprimir_tabla(header, filas, titulo):
    print(f"\n--- {titulo} ---")
    print(" | ".join(header))
    print("-" * (len(header) * 8))
    for fila in filas:
        print(" | ".join(str(c) for c in fila))


# ========================== ESTADO DE LA SESIÓN ==========================
class EstadoSesion:
    """
    Agrupa el estado "vivo" del programa: el autómata cargado (AFD directo
    o AFND) y, si corresponde, el AFD equivalente generado por conversión.
    Se reinicia por completo cada vez que se carga o crea un nuevo
    autómata (regla de operación: separar datos, macroestados e
    historiales anteriores).
    """
    def __init__(self):
        self.reiniciar()

    def reiniciar(self):
        self.afnd = None                 # AFND cargado/creado (o None)
        self.afd_directo = None          # AFD cargado/creado directamente (o None)
        self.afd_generado = None         # AFD resultante de convertir self.afnd (o None)
        self.tabla_equivalencias = None  # dict del último AFND convertido

    def afd_activo(self):
        """
        AFD sobre el que operan las herramientas heredadas de la Fase 1
        (definición, tabla, validación, análisis, simulación, historial):
        si existe un AFD generado por conversión se usa ese; de lo
        contrario se usa el AFD cargado directamente.
        """
        return self.afd_generado if self.afd_generado is not None else self.afd_directo

    def hay_algo_cargado(self):
        return self.afnd is not None or self.afd_directo is not None


# ========================== MENÚ PRINCIPAL ==========================
def mostrar_menu():
    print("\n" + "=" * 62)
    print("  MOTOR DE CONVERSIÓN DE AFND A AFD Y SIMULACIÓN (FASE 1 + 2)")
    print("=" * 62)
    print(" 1. Crear un AFD manualmente")
    print(" 2. Cargar un AFD desde un archivo .txt")
    print(" 3. Crear un AFND manualmente")
    print(" 4. Cargar un AFND desde un archivo .txt")
    print(" 5. Mostrar la definición formal y la tabla del autómata cargado")
    print(" 6. Validar la estructura del autómata")
    print(" 7. Completar el AFD con un estado de trampa (si está incompleto)")
    print(" 8. Convertir el AFND cargado en un AFD equivalente")
    print(" 9. Mostrar la tabla de equivalencias de macroestados")
    print("10. Mostrar la tabla de transición del AFD generado")
    print("11. Evaluar una cadena")
    print("12. Evaluar un archivo de cadenas")
    print("13. Consultar el historial de evaluaciones")
    print("14. Realizar el análisis estructural")
    print("15. Cargar o crear otro autómata")
    print("16. Salir")
    print("-" * 62)


def _pausa():
    input("Presione Enter para continuar...")


def _opcion_crear_afd_manual(estado):
    estado.reiniciar()
    estado.afd_directo = cargar_manual_afd()
    print("\nAFD creado exitosamente.")


def _opcion_cargar_afd_archivo(estado):
    ruta = input("Ingrese la ruta del archivo .txt: ").strip()
    try:
        nuevo = cargar_desde_archivo_afd(ruta)
        estado.reiniciar()
        estado.afd_directo = nuevo
        print(f"\nAFD cargado exitosamente desde '{ruta}'.")
    except Exception as e:
        print(f"\nError: {e}")


def _opcion_crear_afnd_manual(estado):
    estado.reiniciar()
    estado.afnd = cargar_manual_afnd()
    print("\nAFND creado exitosamente.")
    errores = validar_afnd(estado.afnd)
    if errores:
        print("Advertencia: el AFND presenta observaciones de integridad:")
        for e in errores:
            print(f"  - {e}")
    else:
        print("El AFND es formalmente válido (Q, Σ, q0, F consistentes).")
        header, filas = estado.afnd.tabla_transiciones()
        imprimir_tabla(header, filas, "TABLA DE TRANSICIÓN DEL AFND")


def _opcion_cargar_afnd_archivo(estado):
    ruta = input("Ingrese la ruta del archivo .txt: ").strip()
    try:
        nuevo = cargar_desde_archivo_afnd(ruta)
        estado.reiniciar()
        estado.afnd = nuevo
        print(f"\nAFND cargado exitosamente desde '{ruta}'.")
        errores = validar_afnd(estado.afnd)
        if errores:
            print("Advertencia: el AFND presenta observaciones de integridad:")
            for e in errores:
                print(f"  - {e}")
        else:
            print("El AFND es formalmente válido (Q, Σ, q0, F consistentes).")
            header, filas = estado.afnd.tabla_transiciones()
            imprimir_tabla(header, filas, "TABLA DE TRANSICIÓN DEL AFND")
    except Exception as e:
        print(f"\nError: {e}")


def _opcion_mostrar_definicion(estado):
    if not estado.hay_algo_cargado():
        print("\nPrimero debe crear o cargar un autómata.")
        return
    if estado.afnd is not None:
        print("\n--- DEFINICIÓN FORMAL (AFND ORIGINAL) ---")
        print(estado.afnd)
        header, filas = estado.afnd.tabla_transiciones()
        imprimir_tabla(header, filas, "TABLA DE TRANSICIÓN DEL AFND")
    if estado.afd_activo() is not None:
        titulo = "AFD EQUIVALENTE (GENERADO)" if estado.afd_generado is not None else "AFD CARGADO DIRECTAMENTE"
        print(f"\n--- DEFINICIÓN FORMAL ({titulo}) ---")
        print(estado.afd_activo())
        header, filas = estado.afd_activo().tabla_transiciones()
        imprimir_tabla(header, filas, f"TABLA DE TRANSICIÓN ({titulo})")


def _opcion_validar(estado):
    if not estado.hay_algo_cargado():
        print("\nPrimero debe crear o cargar un autómata.")
        return
    if estado.afnd is not None:
        print("\n--- VALIDACIÓN DEL AFND ---")
        errores = validar_afnd(estado.afnd)
        if errores:
            print("Se encontraron errores de integridad:")
            for e in errores:
                print(f"  - {e}")
        else:
            print("✅ El AFND es formalmente válido.")
            multiples, vacios = es_afnd_realmente_no_determinista(estado.afnd)
            if multiples:
                print("  Se detectaron pares (estado, símbolo) con más de un destino (no determinismo genuino).")
            if vacios:
                print("  Se detectaron pares (estado, símbolo) con destino ∅ (transición ausente).")
    if estado.afd_activo() is not None:
        titulo = "AFD GENERADO" if estado.afd_generado is not None else "AFD CARGADO"
        print(f"\n--- VALIDACIÓN DEL {titulo} ---")
        clasificacion, errores = clasificar_afd(estado.afd_activo())
        if clasificacion == "valido_completo":
            print("✅ El AFD es estructuralmente válido, determinista y completo.")
        elif clasificacion == "incompleto":
            print("⚠️ El AFD es determinista pero INCOMPLETO. Observaciones:")
            for e in errores:
                print(f"  - {e}")
            print("  Puede completarlo con un estado de trampa usando la opción 7.")
        else:
            print("❌ El AFD presenta errores de integridad:")
            for e in errores:
                print(f"  - {e}")


def _opcion_completar_trampa(estado):
    afd = estado.afd_activo()
    if afd is None:
        print("\nPrimero debe crear o cargar (o generar por conversión) un AFD.")
        return
    agregado, nombre = completar_afd_con_trampa(afd)
    if agregado:
        print(f"\nEl AFD estaba incompleto. Se agregó el estado de trampa '{nombre}'.")
        print("El AFD ahora es completo.")
    else:
        print("\nEl AFD ya era completo; no fue necesario agregar un estado de trampa.")


def _opcion_convertir(estado):
    if estado.afnd is None:
        print("\nNo hay un AFND válido cargado. No se puede realizar la conversión.")
        return
    errores = validar_afnd(estado.afnd)
    if errores:
        print("\nEl AFND no es formalmente válido. No se puede convertir. Errores:")
        for e in errores:
            print(f"  - {e}")
        return
    afd_generado, tabla = convertir_afnd_a_afd(estado.afnd)
    estado.afd_generado = afd_generado
    estado.tabla_equivalencias = tabla
    print(f"\nConversión realizada con éxito. Se generaron {len(afd_generado.Q)} macroestado(s).")
    imprimir_tabla_equivalencias(tabla)


def _opcion_mostrar_equivalencias(estado):
    if estado.tabla_equivalencias is None:
        print("\nPrimero debe convertir un AFND a AFD (opción 8).")
        return
    imprimir_tabla_equivalencias(estado.tabla_equivalencias)


def _opcion_mostrar_tabla_afd_generado(estado):
    if estado.afd_generado is None:
        print("\nPrimero debe convertir un AFND a AFD (opción 8).")
        return
    header, filas = estado.afd_generado.tabla_transiciones()
    imprimir_tabla(header, filas, "TABLA DE TRANSICIÓN DEL AFD GENERADO")


def _opcion_evaluar_cadena(estado):
    afd = estado.afd_activo()
    if afd is None:
        print("\nPrimero debe crear, cargar o generar (por conversión) un AFD.")
        return
    clasificacion, errores = clasificar_afd(afd)
    if clasificacion == "invalido":
        print("\nEl AFD no es válido. No se puede simular. Ejecute la opción 6 para ver los errores.")
        return
    if clasificacion == "incompleto":
        print("\nAviso: el AFD está incompleto; una cadena puede quedar sin transición definida.")
        print("Puede completarlo primero con la opción 7 si lo desea.")
    cadena = input("Ingrese la cadena a evaluar (Enter para cadena vacía): ").strip()
    try:
        resultado = simular(afd, cadena)
        imprimir_traza(resultado, cadena)
        agregar_historial(afd, cadena, resultado)
    except Exception as e:
        print(f"Error: {e}")


def _opcion_evaluar_archivo(estado):
    afd = estado.afd_activo()
    if afd is None:
        print("\nPrimero debe crear, cargar o generar (por conversión) un AFD.")
        return
    clasificacion, errores = clasificar_afd(afd)
    if clasificacion == "invalido":
        print("\nEl AFD no es válido. No se puede simular. Ejecute la opción 6 para ver los errores.")
        return
    ruta = input("Ingrese la ruta del archivo con cadenas: ").strip()
    try:
        with open(ruta, 'r', encoding='utf-8') as f:
            cadenas = [linea.rstrip("\n") for linea in f]
        if not cadenas:
            print("El archivo no contiene cadenas.")
            return
        print(f"\nProcesando {len(cadenas)} cadena(s)...")
        for cadena in cadenas:
            try:
                resultado = simular(afd, cadena)
                imprimir_traza(resultado, cadena)
                agregar_historial(afd, cadena, resultado)
            except Exception as e:
                print(f"Error al evaluar '{cadena}': {e}")
    except Exception as e:
        print(f"Error al leer el archivo: {e}")


def _opcion_historial(estado):
    afd = estado.afd_activo()
    if afd is None:
        print("\nPrimero debe crear, cargar o generar (por conversión) un AFD.")
        return
    mostrar_historial(afd)


def _opcion_analisis(estado):
    afd = estado.afd_activo()
    if afd is None:
        print("\nPrimero debe crear, cargar o generar (por conversión) un AFD.")
        return
    clasificacion, errores = clasificar_afd(afd)
    if clasificacion == "invalido":
        print("\nEl AFD no es válido. Ejecute la opción 6 para ver los errores.")
        return
    analisis = analizar_estructura(afd)
    print("\n--- ANÁLISIS ESTRUCTURAL ---")
    print(f"  Estados alcanzables: {analisis['alcanzables']}")
    print(f"  Estados inaccesibles: {analisis['inaccesibles']}")
    print(f"  Estados finales alcanzables: {analisis['finales_alcanzables']}")
    if analisis['lenguaje_vacio']:
        print("  ⚠️ El lenguaje reconocido podría ser vacío.")
    else:
        print("  El lenguaje reconocido no es vacío.")


def menu_principal():
    """Bucle principal del menú."""
    estado = EstadoSesion()

    acciones = {
        "1": _opcion_crear_afd_manual,
        "2": _opcion_cargar_afd_archivo,
        "3": _opcion_crear_afnd_manual,
        "4": _opcion_cargar_afnd_archivo,
        "5": _opcion_mostrar_definicion,
        "6": _opcion_validar,
        "7": _opcion_completar_trampa,
        "8": _opcion_convertir,
        "9": _opcion_mostrar_equivalencias,
        "10": _opcion_mostrar_tabla_afd_generado,
        "11": _opcion_evaluar_cadena,
        "12": _opcion_evaluar_archivo,
        "13": _opcion_historial,
        "14": _opcion_analisis,
    }

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "15":
            estado.reiniciar()
            print("\nAutómata(s) actual(es) descartado(s). Puede crear o cargar uno nuevo.")
            _pausa()
            continue

<<<<<<< Updated upstream
        elif opcion == "2":
            ruta = input("Ingrese la ruta del archivo .txt: ").strip()
            try:
                afd_actual = cargar_desde_archivo(ruta)
                print(f"\nAFD cargado exitosamente desde '{ruta}'.")
            except Exception as e:
                print(f"\nError: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "3":
            if afd_actual is None:
                print("\nPrimero debe crear o cargar un AFD.")
            else:
                print("\n--- DEFINICIÓN FORMAL ---")
                print(afd_actual)
            input("Presione Enter para continuar...")

        elif opcion == "4":
            if afd_actual is None:
                print("\nPrimero debe crear o cargar un AFD.")
            else:
                header, filas = afd_actual.tabla_transiciones()
                print("\n--- TABLA DE TRANSICIÓN ---")
                print(" | ".join(header))
                print("-" * (len(header) * 6))
                for fila in filas:
                    print(" | ".join(str(c) for c in fila))
            input("Presione Enter para continuar...")

        elif opcion == "5":
            if afd_actual is None:
                print("\nPrimero debe crear o cargar un AFD.")
            else:
                print("\n--- VALIDACIÓN Y ANÁLISIS ESTRUCTURAL ---")
                errores = validar_afd(afd_actual)
                if errores:
                    print("Se encontraron errores de integridad:")
                    for err in errores:
                        print(f"  - {err}")
                else:
                    print("✅ El AFD es estructuralmente válido y determinista.")
                    analisis = analizar_estructura(afd_actual)
                    print("\nAnálisis estructural:")
                    print(f"  Estados alcanzables: {analisis['alcanzables']}")
                    print(f"  Estados inaccesibles: {analisis['inaccesibles']}")
                    print(f"  Estados finales alcanzables: {analisis['finales_alcanzables']}")
                    if analisis['lenguaje_vacio']:
                        print("  ⚠️ El lenguaje reconocido podría ser vacío.")
                    else:
                        print("  El lenguaje reconocido no es vacío.")
            input("Presione Enter para continuar...")

        elif opcion == "6":
            if afd_actual is None:
                print("\nPrimero debe crear o cargar un AFD.")
            else:
                errores = validar_afd(afd_actual)
                if errores:
                    print("\nEl AFD no es válido. No se puede simular.")
                    print("Ejecute la opción 5 para ver los errores.")
                else:
                    cadena = input("Ingrese la cadena a evaluar: ").strip()
                    try:
                        resultado = simular(afd_actual, cadena)
                        imprimir_traza(resultado, cadena)
                        agregar_historial(afd_actual, cadena, resultado)
                    except Exception as e:
                        print(f"Error: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "7":
            if afd_actual is None:
                print("\nPrimero debe crear o cargar un AFD.")
            else:
                errores = validar_afd(afd_actual)
                if errores:
                    print("\nEl AFD no es válido. No se puede simular.")
                    print("Ejecute la opción 5 para ver los errores.")
                else:
                    ruta = input("Ingrese la ruta del archivo con cadenas: ").strip()
                    try:
                        with open(ruta, 'r', encoding='utf-8') as f:
                            cadenas = [linea.strip() for linea in f if linea.strip()]
                        if not cadenas:
                            print("El archivo no contiene cadenas.")
                        else:
                            print(f"\nProcesando {len(cadenas)} cadenas...")
                            for cadena in cadenas:
                                try:
                                    resultado = simular(afd_actual, cadena)
                                    imprimir_traza(resultado, cadena)
                                    agregar_historial(afd_actual, cadena, resultado)
                                except Exception as e:
                                    print(f"Error al evaluar '{cadena}': {e}")
                    except Exception as e:
                        print(f"Error al leer el archivo: {e}")
            input("Presione Enter para continuar...")

        elif opcion == "8":
            if afd_actual is None:
                print("\nPrimero debe crear o cargar un AFD.")
            else:
                mostrar_historial(afd_actual)
            input("Presione Enter para continuar...")

        elif opcion == "9":
            afd_actual = None
            print("\nAFD actual descartado. Puede crear o cargar uno nuevo.")
            input("Presione Enter para continuar...")

        elif opcion == "10":
=======
        if opcion == "16":
>>>>>>> Stashed changes
            print("\nSaliendo del programa. ¡Hasta luego!")
            break

        accion = acciones.get(opcion)
        if accion is None:
            print("\nOpción no válida. Intente de nuevo.")
        else:
            try:
                accion(estado)
            except Exception as e:
                # Ningún error debe colapsar el programa.
                print(f"\nOcurrió un error inesperado: {e}")
        _pausa()


# ========================== PUNTO DE ENTRADA ==========================
if __name__ == "__main__":
    menu_principal()