"""Excepciones personalizadas del proyecto."""

class DownloadError(Exception):
    """Error al descargar un recurso remoto."""


class SchemaValidationError(Exception):
    """Esquema de datos inválido o faltante."""


class DataValidationError(Exception):
    """Datos inválidos (tipos, rangos, nulos críticos)."""
