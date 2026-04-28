import '../../../core/api_client.dart';

class WaterRepository {
  WaterRepository(this._client);
  final ApiClient _client;

  Future<Map<String, dynamic>> recommend({
    required String block,
    double? targetOilBbl,
  }) async {
    final r = await _client.dio.post('/v1/ml/predict/water', data: {
      'block': block,
      'target_oil_bbl': ?targetOilBbl,
    });
    return Map<String, dynamic>.from(r.data as Map);
  }
}
