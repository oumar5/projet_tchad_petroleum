import 'package:dio/dio.dart';

import '../../../core/api_client.dart';
import '../../../core/offline/offline_cache.dart';

class ProductionRepository {
  ProductionRepository(this._client);
  final ApiClient _client;

  Future<CachedResult<List<Map<String, dynamic>>>> dailyCached({
    String? from,
    String? to,
    String? block,
    int page = 1,
    int pageSize = 100,
  }) {
    final qp = {
      'page': '$page',
      'page_size': '$pageSize',
      'from': ?from,
      'to': ?to,
      'block': ?block,
    };
    return OfflineCache.instance.cached<List<Map<String, dynamic>>>(
      key: 'prod:daily',
      fetch: () async {
        final r = await _client.dio
            .get('/v1/production/daily', queryParameters: qp);
        return List<Map<String, dynamic>>.from(
          (r.data['items'] as List)
              .map((e) => Map<String, dynamic>.from(e as Map)),
        );
      },
      decode: (raw) => List<Map<String, dynamic>>.from(
        (raw as List).map((e) => Map<String, dynamic>.from(e as Map)),
      ),
      encode: (items) => items,
    );
  }

  Future<String> create({
    required String date,
    required String blockCode,
    required int wellsTotal,
    required int wellsActive,
    required double oilBbl,
    required double waterBbl,
    required double watercutPct,
  }) async {
    final r = await _client.dio.post('/v1/production/daily', data: {
      'date': date,
      'block_code': blockCode,
      'wells_total': wellsTotal,
      'wells_active': wellsActive,
      'oil_bbl': oilBbl,
      'water_bbl': waterBbl,
      'watercut_pct': watercutPct,
    });
    return r.data['id'] as String;
  }

  Future<List<int>> exportCsv({String? from, String? to}) async {
    final r = await _client.dio.get<List<int>>(
      '/v1/production/export',
      queryParameters: {'format': 'csv', 'from': ?from, 'to': ?to},
      options: Options(responseType: ResponseType.bytes),
    );
    return r.data ?? const <int>[];
  }
}
