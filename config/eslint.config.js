module.exports = [
  {
    files: ["**/*.js"],
    languageOptions: {
      ecmaVersion: 2019,
      sourceType: "script",
      globals: {
        console: "readonly",
        document: "readonly",
        window: "readonly",
        fetch: "readonly",
        setTimeout: "readonly",
        FormData: "readonly",
        makeTabsWork: "readonly",
        saveData: "readonly",
        buttonPress: "readonly",
        updateProgress: "readonly",
        FileReader: "readonly",
        URLSearchParams: "readonly",
        alert: "readonly"
      }
    },
    rules: {
      "no-unused-vars": ["error", { "varsIgnorePattern": "^(saveData|buttonPress|updateProgress|makeTabsWork)$" }],
      "no-undef": "error",
      "semi": ["error", "always"],
      "quotes": ["error", "single"],
      "indent": ["error", 4],
      "no-const-assign": "error",
      "prefer-const": "warn"
    }
  }
];
