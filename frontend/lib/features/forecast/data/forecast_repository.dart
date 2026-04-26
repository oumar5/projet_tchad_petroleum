import '../../../core/api_client.dart';

class ForecastRepository {
  ForecastRepository(this._client);
  final ApiClient _client;

  Future<Map<String, dynamic>> predictForecast({
    String target = 'oil_bbl',
    int horizonDays = 30,
    String algorithm = 'xgboost',
  }) async {
    final r = await _client.dio.post('/v1/ml/predict/forecast', data: {
      'target': target,
      'horizon_days': horizonDays,
      'algorithm': algorithm,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }
}
