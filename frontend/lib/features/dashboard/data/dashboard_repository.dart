import '../../../core/api_client.dart';
import '../../../core/offline/offline_cache.dart';

class DashboardRepository {
  DashboardRepository(this._client);
  final ApiClient _client;

  Future<Map<String, dynamic>> kpis({String period = '30d'}) async {
    try {
      final r = await _client.dio.get(
        '/v1/production/kpis',
        queryParameters: {'period': period},
      );
      final data = Map<String, dynamic>.from(r.data as Map);
      await OfflineCache.instance.putJson('kpis:$period', data);
      return data;
    } catch (_) {
      final cached = OfflineCache.instance.readJson('kpis:$period');
      if (cached != null) return Map<String, dynamic>.from(cached.data as Map);
      rethrow;
    }
  }
}
