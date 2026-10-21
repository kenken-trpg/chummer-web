- **A formula in uploaded custom data can no longer write warnings to the
  server log.** A string literal with an invalid escape made the parser print
  a `SyntaxWarning`; the expression was refused, but the warning reached
  stderr. The evaluator also refuses an operator it has no rule for instead of
  computing it as `%` (`2**3` came out as 2), although no caller allowed one.
