# pylint: disable=missing-module-docstring

import json
import re
from typing import List, Dict, Tuple, Union, Optional

FACTORES_DIGITO_VERIFICADOR: List[int] = [2, 3, 4, 5, 6, 7]
MODULO_DIGITO_VERIFICADOR: int = 11
RUT_REGEX: str = r"^(\d{1,8}(?:.\d{3})*)(-([0-9kK]))?$"


class RutInvalidoError(Exception):
    """Lanzada cuando el RUT ingresado es inválido."""


def calcular_digito_verificador(base_numerica: str) -> str:
    """
    Calcula el dígito verificador del RUT de forma optimizada.
    
    Args:
        base_numerica (str): El número base del RUT sin puntos ni guiones.
        
    Returns:
        str: El dígito verificador del RUT.
    """
    suma_parcial: int = 0
    factor_index: int = 0
    
    # Iteramos desde el final hacia adelante sin crear string reversed
    for i in range(len(base_numerica) - 1, -1, -1):
        digito: int = int(base_numerica[i])
        suma_parcial += digito * FACTORES_DIGITO_VERIFICADOR[factor_index % 6]
        factor_index += 1
    
    digito_verificador: int = (
        MODULO_DIGITO_VERIFICADOR - suma_parcial % MODULO_DIGITO_VERIFICADOR
    ) % MODULO_DIGITO_VERIFICADOR
    
    return str(digito_verificador) if digito_verificador < 10 else "k"


class RutBase:
    """Representa el número base de un RUT chileno."""

    def __init__(self, base: str):
        self.rut_original: str = base
        self.base: str = self.validar_y_normalizar_base(base)

    def validar_y_normalizar_base(self, base: str) -> str:
        """
        Valida y normaliza el número base.

        Args:
            base (str): El número base del RUT.

        Returns:
            str: El número base normalizado.

        Raises:
            RutInvalidoError: Si el número base es inválido.
        """
        # Validación más robusta
        if not base or not isinstance(base, str):
            raise RutInvalidoError(f"El número base '{base}' no es válido.")
            
        if not re.match(r"^\d{1,3}(?:\.\d{3})*$", base) and not base.isdigit():
            raise RutInvalidoError(f"El número base '{base}' no es válido.")

        base_normalizada: str = base.replace(".", "").lstrip("0")
        
        # Manejar caso donde todos son ceros
        if not base_normalizada:
            base_normalizada = "0"
            
        if len(base_normalizada) > 8:
            raise RutInvalidoError(
                f"El rut '{self.rut_original}' es inválido ya que contiene más de 8 dígitos."
            )

        return base_normalizada

    def __str__(self) -> str:
        return self.base


class Rut:
    """
    Representa un RUT chileno.

    Atributos:
        rut_string (str): El RUT en formato string.
        base (RutBase): El número base del RUT.
        digito_verificador (str): El dígito verificador del RUT.

    Métodos:
        formatear: Formatea el RUT según las opciones especificadas.
        formatear_lista_ruts: Formatea una lista de RUTs según las opciones especificadas.
    """

    PATRON_RUT = re.compile(RUT_REGEX)

    def __init__(self, rut: str):
        self.rut_string: str = str(rut).strip()
        
        # Ejecutar regex una sola vez y guardar resultado
        self._match_result = self._validar_formato_rut()
        self.base_string: str = self._match_result.group(1)
        
        # Calcular dígito verificador sin crear objetos innecesarios
        self.digito_verificador: str = calcular_digito_verificador(
            self.base_string.replace(".", "")
        )
        
        # Validar después de calcular
        self._validar_digito_verificador()
        
        # Crear objeto base solo una vez
        self.base = RutBase(self.base_string)

    def _validar_formato_rut(self) -> re.Match:
        """
        Valida el formato del RUT y retorna el match object.
        
        Returns:
            re.Match: El objeto match de la validación.
            
        Raises:
            RutInvalidoError: Si el formato es inválido.
        """
        match = Rut.PATRON_RUT.fullmatch(self.rut_string)
        if not match:
            raise RutInvalidoError(
                f"El formato del RUT '{self.rut_string}' es inválido."
            )
        return match

    def _validar_digito_verificador(self) -> None:
        """
        Valida que el dígito verificador proporcionado coincida con el calculado.
        
        Raises:
            RutInvalidoError: Si el dígito verificador no coincide.
        """
        # Usar el match ya calculado
        digito_verificador_input = (
            self._match_result.group(3).lower() 
            if self._match_result.group(3) 
            else None
        )

        if (
            digito_verificador_input
            and digito_verificador_input != self.digito_verificador
        ):
            raise RutInvalidoError(
                f"El dígito verificador '{digito_verificador_input}' no coincide con "
                f"el dígito verificador calculado '{self.digito_verificador}'."
            )

    def __str__(self) -> str:
        return f"{self.base}-{self.digito_verificador}"

    def formatear(self, separador_miles: bool = False, mayusculas: bool = False) -> str:
        """
        Formatea el RUT según las opciones especificadas.

        Args:
            separador_miles (bool, optional): Si se deben agregar separadores de miles (puntos).
            mayusculas (bool, optional): Si los RUTs deben estar en mayúsculas.

        Returns:
            str: El RUT formateado.
        """
        rut = str(self)
        if separador_miles:
            rut = (
                self._agregar_separador_miles(rut.split("-", maxsplit=1)[0])
                + "-"
                + rut.split("-")[1]
            )

        if mayusculas:
            rut = rut.upper()

        return rut

    @staticmethod
    def _agregar_separador_miles(numero: str) -> str:
        return f"{int(numero):,}".replace(",", ".")

    @staticmethod
    def _validar_lista_ruts(ruts: List[str]) -> Dict[str, List[Union[str, Tuple[str, str]]]]:
        """
        Optimización en validación de listas
        """
        validos: List[str] = []
        invalidos: List[Tuple[str, str]] = []
        
        for rut_string in ruts:
            try:
                # Solo crear objeto Rut si es necesario para el resultado final
                rut_obj = Rut(rut_string)
                validos.append(str(rut_obj))
            except RutInvalidoError as e:
                invalidos.append((rut_string, str(e)))
                
        return {"validos": validos, "invalidos": invalidos}

    @staticmethod
    def _formatear_csv(ruts_formateados: List[str]) -> str:
        cadena_ruts: str = "\n".join(ruts_formateados)
        return f"rut\n{cadena_ruts}"

    @staticmethod
    def _formatear_xml(ruts_formateados: List[str]) -> str:
        xml_lines: List[str] = ["<root>"]
        for rut in ruts_formateados:
            xml_lines.append(f"    <rut>{rut}</rut>")
        xml_lines.append("</root>")
        return "\n".join(xml_lines)

    @staticmethod
    def _formatear_json(ruts_formateados: List[str]) -> str:
        """
        Generar JSON válido usando json.dumps
        """
        ruts_json: List[Dict[str, str]] = [{"rut": rut} for rut in ruts_formateados]
        return json.dumps(ruts_json, indent=2, ensure_ascii=False)

    @staticmethod
    def formatear_lista_ruts(
        ruts: List[str],
        separador_miles: bool = False,
        mayusculas: bool = False,
        formato: Optional[str] = None,
    ) -> str:
        """
        Formatea una lista de RUTs según las opciones especificadas.

        Args:
            ruts (List[str]): Una lista de RUTs en formato string o numérico.
            separador_miles (bool, opcional): Si se deben agregar separadores de miles (puntos).
            mayusculas (bool, opcional): Si los RUTs deben estar en mayúsculas.
            formato (str, opcional): El formato de salida deseado (csv, json, xml, None).

        Returns:
            str: Una cadena con los RUTs válidos e inválidos formateados según las opciones
                especificadas.
        """
        formato_salida: Dict[str, callable] = {
            "csv": Rut._formatear_csv,
            "xml": Rut._formatear_xml,
            "json": Rut._formatear_json,
        }
        
        ruts_validos_invalidos = Rut._validar_lista_ruts(ruts)
        ruts_validos: List[str] = ruts_validos_invalidos["validos"]
        ruts_invalidos: List[Tuple[str, str]] = ruts_validos_invalidos["invalidos"]

        resultado: str = ""
        if ruts_validos:
            # Evitar recrear objetos Rut innecesariamente
            ruts_validos_formateados: List[str] = []
            for rut_string in ruts_validos:
                try:
                    rut_obj = Rut(rut_string)
                    ruts_validos_formateados.append(
                        rut_obj.formatear(separador_miles, mayusculas)
                    )
                except RutInvalidoError:
                    # Este caso no debería ocurrir ya que los RUTs ya fueron validados
                    continue
                    
            resultado += "RUTs válidos:\n"
            if formato in formato_salida:
                resultado += formato_salida[formato](ruts_validos_formateados)
            else:
                resultado += "\n".join(ruts_validos_formateados)
            resultado += "\n\n"

        if ruts_invalidos:
            resultado += "RUTs inválidos:\n"
            for rut, error in ruts_invalidos:
                resultado += f"{rut} - {error}\n"

        return resultado