#!/usr/bin/env python3
"""
Cypher Standards Validator and Generator
Enforces coding standards and best practices for Cypher query generation
"""

import re
import yaml
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

@dataclass
class ValidationResult:
    level: ValidationLevel
    rule: str
    message: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

class CypherStandardsValidator:
    def __init__(self, standards_file: str = "cypher_standards.yaml"):
        """Initialize validator with standards configuration"""
        self.standards = self.load_standards(standards_file)
        self.validation_results: List[ValidationResult] = []
        
    def load_standards(self, standards_file: str) -> Dict[str, Any]:
        """Load standards configuration from YAML file"""
        try:
            with open(standards_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Standards file not found: {standards_file}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing standards file: {e}")
            return {}
    
    def validate_query(self, cypher_query: str) -> List[ValidationResult]:
        """Validate a Cypher query against standards"""
        self.validation_results = []
        lines = cypher_query.split('\n')
        
        # Run all validation checks
        self._validate_naming_conventions(cypher_query, lines)
        self._validate_query_structure(cypher_query, lines)
        self._validate_performance_patterns(cypher_query, lines)
        self._validate_security_patterns(cypher_query, lines)
        self._validate_custom_rules(cypher_query, lines)
        
        return self.validation_results
    
    def _validate_naming_conventions(self, query: str, lines: List[str]):
        """Validate naming conventions"""
        naming = self.standards.get('naming_conventions', {})
        
        # Check node label conventions
        node_pattern = r'\((\w+):(\w+)'
        for i, line in enumerate(lines):
            matches = re.findall(node_pattern, line)
            for var, label in matches:
                if not self._is_pascal_case(label):
                    self.validation_results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        rule="naming_conventions.nodes.label_case",
                        message=f"Node label '{label}' should be PascalCase",
                        line_number=i + 1,
                        suggestion=f"Use '{self._to_pascal_case(label)}' instead"
                    ))
                
                if len(label) > naming.get('nodes', {}).get('max_label_length', 50):
                    self.validation_results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        rule="naming_conventions.nodes.max_label_length",
                        message=f"Node label '{label}' exceeds maximum length",
                        line_number=i + 1
                    ))
        
        # Check relationship type conventions
        rel_pattern = r'-\[(\w*):(\w+)\]-'
        for i, line in enumerate(lines):
            matches = re.findall(rel_pattern, line)
            for var, rel_type in matches:
                if not self._is_upper_snake_case(rel_type):
                    self.validation_results.append(ValidationResult(
                        level=ValidationLevel.ERROR,
                        rule="naming_conventions.relationships.type_case",
                        message=f"Relationship type '{rel_type}' should be UPPER_SNAKE_CASE",
                        line_number=i + 1,
                        suggestion=f"Use '{self._to_upper_snake_case(rel_type)}' instead"
                    ))
        
        # Check property naming
        prop_pattern = r'\.(\w+)\s*[=:]'
        for i, line in enumerate(lines):
            matches = re.findall(prop_pattern, line)
            for prop in matches:
                if not self._is_snake_case(prop):
                    self.validation_results.append(ValidationResult(
                        level=ValidationLevel.WARNING,
                        rule="naming_conventions.properties.case",
                        message=f"Property '{prop}' should be snake_case",
                        line_number=i + 1,
                        suggestion=f"Use '{self._to_snake_case(prop)}' instead"
                    ))
    
    def _validate_query_structure(self, query: str, lines: List[str]):
        """Validate query structure and formatting"""
        structure = self.standards.get('query_structure', {})
        
        # Check for parameterized queries
        if structure.get('patterns', {}).get('require_parameters', True):
            if '$' not in query and 'parameters' not in query.lower():
                self.validation_results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    rule="query_structure.patterns.require_parameters",
                    message="Query should use parameters instead of hardcoded values",
                    suggestion="Use $parameter syntax for dynamic values"
                ))
        
        # Check for LIMIT clauses in potentially large result sets
        if 'MATCH' in query and 'LIMIT' not in query:
            self.validation_results.append(ValidationResult(
                level=ValidationLevel.INFO,
                rule="query_structure.patterns.default_limit",
                message="Consider adding LIMIT clause for large result sets",
                suggestion=f"Add 'LIMIT {structure.get('patterns', {}).get('default_limit', 1000)}'"
            ))
        
        # Check for dangerous DELETE operations
        if structure.get('validation', {}).get('disallow_delete_all', True):
            if re.search(r'DELETE\s+\w+\s*$', query, re.IGNORECASE | re.MULTILINE):
                self.validation_results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    rule="query_structure.validation.disallow_delete_all",
                    message="DELETE without WHERE clause is dangerous",
                    suggestion="Add WHERE clause to limit deletion scope"
                ))
        
        # Check line length
        max_length = structure.get('formatting', {}).get('max_line_length', 100)
        for i, line in enumerate(lines):
            if len(line) > max_length:
                self.validation_results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    rule="query_structure.formatting.max_line_length",
                    message=f"Line {i + 1} exceeds maximum length ({len(line)} > {max_length})",
                    line_number=i + 1
                ))
    
    def _validate_performance_patterns(self, query: str, lines: List[str]):
        """Validate performance-related patterns"""
        performance = self.standards.get('performance', {})
        
        # Check for potential Cartesian products
        match_count = len(re.findall(r'MATCH', query, re.IGNORECASE))
        where_count = len(re.findall(r'WHERE', query, re.IGNORECASE))
        
        if match_count > 1 and where_count == 0:
            self.validation_results.append(ValidationResult(
                level=ValidationLevel.WARNING,
                rule="performance.cartesian_product_risk",
                message="Multiple MATCH clauses without WHERE may cause Cartesian product",
                suggestion="Add WHERE clause to connect patterns"
            ))
        
        # Suggest indexes for frequently queried properties
        if performance.get('indexing', {}).get('auto_suggest', True):
            prop_pattern = r'WHERE\s+\w+\.(\w+)\s*='
            properties = re.findall(prop_pattern, query, re.IGNORECASE)
            for prop in set(properties):
                self.validation_results.append(ValidationResult(
                    level=ValidationLevel.INFO,
                    rule="performance.indexing.auto_suggest",
                    message=f"Consider creating index on property '{prop}'",
                    suggestion=f"CREATE INDEX FOR (n:NodeType) ON (n.{prop})"
                ))
    
    def _validate_security_patterns(self, query: str, lines: List[str]):
        """Validate security-related patterns"""
        security = self.standards.get('security', {})
        
        # Check for potential injection vulnerabilities
        if security.get('access_control', {}).get('prevent_injection', True):
            # Look for string concatenation in queries
            if '+' in query and '"' in query:
                self.validation_results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    rule="security.access_control.prevent_injection",
                    message="Potential SQL injection vulnerability detected",
                    suggestion="Use parameterized queries instead of string concatenation"
                ))
        
        # Check for sensitive data patterns
        sensitive_patterns = security.get('privacy', {}).get('sensitive_patterns', [])
        for pattern in sensitive_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                self.validation_results.append(ValidationResult(
                    level=ValidationLevel.WARNING,
                    rule="security.privacy.sensitive_data",
                    message=f"Potential sensitive data pattern detected: {pattern}",
                    suggestion="Ensure sensitive data is properly masked or encrypted"
                ))
    
    def _validate_custom_rules(self, query: str, lines: List[str]):
        """Validate custom rules defined in standards"""
        custom_rules = self.standards.get('validation_rules', {}).get('custom_rules', [])
        
        for rule in custom_rules:
            pattern = rule.get('pattern', '')
            required = rule.get('required', False)
            
            if required and not re.search(pattern, query):
                self.validation_results.append(ValidationResult(
                    level=ValidationLevel.ERROR,
                    rule=f"custom_rules.{rule.get('name')}",
                    message=rule.get('description', 'Custom rule violation'),
                    suggestion=f"Query should match pattern: {pattern}"
                ))
    
    def _is_pascal_case(self, text: str) -> bool:
        """Check if text is in PascalCase"""
        return re.match(r'^[A-Z][a-zA-Z0-9]*$', text) is not None
    
    def _is_snake_case(self, text: str) -> bool:
        """Check if text is in snake_case"""
        return re.match(r'^[a-z][a-z0-9_]*$', text) is not None
    
    def _is_upper_snake_case(self, text: str) -> bool:
        """Check if text is in UPPER_SNAKE_CASE"""
        return re.match(r'^[A-Z][A-Z0-9_]*$', text) is not None
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase"""
        return ''.join(word.capitalize() for word in re.split(r'[_\s]+', text))
    
    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        return re.sub(r'([A-Z])', r'_\1', text).lower().lstrip('_')
    
    def _to_upper_snake_case(self, text: str) -> str:
        """Convert text to UPPER_SNAKE_CASE"""
        return self._to_snake_case(text).upper()

class CypherGenerator:
    def __init__(self, standards_file: str = "cypher_standards.yaml"):
        """Initialize generator with standards configuration"""
        self.standards = self.load_standards(standards_file)
        self.validator = CypherStandardsValidator(standards_file)
        
    def load_standards(self, standards_file: str) -> Dict[str, Any]:
        """Load standards configuration from YAML file"""
        try:
            with open(standards_file, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Standards file not found: {standards_file}")
            return {}
    
    def generate_create_node_query(self, node_type: str, properties: Dict[str, Any]) -> str:
        """Generate standardized node creation query"""
        template = self.standards.get('templates', {}).get('create_node', '')
        
        # Format properties according to standards
        formatted_props = []
        for key, value in properties.items():
            formatted_key = self._format_property_name(key)
            if isinstance(value, str):
                formatted_props.append(f"{formatted_key}: ${formatted_key}")
            else:
                formatted_props.append(f"{formatted_key}: ${formatted_key}")
        
        query = template.format(
            node_type=self._format_node_label(node_type),
            properties=',\n      '.join(formatted_props)
        )
        
        return self._format_query(query)
    
    def generate_create_relationship_query(self, source_type: str, target_type: str, 
                                         relationship_type: str, **kwargs) -> str:
        """Generate standardized relationship creation query"""
        template = self.standards.get('templates', {}).get('create_relationship', '')
        
        query = template.format(
            source_type=self._format_node_label(source_type),
            target_type=self._format_node_label(target_type),
            relationship_type=self._format_relationship_type(relationship_type),
            source_property=kwargs.get('source_property', 'id'),
            target_property=kwargs.get('target_property', 'id'),
            source_param=kwargs.get('source_param', 'source_id'),
            target_param=kwargs.get('target_param', 'target_id')
        )
        
        return self._format_query(query)
    
    def generate_search_query(self, node_type: str, search_field: str, **kwargs) -> str:
        """Generate standardized search query"""
        template = self.standards.get('templates', {}).get('search_pattern', '')
        
        query = template.format(
            node_type=self._format_node_label(node_type),
            search_field=self._format_property_name(search_field),
            search_param=kwargs.get('search_param', 'search_term'),
            order_field=kwargs.get('order_field', 'created_date'),
            limit=kwargs.get('limit', '${limit}')
        )
        
        return self._format_query(query)
    
    def validate_and_fix_query(self, query: str) -> Tuple[str, List[ValidationResult]]:
        """Validate query and attempt to fix common issues"""
        validation_results = self.validator.validate_query(query)
        fixed_query = query
        
        # Apply automatic fixes for common issues
        for result in validation_results:
            if result.level == ValidationLevel.ERROR and result.suggestion:
                # Apply simple fixes
                if "should be PascalCase" in result.message:
                    # Fix node label casing
                    pass  # Would need more sophisticated parsing
                elif "should be UPPER_SNAKE_CASE" in result.message:
                    # Fix relationship type casing
                    pass  # Would need more sophisticated parsing
        
        return fixed_query, validation_results
    
    def _format_node_label(self, label: str) -> str:
        """Format node label according to standards"""
        return self._to_pascal_case(label)
    
    def _format_relationship_type(self, rel_type: str) -> str:
        """Format relationship type according to standards"""
        return self._to_upper_snake_case(rel_type)
    
    def _format_property_name(self, prop_name: str) -> str:
        """Format property name according to standards"""
        return self._to_snake_case(prop_name)
    
    def _format_query(self, query: str) -> str:
        """Format query according to standards"""
        # Apply basic formatting
        lines = query.split('\n')
        formatted_lines = []
        
        for line in lines:
            # Remove extra whitespace
            line = line.strip()
            if line:
                formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase"""
        return ''.join(word.capitalize() for word in re.split(r'[_\s]+', text))
    
    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        return re.sub(r'([A-Z])', r'_\1', text).lower().lstrip('_')
    
    def _to_upper_snake_case(self, text: str) -> str:
        """Convert text to UPPER_SNAKE_CASE"""
        return self._to_snake_case(text).upper()

# Example usage and testing
if __name__ == "__main__":
    # Test the validator
    validator = CypherStandardsValidator()
    
    test_query = """
    CREATE (author:author {name: "John Doe", Email: "john@example.com"})
    MATCH (a:article)-[wrote]->(b:Author)
    DELETE a
    """
    
    results = validator.validate_query(test_query)
    
    print("Validation Results:")
    for result in results:
        print(f"{result.level.value.upper()}: {result.message}")
        if result.suggestion:
            print(f"  Suggestion: {result.suggestion}")
        print()
    
    # Test the generator
    generator = CypherGenerator()
    
    node_query = generator.generate_create_node_query("Author", {
        "name": "John Doe",
        "email": "john@example.com",
        "specialization": "Healthcare"
    })
    
    print("Generated Node Creation Query:")
    print(node_query)