# Translation Validation

Автоматическая валидация переводов для обеспечения корректности ICU placeholders и качества переводов.

## Обзор

TranslateGemma CLI включает двухуровневую систему защиты качества переводов:

1. **Промпт-инжиниринг** - Инструкции модели сохранять placeholders
2. **Post-processing валидация** - Проверка результата после перевода

## Промпт-инжиниринг

### Автоматическое добавление инструкций

Когда текст содержит `{placeholders}`, автоматически добавляется инструкция:

```
[IMPORTANT: Keep all {placeholders} EXACTLY as they are.
Do NOT translate words inside {curly braces}.
Translate only the text outside placeholders.]

Hello {name}
```

### Для batch-переводов

Инструкция добавляется один раз для всего батча:

```
[IMPORTANT: Keep all {placeholders} EXACTLY as they are...]

Translate the following texts:
1. Hello {name}
2. You have {count} items
3. Welcome back {user}
```

## Валидация после перевода

### Что проверяется

#### 1. Сохранность placeholders

```python
Original:   "Hello {name}"
Translated: "Привет {name}"     ✅ Valid
Translated: "Привет {имя}"      ❌ Invalid - placeholder translated
```

#### 2. Структура ICU syntax

```python
Original:   "{count, plural, one {# item} other {# items}}"
Translated: "{count, plural, one {# элемент} other {# элементов}}"  ✅ Valid
Translated: "{количество, множественное число...}"                   ❌ Invalid
```

#### 3. Пустые переводы

```python
Original:   "Hello"
Translated: ""          ❌ Invalid - empty translation
```

#### 4. Подозрительно длинные переводы

```python
Original:   "Hello"
Translated: "Очень длинный текст который в 5 раз длиннее..."  ⚠ Warning
```

### Validation результаты

#### ValidationResult

```python
@dataclass
class ValidationResult:
    is_valid: bool          # Общий статус
    errors: list[str]       # Критические ошибки
    warnings: list[str]     # Предупреждения
```

#### Примеры результатов

**Успешная валидация:**
```python
ValidationResult(
    is_valid=True,
    errors=[],
    warnings=[]
)
```

**Переведенный placeholder:**
```python
ValidationResult(
    is_valid=False,
    errors=["Extra/translated placeholders found: {имя}",
            "Missing placeholders in translation: {name}"],
    warnings=[]
)
```

**Потерянный ICU синтаксис:**
```python
ValidationResult(
    is_valid=False,
    errors=["ICU keywords lost: plural"],
    warnings=["ICU syntax appears to be completely translated/broken"]
)
```

## Использование в коде

### Валидация одного перевода

```python
from translate_intl.utils.validators import validate_translation

original = "Hello {name}"
translated = "Привет {name}"

result = validate_translation(original, translated)

if result.is_valid:
    print("✅ Translation valid")
else:
    print("❌ Validation failed:")
    for error in result.errors:
        print(f"  - {error}")
```

### Извлечение placeholders

```python
from translate_intl.utils.validators import extract_placeholders

text = "Hello {name}, you have {count} items"
placeholders = extract_placeholders(text)
# Returns: {"name", "count"}
```

### Проверка ICU keywords

```python
from translate_intl.utils.validators import extract_icu_keywords

text = "{count, plural, one {# item} other {# items}}"
keywords = extract_icu_keywords(text)
# Returns: {"plural"}
```

## Поведение при ошибках

### В процессе перевода

При обнаружении ошибки валидации:

1. **Warnings** - Логируются, перевод сохраняется
2. **Errors** - Логируются, **перевод пропускается**, оригинал не изменяется

### Пример вывода

```
⚠ Validation failed for 'greeting':
  Original:   Hello {name}
  Translated: Привет {имя}
  Errors:
    - Extra/translated placeholders found: {имя}
    - Missing placeholders in translation: {name}
  Skipping invalid translation for 'greeting'
```

### Статистика

После завершения перевода:

```
✓ Language ru: 25/28 keys translated in 5.2s (4.8 keys/sec)
  - 3 keys skipped due to validation errors
```

## Тестирование валидации

### Запуск тестов

```bash
# Тест валидаторов
python test_validation.py
```

### Проверка существующих переводов

```bash
# Анализ качества в test_messages
python test_validation.py

# Вывод:
=== Testing Actual Translations from test_messages ===

❌ Key: greeting
   Original:   Hello {name}
   Translated: Здравствуйте, {имя}
   Errors:     Extra/translated placeholders found: {имя}

❌ Key: items
   Original:   {count, plural, one {# item} other {# items}}
   Translated: {количество, множественное число...}
   Errors:     ICU keywords lost: plural
```

## Режимы валидации

### Strict mode (строгий)

Предупреждения рассматриваются как ошибки:

```python
result = validate_translation(original, translated, strict=True)
# warnings становятся errors
```

### Relaxed mode (мягкий)

Только критические ошибки блокируют перевод:

```python
result = validate_translation(original, translated, strict=False)
# warnings логируются, но перевод сохраняется
```

По умолчанию используется **relaxed mode**.

## Примеры валидации

### ✅ Корректные переводы

```python
# Простой placeholder
Original:   "Hello {name}"
Translated: "Привет {name}"
Result:     ✅ Valid

# ICU plural
Original:   "{count, plural, one {# item} other {# items}}"
Translated: "{count, plural, one {# элемент} other {# элементов}}"
Result:     ✅ Valid

# Без placeholders
Original:   "Sign In"
Translated: "Войти"
Result:     ✅ Valid
```

### ❌ Некорректные переводы

```python
# Переведенный placeholder
Original:   "Hello {name}"
Translated: "Привет {имя}"
Result:     ❌ Invalid
Errors:     Missing placeholders: {name}, Extra: {имя}

# Потерян ICU синтаксис
Original:   "{count, plural, one {# item} other {# items}}"
Translated: "{количество, множественное число, одно {# элемент}}"
Result:     ❌ Invalid
Errors:     ICU keywords lost: plural

# Пустой перевод
Original:   "Hello"
Translated: ""
Result:     ❌ Invalid
Errors:     Translation is empty
```

## Ограничения

### Что валидация НЕ проверяет

1. **Качество перевода** - только техническая корректность
2. **Грамматика** - не проверяется правильность языка
3. **Контекст** - "Email" может быть переведен по-разному
4. **Стиль** - формальность, тон не анализируются

### Для этого требуется

- Ручная проверка носителем языка
- Контекстные подсказки в исходном тексте
- Специализированные инструменты для проверки качества

## Рекомендации

### 1. Проверяйте результаты

После автоматического перевода всегда проверяйте:

```bash
# Проверить валидацию
python test_validation.py

# Просмотреть логи перевода
docker compose logs cli
```

### 2. Исправляйте ошибки вручную

Если валидация отклонила перевод:

```json
// ru.json - исправить вручную
{
  "greeting": "Привет, {name}"  // Вместо {имя}
}
```

### 3. Используйте контекстные подсказки

```json
// en.json
{
  "email_field": "Email",           // Поле формы
  "email_message": "Email sent",    // Сообщение о действии
  "email_address": "Email address"  // Полный адрес
}
```

### 4. Добавляйте комментарии

```json
// en.json
{
  // Form labels - keep concise
  "login": "Sign In",
  "password": "Password",

  // ICU messages - preserve {placeholders}
  "greeting": "Hello {name}",
  "items_count": "{count, plural, one {# item} other {# items}}"
}
```

## Troubleshooting

### Слишком много ошибок валидации

**Проблема:** Модель игнорирует инструкции

**Решение:**
1. Уменьшить batch_size (меньше контекста для модели)
2. Перевести проблемные строки по отдельности
3. Исправить вручную после перевода

### Ложные срабатывания

**Проблема:** Валидация отклоняет корректные переводы

**Решение:**
1. Проверить логику в `validators.py`
2. Отключить strict mode
3. Добавить исключения для конкретных случаев

### Пропущенные ошибки

**Проблема:** Валидация не ловит некорректный перевод

**Решение:**
1. Добавить новые проверки в `validate_translation()`
2. Улучшить регулярные выражения
3. Добавить тесты для edge cases

## API Reference

### Functions

```python
def extract_placeholders(text: str) -> set[str]:
    """Extract {placeholder} names from text."""

def extract_icu_keywords(text: str) -> set[str]:
    """Extract ICU keywords (plural, select, etc.)."""

def validate_placeholders(original: str, translated: str) -> ValidationResult:
    """Validate placeholder preservation."""

def validate_translation(
    original: str,
    translated: str,
    strict: bool = True
) -> ValidationResult:
    """Comprehensive translation validation."""

def format_validation_error(
    key: str,
    original: str,
    translated: str,
    result: ValidationResult
) -> str:
    """Format validation error for display."""
```

### Classes

```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]

    @property
    def has_errors(self) -> bool: ...

    @property
    def has_warnings(self) -> bool: ...
```

## См. также

- [test_validation.py](../test_validation.py) - Тесты валидации
- [validators.py](../src/translate_intl/utils/validators.py) - Исходный код
- [TRANSLATION_QUALITY_REVIEW.md](../test_messages/TRANSLATION_QUALITY_REVIEW.md) - Анализ качества
