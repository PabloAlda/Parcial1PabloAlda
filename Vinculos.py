import csv
import json

class Persona:
    def __init__(self, id_, nombre, padre_id=None, madre_id=None):
        self.id = id_
        self.nombre = nombre
        self.padre_id = padre_id if padre_id else None
        self.madre_id = madre_id if madre_id else None


class ArbolGenealogico:
    def __init__(self):
        self.personas = {}
        self.uniones = []
        self.max_generaciones = 2  # límite configurable

    # ---------------------------
    # CARGA DE DATOS
    # ---------------------------
    def cargar_personas(self, nombre_archivo):
        with open(nombre_archivo, newline='', encoding='utf-8') as f:
            lector = csv.DictReader(f)
            for fila in lector:
                id_ = fila['id'].strip()
                nombre = fila['nombre'].strip()
                padre_id = fila['padre_id'].strip() if fila['padre_id'] else None
                madre_id = fila['madre_id'].strip() if fila['madre_id'] else None
                self.personas[id_] = Persona(id_, nombre, padre_id, madre_id)

    def cargar_uniones(self, nombre_archivo):
        lineas = []
        with open(nombre_archivo, encoding='utf-8') as f:
            for linea in f:
                linea = linea.split('#')[0].strip()  # elimina comentarios
                if linea:
                    lineas.append(linea)
        lector = csv.DictReader(lineas)
        for fila in lector:
            p1 = fila['persona_a'].strip()
            p2 = fila['persona_b'].strip()
            self.uniones.append((p1, p2))

    # ---------------------------
    # RELACIONES FAMILIARES
    # ---------------------------
    def obtener_nombre(self, id_):
        return self.personas[id_].nombre if id_ in self.personas else f"Desconocido({id_})"

    def es_asc_desc(self, a, b):
        """True si a es ascendiente o descendiente de b."""
        return self._es_asc(a, b) or self._es_asc(b, a)

    def _es_asc(self, asc, desc):
        if not asc or not desc:
            return False
        padre = self.personas[desc].padre_id
        madre = self.personas[desc].madre_id
        if asc == padre or asc == madre:
            return True
        return (padre and self._es_asc(asc, padre)) or (madre and self._es_asc(asc, madre))

    def son_hermanos(self, a, b):
        pa, ma = self.personas[a].padre_id, self.personas[a].madre_id
        pb, mb = self.personas[b].padre_id, self.personas[b].madre_id
        return pa and ma and pa == pb and ma == mb

    def ancestros(self, id_, k):
        """Devuelve el conjunto de ancestros hasta k generaciones."""
        resultado = set()
        self._ancestros_rec(id_, k, resultado)
        return resultado

    def _ancestros_rec(self, id_, k, resultado):
        if k == 0 or id_ not in self.personas:
            return
        persona = self.personas[id_]
        for padre in [persona.padre_id, persona.madre_id]:
            if padre:
                resultado.add(padre)
                self._ancestros_rec(padre, k - 1, resultado)

    # ---------------------------
    # VALIDACIÓN DE UNIONES
    # ---------------------------
    def validar_uniones(self):
        resultados = []

        for a, b in self.uniones:
            nombre_a = self.obtener_nombre(a)
            nombre_b = self.obtener_nombre(b)
            estado = "OK"
            motivo = ""

            # a) ascendiente/descendiente
            if self.es_asc_desc(a, b):
                estado = "NO PERMITIDO"
                motivo = f"Relación ascendiente/descendiente entre {nombre_a} y {nombre_b}"

            # b) hermanos
            elif self.son_hermanos(a, b):
                estado = "NO PERMITIDO"
                motivo = f"Son hermanos ({nombre_a} y {nombre_b})"

            # c) comparten ancestro en ≤ k generaciones
            else:
                anc_a = self.ancestros(a, self.max_generaciones)
                anc_b = self.ancestros(b, self.max_generaciones)
                comunes = anc_a.intersection(anc_b)
                if comunes:
                    nombres_comunes = [self.obtener_nombre(x) for x in comunes]
                    estado = "NO PERMITIDO"
                    motivo = f"Comparten ancestro en ≤ {self.max_generaciones} generaciones: {nombres_comunes}"

            resultados.append({
                "persona_a": nombre_a,
                "persona_b": nombre_b,
                "estado": estado,
                "motivo": motivo
            })

        return resultados

    # ---------------------------
    # SALIDA
    # ---------------------------
    def imprimir_resultados(self, resultados):
        for r in resultados:
            print(f"{r['persona_a']} - {r['persona_b']}: {r['estado']}. {r['motivo']}")

    def guardar_json(self, resultados, nombre_archivo="resultado.json"):
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=4)
        print(f"\n✅ Resultados guardados en {nombre_archivo}")


# ---------------------------
# EJECUCIÓN PRINCIPAL
# ---------------------------
if __name__ == "__main__":
    arbol = ArbolGenealogico()
    arbol.cargar_personas("personas.csv")
    arbol.cargar_uniones("uniones.csv")
    resultados = arbol.validar_uniones()
    arbol.imprimir_resultados(resultados)
    arbol.guardar_json(resultados)
