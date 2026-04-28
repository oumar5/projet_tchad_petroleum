import '../../../core/api_client.dart';
import '../../../core/offline/offline_cache.dart';

List<Map<String, dynamic>> _decodeList(Object raw) =>
    List<Map<String, dynamic>>.from(
      (raw as List).map((e) => Map<String, dynamic>.from(e as Map)),
    );

class MaintenanceRepository {
  MaintenanceRepository(this._client);
  final ApiClient _client;

  Future<CachedResult<List<Map<String, dynamic>>>> failuresCached({
    String? block,
  }) {
    final key = block == null ? 'maint:failures:_all' : 'maint:failures:$block';
    return OfflineCache.instance.cached<List<Map<String, dynamic>>>(
      key: key,
      fetch: () async {
        final r = await _client.dio.get(
          '/v1/maintenance/failures',
          queryParameters: {'block': ?block},
        );
        return _decodeList(r.data as Object);
      },
      decode: _decodeList,
      encode: (items) => items,
    );
  }

  Future<CachedResult<List<Map<String, dynamic>>>> interventionsCached() {
    return OfflineCache.instance.cached<List<Map<String, dynamic>>>(
      key: 'maint:interventions',
      fetch: () async {
        final r = await _client.dio.get('/v1/maintenance/interventions');
        return _decodeList(r.data as Object);
      },
      decode: _decodeList,
      encode: (items) => items,
    );
  }

  Future<void> reportFailure({
    required String date,
    required String block,
    required String type,
    required String severity,
    String? description,
  }) async {
    await _client.dio.post('/v1/maintenance/failures', data: {
      'notification_date': date,
      'block': block,
      'failure_type': type,
      'severity': severity,
      'description': ?description,
    });
  }

  Future<Map<String, dynamic>> predictRisk({
    required String block,
    int horizonDays = 7,
  }) async {
    final r = await _client.dio.post(
      '/v1/ml/predict/maintenance',
      data: {'block': block, 'horizon_days': horizonDays},
    );
    return Map<String, dynamic>.from(r.data as Map);
  }
}
