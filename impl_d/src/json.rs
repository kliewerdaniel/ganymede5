// Minimal JSON reader/writer.
//
// Rationale: impl_d has zero external crates so that the engine is auditable
// against the two spec documents alone. Nothing here knows anything about
// defeat semantics; it is a pure syntax layer.

#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    Null,
    Bool(bool),
    Num(f64),
    Str(String),
    Arr(Vec<Value>),
    Obj(Vec<(String, Value)>),
}

impl Value {
    pub fn get(&self, key: &str) -> Option<&Value> {
        match self {
            Value::Obj(m) => m.iter().find(|(k, _)| k == key).map(|(_, v)| v),
            _ => None,
        }
    }
    pub fn as_f64(&self) -> Option<f64> {
        match self {
            Value::Num(n) => Some(*n),
            _ => None,
        }
    }
    pub fn as_str(&self) -> Option<&str> {
        match self {
            Value::Str(s) => Some(s.as_str()),
            _ => None,
        }
    }
    pub fn as_bool(&self) -> Option<bool> {
        match self {
            Value::Bool(b) => Some(*b),
            _ => None,
        }
    }
    pub fn as_arr(&self) -> Option<&Vec<Value>> {
        match self {
            Value::Arr(a) => Some(a),
            _ => None,
        }
    }
    pub fn as_strs(&self) -> Vec<String> {
        match self {
            Value::Arr(a) => a
                .iter()
                .filter_map(|v| v.as_str().map(|s| s.to_string()))
                .collect(),
            _ => Vec::new(),
        }
    }

    /// Present-and-non-null numeric field. `null` and missing are both "absent"
    /// (SEMANTICS.md 4.6: absence has no implied value, in particular not -inf).
    pub fn opt_f64(&self, key: &str) -> Option<f64> {
        self.get(key).and_then(|v| v.as_f64())
    }
    pub fn opt_str(&self, key: &str) -> Option<String> {
        self.get(key).and_then(|v| v.as_str()).map(|s| s.to_string())
    }
    /// Boolean field. `None` when the field is missing or null, so callers must
    /// decide absence behaviour explicitly rather than inheriting a default.
    pub fn opt_bool(&self, key: &str) -> Option<bool> {
        self.get(key).and_then(|v| v.as_bool())
    }
}

pub fn parse(src: &str) -> Result<Value, String> {
    let b: Vec<char> = src.chars().collect();
    let mut p = Parser { b, i: 0 };
    p.ws();
    let v = p.value()?;
    p.ws();
    if p.i != p.b.len() {
        return Err(format!("trailing input at char {}", p.i));
    }
    Ok(v)
}

struct Parser {
    b: Vec<char>,
    i: usize,
}

impl Parser {
    fn peek(&self) -> Option<char> {
        self.b.get(self.i).copied()
    }
    fn ws(&mut self) {
        while matches!(self.peek(), Some(' ') | Some('\t') | Some('\n') | Some('\r')) {
            self.i += 1;
        }
    }
    fn lit(&mut self, s: &str) -> bool {
        let chars: Vec<char> = s.chars().collect();
        if self.b.len() >= self.i + chars.len() && self.b[self.i..self.i + chars.len()] == chars[..] {
            self.i += chars.len();
            true
        } else {
            false
        }
    }
    fn value(&mut self) -> Result<Value, String> {
        self.ws();
        match self.peek() {
            Some('{') => self.object(),
            Some('[') => self.array(),
            Some('"') => Ok(Value::Str(self.string()?)),
            Some('t') if self.lit("true") => Ok(Value::Bool(true)),
            Some('f') if self.lit("false") => Ok(Value::Bool(false)),
            Some('n') if self.lit("null") => Ok(Value::Null),
            Some(c) if c == '-' || c.is_ascii_digit() => self.number(),
            other => Err(format!("unexpected {:?} at {}", other, self.i)),
        }
    }
    fn object(&mut self) -> Result<Value, String> {
        self.i += 1; // {
        let mut out = Vec::new();
        self.ws();
        if self.peek() == Some('}') {
            self.i += 1;
            return Ok(Value::Obj(out));
        }
        loop {
            self.ws();
            let k = self.string()?;
            self.ws();
            if self.peek() != Some(':') {
                return Err(format!("expected ':' at {}", self.i));
            }
            self.i += 1;
            let v = self.value()?;
            out.push((k, v));
            self.ws();
            match self.peek() {
                Some(',') => {
                    self.i += 1;
                }
                Some('}') => {
                    self.i += 1;
                    return Ok(Value::Obj(out));
                }
                other => return Err(format!("expected ',' or '}}' got {:?} at {}", other, self.i)),
            }
        }
    }
    fn array(&mut self) -> Result<Value, String> {
        self.i += 1; // [
        let mut out = Vec::new();
        self.ws();
        if self.peek() == Some(']') {
            self.i += 1;
            return Ok(Value::Arr(out));
        }
        loop {
            let v = self.value()?;
            out.push(v);
            self.ws();
            match self.peek() {
                Some(',') => {
                    self.i += 1;
                }
                Some(']') => {
                    self.i += 1;
                    return Ok(Value::Arr(out));
                }
                other => return Err(format!("expected ',' or ']' got {:?} at {}", other, self.i)),
            }
        }
    }
    fn string(&mut self) -> Result<String, String> {
        if self.peek() != Some('"') {
            return Err(format!("expected string at {}", self.i));
        }
        self.i += 1;
        let mut s = String::new();
        loop {
            let c = self.peek().ok_or("unterminated string")?;
            self.i += 1;
            match c {
                '"' => return Ok(s),
                '\\' => {
                    let e = self.peek().ok_or("unterminated escape")?;
                    self.i += 1;
                    match e {
                        '"' => s.push('"'),
                        '\\' => s.push('\\'),
                        '/' => s.push('/'),
                        'b' => s.push('\u{8}'),
                        'f' => s.push('\u{c}'),
                        'n' => s.push('\n'),
                        'r' => s.push('\r'),
                        't' => s.push('\t'),
                        'u' => {
                            let hex: String = self.b[self.i..self.i + 4].iter().collect();
                            self.i += 4;
                            let n = u32::from_str_radix(&hex, 16).map_err(|e| e.to_string())?;
                            s.push(char::from_u32(n).unwrap_or('\u{fffd}'));
                        }
                        other => return Err(format!("bad escape \\{}", other)),
                    }
                }
                other => s.push(other),
            }
        }
    }
    fn number(&mut self) -> Result<Value, String> {
        let start = self.i;
        if self.peek() == Some('-') {
            self.i += 1;
        }
        while matches!(self.peek(), Some(c) if c.is_ascii_digit()) {
            self.i += 1;
        }
        if self.peek() == Some('.') {
            self.i += 1;
            while matches!(self.peek(), Some(c) if c.is_ascii_digit()) {
                self.i += 1;
            }
        }
        if matches!(self.peek(), Some('e') | Some('E')) {
            self.i += 1;
            if matches!(self.peek(), Some('+') | Some('-')) {
                self.i += 1;
            }
            while matches!(self.peek(), Some(c) if c.is_ascii_digit()) {
                self.i += 1;
            }
        }
        let s: String = self.b[start..self.i].iter().collect();
        s.parse::<f64>().map(Value::Num).map_err(|e| e.to_string())
    }
}

// ---- writing -------------------------------------------------------------

pub fn esc(s: &str) -> String {
    let mut o = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => o.push_str("\\\""),
            '\\' => o.push_str("\\\\"),
            '\n' => o.push_str("\\n"),
            '\r' => o.push_str("\\r"),
            '\t' => o.push_str("\\t"),
            c if (c as u32) < 0x20 => o.push_str(&format!("\\u{:04x}", c as u32)),
            c => o.push(c),
        }
    }
    o.push('"');
    o
}

pub fn num(n: f64) -> String {
    if n.fract() == 0.0 && n.abs() < 1e15 {
        format!("{}", n as i64)
    } else {
        format!("{}", n)
    }
}
