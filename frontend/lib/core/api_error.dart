import 'package:dio/dio.dart';

/// Convertit n'importe quelle exception en message lisible — jamais de JSON brut.
String prettyError(Object err) {
  if (err is DioException) {
    final code = err.response?.statusCode;
    final data = err.response?.data;
    String? detail;
    if (data is Map && data['detail'] is String) {
      detail = data['detail'] as String;
    } else if (data is String && data.isNotEmpty && !data.startsWith('{')) {
      detail = data;
    }
    if (code == null) {
      if (err.type == DioExceptionType.connectionTimeout ||
          err.type == DioExceptionType.receiveTimeout ||
          err.type == DioExceptionType.sendTimeout) {
        return 'Délai dépassé. Vérifie ta connexion réseau.';
      }
      if (err.type == DioExceptionType.connectionError) {
        return 'Serveur injoignable. Vérifie ta connexion.';
      }
      return 'Erreur réseau.';
    }
    switch (code) {
      case 400:
        return detail ?? 'Requête invalide.';
      case 401:
        return 'Session expirée. Reconnecte-toi.';
      case 403:
        return 'Accès refusé.';
      case 404:
        return detail ?? 'Ressource introuvable.';
      case 409:
        return detail ?? 'Conflit avec une donnée existante.';
      case 422:
        return detail ?? 'Données invalides.';
      case 429:
        return 'Trop de requêtes. Réessaie plus tard.';
      case 500:
      case 502:
      case 503:
        return 'Service indisponible. Réessaie dans un instant.';
    }
    return detail ?? 'Erreur HTTP $code.';
  }
  return 'Une erreur est survenue.';
}
