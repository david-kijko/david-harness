# Rust Code Style Guide

## Formatting

- Use `rustfmt` for automatic formatting
- Run `cargo fmt` before committing
- Maximum line length: 100 characters

## Naming Conventions

```rust
// Modules: snake_case
mod my_module;

// Types: PascalCase
struct MyStruct;
enum MyEnum;
trait MyTrait;

// Functions and methods: snake_case
fn my_function() {}

// Constants: SCREAMING_SNAKE_CASE
const MAX_SIZE: usize = 100;

// Variables: snake_case
let my_variable = 42;

// Lifetimes: short lowercase, typically 'a, 'b
fn example<'a>(x: &'a str) -> &'a str { x }
```

## Error Handling

```rust
// Prefer Result over panic! for recoverable errors
fn parse_config(path: &str) -> Result<Config, ConfigError> {
    // ...
}

// Use ? operator for error propagation
fn load_data() -> Result<Data, Error> {
    let config = parse_config("config.toml")?;
    let data = fetch_data(&config)?;
    Ok(data)
}

// Custom error types with thiserror
#[derive(Debug, thiserror::Error)]
enum AppError {
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Parse error: {0}")]
    Parse(String),
}
```

## Documentation

```rust
/// Brief description of the function.
///
/// More detailed explanation if needed.
///
/// # Arguments
///
/// * `param` - Description of the parameter
///
/// # Returns
///
/// Description of return value
///
/// # Examples
///
/// ```
/// let result = my_function(42);
/// assert_eq!(result, 84);
/// ```
///
/// # Errors
///
/// Returns `Error` if something goes wrong
pub fn my_function(param: i32) -> Result<i32, Error> {
    Ok(param * 2)
}
```

## Clippy

- Run `cargo clippy` and address all warnings
- Use `#[allow(clippy::...)]` sparingly with justification

## Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_basic_functionality() {
        let result = my_function(21);
        assert_eq!(result.unwrap(), 42);
    }

    #[test]
    fn test_error_case() {
        let result = my_function(-1);
        assert!(result.is_err());
    }
}
```

## Dependencies

- Prefer standard library when possible
- Audit dependencies with `cargo audit`
- Pin major versions in `Cargo.toml`

## Performance

- Avoid unnecessary allocations
- Use iterators over manual loops
- Profile before optimizing
