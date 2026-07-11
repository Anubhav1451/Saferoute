from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable


@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    field_errors: Dict[str, List[str]] = field(default_factory=dict)

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        for field, errs in other.field_errors.items():
            self.field_errors.setdefault(field, []).extend(errs)
        return self


class BaseValidator(ABC):
    @abstractmethod
    def validate(self, value: Any, field_name: str, row: Dict[str, Any]) -> Optional[str]:
        pass


class NotNullValidator(BaseValidator):
    def validate(self, value: Any, field_name: str, row: Dict[str, Any]) -> Optional[str]:
        if value is None:
            return f"{field_name} is required"
        if isinstance(value, str) and not value.strip():
            return f"{field_name} must not be empty"
        return None


class RangeValidator(BaseValidator):
    def __init__(self, min_val: Optional[float] = None, max_val: Optional[float] = None):
        self.min_val = min_val
        self.max_val = max_val

    def validate(self, value: Any, field_name: str, row: Dict[str, Any]) -> Optional[str]:
        if value is None:
            return None
        try:
            v = float(value)
            if self.min_val is not None and v < self.min_val:
                return f"{field_name}={v} is below minimum {self.min_val}"
            if self.max_val is not None and v > self.max_val:
                return f"{field_name}={v} exceeds maximum {self.max_val}"
        except (TypeError, ValueError):
            return f"{field_name}={value} is not a valid number"
        return None


class RegexValidator(BaseValidator):
    def __init__(self, pattern: str, message: Optional[str] = None):
        import re
        self._pattern = re.compile(pattern)
        self._message = message

    def validate(self, value: Any, field_name: str, row: Dict[str, Any]) -> Optional[str]:
        if value is None:
            return None
        if not self._pattern.match(str(value)):
            return self._message or f"{field_name}={value} does not match pattern {self._pattern.pattern}"
        return None


class ChoiceValidator(BaseValidator):
    def __init__(self, choices: List[str], case_sensitive: bool = False):
        self._choices = choices
        self._case_sensitive = case_sensitive

    def validate(self, value: Any, field_name: str, row: Dict[str, Any]) -> Optional[str]:
        if value is None:
            return None
        v = str(value) if self._case_sensitive else str(value).lower()
        valid = self._choices if self._case_sensitive else [c.lower() for c in self._choices]
        if v not in valid:
            return f"{field_name}={value} is not in allowed choices: {self._choices}"
        return None


class ConditionalValidator(BaseValidator):
    def __init__(self, condition: Callable[[Dict[str, Any]], bool],
                 field_name: str, validator: BaseValidator):
        self._condition = condition
        self._field_name = field_name
        self._validator = validator

    def validate(self, value: Any, field_name: str, row: Dict[str, Any]) -> Optional[str]:
        if self._condition(row):
            return self._validator.validate(value, self._field_name, row)
        return None


class ValidatorRegistry:
    def __init__(self):
        self._rules: Dict[str, List[BaseValidator]] = {}
        self._global_rules: List[BaseValidator] = []

    def add_rule(self, field_name: str, validator: BaseValidator):
        self._rules.setdefault(field_name, []).append(validator)

    def add_global_rule(self, validator: BaseValidator):
        self._global_rules.append(validator)

    def validate(self, row: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult()
        for field_name, validators in self._rules.items():
            value = row.get(field_name)
            for v in validators:
                err = v.validate(value, field_name, row)
                if err:
                    result.is_valid = False
                    result.errors.append(err)
                    result.field_errors.setdefault(field_name, []).append(err)
        for v in self._global_rules:
            err = v.validate(None, "_global", row)
            if err:
                result.is_valid = False
                result.errors.append(err)
        return result
