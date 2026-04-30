/// Application config (compile-time API base URL).
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://api-smartbarrel.oumarbenlol.com',
  );
}
