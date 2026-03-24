import json
from jsonschema import validate, ValidationError
from typing import Dict, Any, Optional

class MetadataValidator:
    """Validates harvested metadata against predefined schemas and rules"""

    def __init__(self, schema_path: Optional[str] = None):
        self.schema = self._load_schema(schema_path) if schema_path else self._default_schema()

    def _load_schema(self, schema_path: str) -> Dict[str, Any]:
        """Load a custom JSON schema from file"""
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise ValueError(f'Failed to load schema from {schema_path}: {str(e)}')

    def _default_schema(self) -> Dict[str, Any]:
        """Provide a default schema for basic metadata validation"""
        return {
            'type': 'object',
            'required': ['id', 'timestamp', 'source'],
            'properties': {
                'id': {'type': 'string'},
                'timestamp': {'type': 'string', 'format': 'date-time'},
                'source': {'type': 'string'},
                'title': {'type': 'string'},
                'description': {'type': 'string'},
                'tags': {
                    'type': 'array',
                    'items': {'type': 'string'}
                },
                'properties': {
                    'type': 'object',
                    'additionalProperties': True
                }
            }
        }

    def validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate metadata against the schema
        Returns cleaned metadata if valid, raises ValidationError if invalid
        """
        try:
            validate(instance=metadata, schema=self.schema)
            return self._clean_metadata(metadata)
        except ValidationError as e:
            raise ValidationError(f'Metadata validation failed: {str(e)}')

    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and normalize metadata fields"""
        cleaned = metadata.copy()
        
        # Strip whitespace from string fields
        for key, value in cleaned.items():
            if isinstance(value, str):
                cleaned[key] = value.strip()
            elif isinstance(value, list) and all(isinstance(x, str) for x in value):
                cleaned[key] = [x.strip() for x in value]

        # Remove empty strings and None values
        return {k: v for k, v in cleaned.items() if v not in (None, '')}

    def bulk_validate(self, metadata_list: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Validate multiple metadata entries, returns list of valid entries"""
        valid_entries = []
        for entry in metadata_list:
            try:
                valid_entries.append(self.validate_metadata(entry))
            except ValidationError:
                continue
        return valid_entries