# -*- coding: utf-8 -*-
"""
Proyecto No. 1 - Lenguajes Formales y Autómatas
Motor de Parsing, Validación y Simulación de AFD
Todo en un solo archivo para evitar problemas de importación.
"""

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


# ========================== CARGA MANUAL Y DESDE ARCHIVO ==========================
def cargar_manual():
    """
    Solicita al usuario los componentes del AFD por consola.
    Retorna un objeto AFD.
    """
    print("\n--- CREACIÓN MANUAL DE AFD ---")
    nombre = input("Nombre o identificador del autómata: ").strip()
    afd = AFD(nombre)

    # Estados
    estados_str = input("Ingrese los estados (separados por comas): ").strip()
    estados = [e.strip() for e in estados_str.split(",") if e.strip()]
    afd.Q = set(estados)

    # Alfabeto
    sigma_str = input("Ingrese el alfabeto (símbolos separados por comas): ").strip()
    sigma = [s.strip() for s in sigma_str.split(",") if s.strip()]
    afd.Sigma = set(sigma)

    # Estado inicial
    while True:
        q0 = input("Ingrese el estado inicial: ").strip()
        if q0 in afd.Q:
            afd.q0 = q0
            break
        else:
            print(f"Error: '{q0}' no está en el conjunto de estados. Intente de nuevo.")

    # Estados finales
    while True:
        finales_str = input("Ingrese los estados finales (separados por comas): ").strip()
        if not finales_str:
            print("Debe ingresar al menos un estado final.")
            continue
        finales = [f.strip() for f in finales_str.split(",") if f.strip()]
        if all(f in afd.Q for f in finales):
            afd.F = set(finales)
            break
        else:
            print("Error: uno o más estados finales no pertenecen a Q. Intente de nuevo.")

    # Transiciones
    print("\nIngrese las transiciones una por una.")
    print("Formato: estado_origen, símbolo, estado_destino")
    print("Escriba 'fin' para terminar.")
    while True:
        linea = input("Transición: ").strip()
        if linea.lower() == "fin":
            break
        partes = [p.strip() for p in linea.split(",")]
        if len(partes) != 3:
            print("Formato incorrecto. Debe ser: origen, símbolo, destino")
            continue
        origen, simbolo, destino = partes
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


def cargar_desde_archivo(ruta_archivo):
    """
    Lee un archivo de texto con el formato especificado y retorna un objeto AFD.
    No utiliza expresiones regulares, solo métodos de cadena.
    """
    afd = AFD()
    modo_transiciones = False

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
    except FileNotFoundError:
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")
    except Exception as e:
        raise Exception(f"Error al leer el archivo: {e}")

    for num_linea, linea_raw in enumerate(lineas, start=1):
        linea = linea_raw.strip()
        if not linea:
            continue

        if modo_transiciones:
            partes = [p.strip() for p in linea.split(',')]
            if len(partes) != 3:
                raise SyntaxError(
                    f"Línea {num_linea}: formato de transición inválido (se esperan 3 campos): '{linea}'"
                )
            origen, simbolo, destino = partes
            try:
                afd.agregar_transicion(origen, simbolo, destino)
            except ValueError as e:
                raise ValueError(f"Línea {num_linea}: {e}")
            continue

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
    if not afd.Q:
        raise ValueError("No se definieron estados (Q).")
    if not afd.Sigma:
        raise ValueError("No se definió el alfabeto (Σ).")
    if afd.q0 is None:
        raise ValueError("No se definió el estado inicial (q0).")
    if not afd.F:
        raise ValueError("No se definieron estados finales (F).")

    return afd


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

    for (origen, simbolo), destino in afd.delta.items():
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
    print(f"Cadena evaluada: '{cadena}'")
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
    """
    Agrega una entrada al historial del AFD.
    """
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
        estado = "ACEPTADA ✅" if entrada["aceptada"] else "RECHAZADA ❌"
        print(f"{i}. Cadena: '{entrada['cadena']}' -> {estado} (Estado final: {entrada['estado_final']})")
    print("-" * 30)


# ========================== MENÚ PRINCIPAL ==========================
def mostrar_menu():
    """Muestra el menú principal."""
    print("\n" + "=" * 50)
    print("   MOTOR DE PARSING, VALIDACIÓN Y SIMULACIÓN DE AFD")
    print("=" * 50)
    print("1. Crear AFD manualmente")
    print("2. Cargar AFD desde archivo .txt")
    print("3. Mostrar definición formal del AFD")
    print("4. Mostrar tabla de transición")
    print("5. Validar la estructura del autómata")
    print("6. Evaluar una cadena")
    print("7. Evaluar un archivo de cadenas")
    print("8. Consultar historial de evaluaciones")
    print("9. Cargar o crear otro autómata")
    print("10. Salir")
    print("-" * 50)


def menu_principal():
    """Bucle principal del menú."""
    afd_actual = None

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            afd_actual = cargar_manual()
            print("\nAFD creado exitosamente.")
            input("Presione Enter para continuar...")

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
            print("\nSaliendo del programa. ¡Hasta luego!")
            break

        else:
            print("\nOpción no válida. Intente de nuevo.")
            input("Presione Enter para continuar...")


# ========================== PUNTO DE ENTRADA ==========================
if __name__ == "__main__":
    menu_principal()