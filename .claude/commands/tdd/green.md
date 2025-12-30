# TDD Green Phase Command

Implement minimal solution to make tests pass (Green phase of TDD cycle).

## Command
`/tdd:green`

## Description
Implements the Green phase of TDD by writing the minimal code necessary to make failing tests pass.

## Core Principle
**"Write only enough code to make the failing tests pass"**

## Process
1. Run failing tests to confirm current state
2. Implement minimal solution
3. Run tests to verify they pass
4. Avoid over-engineering or premature optimization
5. Ensure no existing tests are broken

## Implementation Guidelines
- Focus on making tests pass, not on perfect design
- Avoid adding functionality not covered by tests
- Keep solutions simple and straightforward
- Don't optimize prematurely

## Quality Checks
- All targeted tests now pass
- No regression in existing tests
- Code is functional but not necessarily optimal
- Solution addresses test requirements exactly

## Integration
- Updates CCMP issue with implementation progress
- Tracks test pass/fail metrics
- Links implementation to specifications

## Next Step
After Green phase completion, use `/tdd:refactor` to improve code quality.