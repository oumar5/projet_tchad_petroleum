import '../../../core/api_client.dart';
import '../../../core/offline/offline_cache.dart';

class DashboardRepository {
  DashboardRepository(this._client);
  final ApiClient _client;

  Future<CachedResult<Map<String, dynamic>>> kpisCached({
    String period = '30d',
  }) {
    return OfflineCache.instance.cached<Map<String, dynamic>>(
      key: 'kpis:$period',
      fetch: () async {
        final r = await _client.dio.get(
          '/v1/production/kpis',
          queryParameters: {'period': period},
        );
        return Map<String, dynamic>.from(r.data as Map);
      },
      decode: (raw) => Map<String, dynamic>.from(raw as Map),
      encode: (m) => m,
    );
  }
}
