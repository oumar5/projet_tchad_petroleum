import 'package:dio/dio.dart';

import '../../../core/api_client.dart';
import '../../../core/offline/offline_cache.dart';

class ProductionRepository {
  ProductionRepository(this._client);
  final ApiClient _client;

  Future<List<Map<String, dynamic>>> daily({
    String? from,
    String? to,
    String? block,
    int page = 1,
    int pageSize = 100,
  }) async {
    final qp = {
      'page': '$page',
      'page_size': '$pageSize',
      'from': ?from,
      'to': ?to,
      'block': ?block,
    };
    try {
      final r = await _client.dio
          .get('/v1/production/daily', queryParameters: qp);
      final items = List<Map<String, dynamic>>.from(
        (r.data['items'] as List).map((e) => Map<String, dynamic>.from(e as Map)),
      );
      await OfflineCache.instance.putJson('prod:daily', items);
      return items;
    } catch (_) {
      final cached = OfflineCache.instance.readJson('prod:daily');
      if (cached != null) {
        return List<Map<String, dynamic>>.from(
          (cached.data as List).map((e) => Map<String, dynamic>.from(e as Map)),
        );
      }
      rethrow;
    }
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
