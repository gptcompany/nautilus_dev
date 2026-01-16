// Commitlint configuration for conventional commits
// https://www.conventionalcommits.org/
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Enforce specific commit types
    'type-enum': [2, 'always', [
      'feat',     // New feature
      'fix',      // Bug fix
      'docs',     // Documentation only
      'style',    // Code style (formatting, semicolons, etc.)
      'refactor', // Code refactoring (no feature/fix)
      'perf',     // Performance improvement
      'test',     // Adding/updating tests
      'chore',    // Build process, dependencies
      'ci',       // CI/CD changes
      'revert',   // Reverting previous commit
      'build',    // Build system changes
    ]],
    // Scope is optional but recommended
    'scope-case': [2, 'always', 'kebab-case'],
    // Subject requirements
    'subject-case': [2, 'never', ['sentence-case', 'start-case', 'pascal-case', 'upper-case']],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    // Body and footer
    'body-leading-blank': [2, 'always'],
    'footer-leading-blank': [2, 'always'],
  },
};
