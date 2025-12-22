# TDD Refactor Phase Command

Improve code quality while maintaining test coverage (Refactor phase of TDD cycle).

## Command
`/tdd:refactor`

## Description
Implements the Refactor phase of TDD by improving code quality, design, and maintainability while ensuring all tests continue to pass.

## Core Principle
**"Improve code quality without changing behavior"**

## Process
1. Ensure all tests are passing
2. Identify refactoring opportunities
3. Apply refactoring techniques
4. Run tests continuously to ensure no regressions
5. Verify improved code quality metrics

## Refactoring Techniques
- Extract methods/functions
- Rename variables and methods for clarity
- Remove code duplication
- Improve code organization
- Optimize performance (when safe)
- Enhance readability and maintainability

## Safety Rules
- All existing tests must continue to pass
- No changes to external behavior
- Refactor in small, incremental steps
- Run tests after each change

## Quality Improvements
- Better code organization
- Reduced complexity
- Improved readability
- Enhanced maintainability
- Better performance (when applicable)

## Integration
- Updates Taskmaster tasks with code quality metrics
- Tracks refactoring improvements
- Maintains traceability to specifications

## Completion Criteria
- All tests passing
- Code quality metrics improved
- No behavioral changes
- Improved maintainability