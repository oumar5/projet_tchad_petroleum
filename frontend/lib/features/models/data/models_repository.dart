import '../../../core/api_client.dart';

class ModelsRepository {
  ModelsRepository(this._client);
  final ApiClient _client;

  Future<List<Map<String, dynamic>>> list({
    String? type,
    bool? active,
  }) async {
    final r = await _client.dio.get(
      '/v1/ml/models',
      queryParameters: {'type': ?type, 'active': ?active},
    );
    return List<Map<String, dynamic>>.from(
      (r.data as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );
  }

  Future<void> activate(String modelId) async {
    await _client.dio.patch('/v1/ml/models/$modelId/activate');
  }

  Future<String> startTraining({
    required String modelType,
    String algorithm = 'gradient_boosting',
    Map<String, dynamic>? params,
  }) async {
    final r = await _client.dio.post('/v1/ml/train', data: {
      'model_type': modelType,
      'algorithm': algorithm,
      'params': params ?? {},
    });
    return (r.data['job_id'] ?? r.data['id']).toString();
  }

  Future<Map<String, dynamic>> getJob(String jobId) async {
    final r = await _client.dio.get('/v1/ml/jobs/$jobId');
    return Map<String, dynamic>.from(r.data as Map);
  }
}
