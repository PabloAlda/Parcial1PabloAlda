#!/usr/bin/env python3
# verificador_uniones.py
import csv
import json
import sys
from collections import deque, defaultdict

# ---- CONFIG / NOMBRES DE ARCHIVOS ----
PERSONAS_CSV = "personas.csv"
UNIONES_CSV = "uniones.csv"
PARAMS_CSV = "parametros.csv"
OUTPUT_JSON = "resultado_uniones.json"

# ---- CARGA CSV ----
def leer_parametros(path):
    params = {}
    try:
        with open(path, newline='', encoding='utf-8') as f:
            r = csv.reader(f)
            for row in r:
                if not row or len(row) < 2: 
                    continue
                clave = row[0].strip()
                valor = row[1].strip()
                # intentar convertir a entero
                try:
                    valor = int(valor)
                except:
                    pass
                params[clave] = valor
    except FileNotFoundError:
        print(f"Atención: no encontrado {path}. Usando valores por defecto.")
    return params

def cargar_personas(path):
    personas = {}
    try:
        with open(path, newline='', encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                pid = row.get('id') or row.get('ID') or row.get('Id')
                if pid is None:
                    continue
                personas[pid] = row  # guardamos la fila completa por si hace falta nombre u otros datos
    except FileNotFoundError:
        print(f"Error: no existe {path}")
        sys.exit(1)
    return personas

def cargar_uniones(path):
    # esperamos filas con: id_union, padre, madre, hijo
    uniones = []
    try:
        with open(path, newline='', encoding='utf-8') as f:
            r = csv.DictReader(f)
            for row in r:
                uniones.append(row)
    except FileNotFoundError:
        print(f"Error: no existe {path}")
        sys.exit(1)
    return uniones

# ---- CONSTRUCCIÓN DE GRAFOS ----
def construir_grafos(uniones):
    padres = defaultdict(list)   # hijo -> [padre, madre]
    hijos = defaultdict(set)     # persona -> set(hijos)
    parejas = set()              # conjunto de pares (a,b) que aparecen como pareja

    for u in uniones:
        padre = u.get('padre') or u.get('Padre')
        madre = u.get('madre') or u.get('Madre')
        hijo  = u.get('hijo')  or u.get('Hijo')
        # si el archivo tiene id_union y una fila por hijo, OK
        if hijo:
            if padre: 
                padres[hijo].append(padre)
                hijos[padre].add(hijo)
            if madre:
                padres[hijo].append(madre)
                hijos[madre].add(hijo)
        # registrar la pareja
        if padre and madre:
            parejas.add((padre, madre))
            parejas.add((madre, padre))
    return padres, hijos, parejas

# ---- RECORRIDOS ----
def ancestros(persona, padres_map, k):
    """Devuelve set de ancestros de 'persona' hasta k generaciones.
       Generacion 1 = padres directos, generacion 2 = padres de padres, etc."""
    resultado = set()
    if persona is None:
        return resultado
    q = deque()
    # (node, nivel) nivel 0 = la persona misma; padres están a nivel 1
    q.append((persona, 0))
    visited = set([persona])
    while q:
        node, nivel = q.popleft()
        if nivel >= k:
            continue
        # buscar padres del nodo
        for p in padres_map.get(node, []):
            if p not in resultado:
                resultado.add(p)
            if p not in visited:
                visited.add(p)
                q.append((p, nivel+1))
    return resultado

def es_ancestro(a, b, padres_map):
    """True si a es ancestro de b en cualquier número de generaciones (bucle protegido)."""
    if a == b:
        return False
    # DFS/BFS subiendo
    q = deque([b])
    visited = set([b])
    while q:
        node = q.popleft()
        for p in padres_map.get(node, []):
            if p == a:
                return True
            if p not in visited:
                visited.add(p)
                q.append(p)
    return False

def son_hermanos(a, b, padres_map):
    if a == b:
        return False
    pa = set(padres_map.get(a, []))
    pb = set(padres_map.get(b, []))
    return len(pa.intersection(pb)) > 0

# ---- VALIDACIÓN ----
def validar_union(a, b, padres_map, max_gen):
    # regla a) asc/desc
    if es_ancestro(a, b, padres_map) or es_ancestro(b, a, padres_map):
        return (False, "Ascendiente/descendiente directo")
    # regla b) hermanos
    if son_hermanos(a, b, padres_map):
        return (False, "Hermanos (comparten padre/madre conocido)")
    # regla c) comparten ancestro en <= k generaciones
    anc_a = ancestros(a, padres_map, max_gen)
    anc_b = ancestros(b, padres_map, max_gen)
    inter = anc_a.intersection(anc_b)
    if inter:
        return (False, f"Comparten ancestro en ≤{max_gen} generaciones: {', '.join(sorted(inter))}")
    # si pasa todo: permitido
    return (True, "OK")

# ---- MAIN ----
def main():
    params = leer_parametros(PARAMS_CSV)
    max_gen = params.get('max_generaciones', 3)  # por defecto 3
    personas = cargar_personas(PERSONAS_CSV)
    uniones = cargar_uniones(UNIONES_CSV)

    padres_map, hijos_map, parejas = construir_grafos(uniones)

    resultados = []
    # asumimos que UNIONES_CSV contiene filas con la pareja (padre,madre). Recorremos parejas detectadas
    parejas_list = set()
    for u in uniones:
        padre = u.get('padre') or u.get('Padre')
        madre = u.get('madre') or u.get('Madre')
        if padre and madre:
            parejas_list.add((padre, madre))

    print(f"Validando uniones (max_generaciones={max_gen})\n")
    for a, b in sorted(parejas_list):
        permitido, motivo = validar_union(a, b, padres_map, max_gen)
        estado = "OK" if permitido else "NO"
        fila = {
            "pareja": [a, b],
            "estado": estado,
            "motivo": motivo
        }
        resultados.append(fila)
        print(f"{a} + {b} -> {estado} ({motivo})")

    # guardar JSON opcional
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as jf:
        json.dump({"max_generaciones": max_gen, "resultados": resultados}, jf, ensure_ascii=False, indent=2)
    print(f"\nGuardado JSON en {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
