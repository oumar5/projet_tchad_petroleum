import '../../../core/api_client.dart';
import '../../../core/offline/offline_cache.dart';

List<Map<String, dynamic>> _decodeList(Object raw) =>
    List<Map<String, dynamic>>.from(
      (raw as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );

class ModelsRepository {
  ModelsRepository(this._client);
  final ApiClient _client;

  Future<CachedResult<List<Map<String, dynamic>>>> listCached({
    String? type,
    bool? active,
  }) {
    final key = 'ml:models:${type ?? "_all"}:${active ?? "_all"}';
    return OfflineCache.instance.cached<List<Map<String, dynamic>>>(
      key: key,
      fetch: () async {
        final r = await _client.dio.get(
          '/v1/ml/models',
          queryParameters: {'type': ?type, 'active': ?active},
        );
        return _decodeList(r.data as Object);
      },
      decode: _decodeList,
      encode: (items) => items,
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
