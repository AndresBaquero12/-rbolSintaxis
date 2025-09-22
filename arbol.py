import re
import matplotlib.pyplot as plt
import networkx as nx

class NodoArbol:
    def __init__(self, tipo, valor=None, hijos=None):
        self.tipo = tipo
        self.valor = valor
        self.hijos = hijos if hijos else []
        self.id = id(self)

    def __str__(self):
        return self._formatear_arbol()

    def _formatear_arbol(self, nivel=0):
        sangria = "  " * nivel
        texto_nodo = f"{sangria}{self.tipo}"
        if self.valor is not None:
            texto_nodo += f": {self.valor}"
        texto_nodo += "\n"
        for hijo in self.hijos:
            texto_nodo += hijo._formatear_arbol(nivel + 1)
        return texto_nodo

    def a_grafo_networkx(self, grafo=None, padre_id=None):
        if grafo is None:
            grafo = nx.DiGraph()
        
        etiqueta = self.tipo
        if self.valor is not None:
            etiqueta += f"\n{self.valor}"
        
        grafo.add_node(self.id, label=etiqueta)
        
        if padre_id is not None:
            grafo.add_edge(padre_id, self.id)
        
        for hijo in self.hijos:
            hijo.a_grafo_networkx(grafo, self.id)
        
        return grafo

class AnalizadorSintactico:
    def __init__(self, archivo_gramatica):
        self.gramatica = self._leer_gramatica(archivo_gramatica)
        self.tokens = []
        self.posicion_actual = 0

    def _leer_gramatica(self, archivo):
        reglas_gramatica = {}
        try:
            with open(archivo, 'r', encoding='utf-8') as archivo:
                for linea in archivo:
                    linea = linea.strip()
                    if not linea or '->' not in linea:
                        continue
                    parte_izquierda, parte_derecha = linea.split('->', 1)
                    parte_izquierda = parte_izquierda.strip()
                    parte_derecha = parte_derecha.strip()
                    if parte_izquierda not in reglas_gramatica:
                        reglas_gramatica[parte_izquierda] = []
                    reglas_gramatica[parte_izquierda].append(parte_derecha.split())
        except FileNotFoundError:
            raise ValueError(f"Archivo '{archivo}' no encontrado")
        return reglas_gramatica

    def _dividir_en_tokens(self, cadena):
        patrones_tokens = [
            (r'\+', 'opsuma'),
            (r'-', 'opsuma'),
            (r'\*', 'opmul'),
            (r'\/', 'opmul'),
            (r'\(', 'pari'),
            (r'\)', 'pard'),
            (r'[a-zA-Z_][a-zA-Z0-9_]*', 'id'),
            (r'[0-9]+(?:\.[0-9]+)?', 'num'),
            (r'\s+', None)
        ]

        tokens_encontrados = []
        cadena_restante = cadena
        
        while cadena_restante:
            coincidencia_encontrada = None
            for patron, tipo_token in patrones_tokens:
                expresion_regular = re.compile(patron)
                coincidencia_encontrada = expresion_regular.match(cadena_restante)
                if coincidencia_encontrada:
                    valor_token = coincidencia_encontrada.group(0)
                    if tipo_token:
                        tokens_encontrados.append((tipo_token, valor_token))
                    cadena_restante = cadena_restante[coincidencia_encontrada.end():]
                    break

            if not coincidencia_encontrada:
                raise ValueError(f"Carácter no reconocido: '{cadena_restante[0]}'")

        return tokens_encontrados

    def analizar(self, cadena_expresion):
        self.tokens = self._dividir_en_tokens(cadena_expresion)
        self.posicion_actual = 0
        arbol_sintaxis = self._E()
        
        if self.posicion_actual < len(self.tokens):
            token_extra = self.tokens[self.posicion_actual]
            raise ValueError(f"Tokens adicionales: '{token_extra[1]}'")
        
        return arbol_sintaxis

    def _obtener_token_actual(self):
        if self.posicion_actual < len(self.tokens):
            return self.tokens[self.posicion_actual]
        return None

    def _consumir_token(self, tipo_esperado):
        if self.posicion_actual >= len(self.tokens):
            raise ValueError("Fin inesperado de la entrada")

        tipo_actual, valor_actual = self.tokens[self.posicion_actual]

        if tipo_actual != tipo_esperado:
            raise ValueError(f"Se esperaba '{tipo_esperado}', se encontró '{tipo_actual}'")

        self.posicion_actual += 1
        return NodoArbol(tipo_actual, valor_actual)

    def _E(self):
        nodo_actual = self._T()
        while self._obtener_token_actual() and self._obtener_token_actual()[0] == 'opsuma':
            operador = self._consumir_token('opsuma')
            termino_derecho = self._T()
            nodo_actual = NodoArbol("E", hijos=[nodo_actual, operador, termino_derecho])
        return nodo_actual

    def _T(self):
        nodo_actual = self._F()
        while self._obtener_token_actual() and self._obtener_token_actual()[0] == 'opmul':
            operador = self._consumir_token('opmul')
            factor_derecho = self._F()
            nodo_actual = NodoArbol("T", hijos=[nodo_actual, operador, factor_derecho])
        return nodo_actual

    def _F(self):
        token_actual = self._obtener_token_actual()
        if not token_actual:
            raise ValueError("Se esperaba un factor")

        tipo_token, valor_token = token_actual

        if tipo_token == 'id':
            return self._consumir_token('id')
        elif tipo_token == 'num':
            return self._consumir_token('num')
        elif tipo_token == 'pari':
            self._consumir_token('pari')
            expresion_interior = self._E()
            self._consumir_token('pard')
            return NodoArbol("F", hijos=[
                NodoArbol("pari", "("),
                expresion_interior,
                NodoArbol("pard", ")")
            ])
        else:
            raise ValueError(f"Factor inválido: '{valor_token}'")

    def visualizar_arbol(self, cadena_expresion, nombre_archivo=None):
        try:
            arbol = self.analizar(cadena_expresion)
            grafo = arbol.a_grafo_networkx()
            
            plt.figure(figsize=(10, 6))
            pos = nx.spring_layout(grafo, seed=42)
            
            etiquetas = nx.get_node_attributes(grafo, 'label')
            
            nx.draw(grafo, pos, 
                   labels=etiquetas, 
                   with_labels=True, 
                   node_size=2000, 
                   node_color='lightblue', 
                   font_size=8, 
                   font_weight='bold',
                   arrows=False)
            
            plt.title(f"Árbol de Sintaxis: {cadena_expresion}")
            
            if nombre_archivo:
                plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
                print(f"Imagen guardada: {nombre_archivo}")
            
            plt.show()
            return arbol
            
        except Exception as error:
            print(f"Error al visualizar: {error}")
            return None

def ejecutar_principal():
    print("Analisador arbol sintaxis")
    print("=" * 50)
    
    analizador = AnalizadorSintactico("gra.txt")
    
    try:
        with open("prueba.txt", "r", encoding='utf-8') as archivo:
            for numero_linea, linea in enumerate(archivo, 1):
                expresion = linea.strip()
                if not expresion or expresion.startswith('#'):
                    continue
                
                print(f"\n🔍 EXPRESIÓN {numero_linea}: {expresion}")
                print("-" * 30)
                
                try:
                    # Visualizar como imagen
                    archivo_imagen = f"arbol_{numero_linea}.png"
                    arbol = analizador.visualizar_arbol(expresion, archivo_imagen)
                    
                    if arbol:
                        print("✅ Árbol generado correctamente")
                        print(arbol)
                        
                except Exception as error:
                    print(f"❌ ERROR: {error}")
                    
    except FileNotFoundError:
        print("❌ No se encontró 'prueba.txt'")
    except Exception as error_general:
        print(f"❌ Error inesperado: {error_general}")

if __name__ == "__main__":
    ejecutar_principal()
